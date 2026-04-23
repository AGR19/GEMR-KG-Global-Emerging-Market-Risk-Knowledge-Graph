import re
import sys
import os
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

_GRAPHDB_URL = os.getenv("GRAPHDB_URL", "http://localhost:7200")
_GRAPHDB_REPO = os.getenv("GRAPHDB_REPO", "GEMR")
_SPARQL_ENDPOINT = f"{_GRAPHDB_URL}/repositories/{_GRAPHDB_REPO}"

__all__ = [
    "execute_sparql", "is_syntactically_valid", "count_hallucinations",
    "get_result_count", "compare_results",
]


def execute_sparql(sparql: str) -> dict:
    """Execute a SPARQL query against GraphDB.

    Retries once on 503/502 (transient backpressure) with a short backoff,
    which absorbs the GraphDB slowness we saw during parallel sweeps.
    """
    import time as _time
    last_err: str | None = None
    last_status = 0
    for attempt in range(2):
        try:
            response = requests.get(
                _SPARQL_ENDPOINT,
                params={"query": sparql},
                headers={"Accept": "application/sparql-results+json"},
                timeout=60,
            )
            if response.ok:
                return {"success": True, "data": response.json(), "error": None, "status_code": response.status_code}
            last_status = response.status_code
            last_err = f"HTTP {response.status_code}: {response.text[:500]}"
            if response.status_code in (502, 503) and attempt == 0:
                _time.sleep(3)
                continue
            return {"success": False, "data": None, "error": last_err, "status_code": last_status}
        except requests.exceptions.ConnectionError:
            return {"success": False, "data": None, "error": "Cannot connect to GraphDB", "status_code": 0}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e), "status_code": 0}
    return {"success": False, "data": None, "error": last_err or "unknown", "status_code": last_status}

_SPARQL_START = re.compile(
    r"^\s*(PREFIX|SELECT|ASK|CONSTRUCT|DESCRIBE)\b",
    re.IGNORECASE | re.MULTILINE,
)

# Known-safe namespaces — anything else in angle-bracket IRI form is suspect
_SAFE_IRI_PATTERN = re.compile(
    r"<(https://gemr-kg\.org/ontology#|http://www\.w3\.org/|http://purl\.org/)[^>]*>"
)
_ANY_IRI_PATTERN = re.compile(r"<[^>]+>")

# SPARQL built-in keywords that appear as "word:" patterns — not prefixes
_SPARQL_BUILTINS = {
    "FILTER", "BIND", "OPTIONAL", "UNION", "VALUES", "SELECT", "WHERE",
    "FROM", "LIMIT", "OFFSET", "ORDER", "BY", "GROUP", "HAVING", "ASC",
    "DESC", "DISTINCT", "REDUCED", "AS", "STR", "LANG", "DATATYPE", "IRI",
    "URI", "BNODE", "COUNT", "SUM", "AVG", "MIN", "MAX", "SAMPLE", "CONCAT",
    "SUBSTR", "STRLEN", "UCASE", "LCASE", "STRSTARTS", "STRENDS", "CONTAINS",
    "ENCODE_FOR_URI", "YEAR", "MONTH", "DAY", "NOW", "RAND", "ABS", "CEIL",
    "FLOOR", "ROUND", "IF", "COALESCE", "NOT", "EXISTS", "MINUS", "SERVICE",
    "GRAPH", "PREFIX", "BASE", "CONSTRUCT", "DESCRIBE", "ASK", "REPLACE",
    "REGEX", "BOUND", "ISIRI", "ISURI", "ISBLANK", "ISLITERAL", "ISNUMERIC",
}

_KNOWN_PREFIXES = {"gemr", "xsd", "rdf", "rdfs", "owl"}


def is_syntactically_valid(sparql: str) -> bool:
    if not sparql or not sparql.strip():
        return False
    text = sparql.strip()
    if not _SPARQL_START.search(text):
        return False
    if "SELECT" in text.upper() and "WHERE" not in text.upper():
        return False
    if text.count("{") != text.count("}"):
        return False
    return True


def count_hallucinations(sparql: str) -> int:
    if not sparql:
        return 0

    count = 0

    # Count any angle-bracket IRIs that are NOT in known-safe namespaces
    for iri_match in _ANY_IRI_PATTERN.finditer(sparql):
        iri = iri_match.group(0)
        if not _SAFE_IRI_PATTERN.match(iri):
            count += 1

    # Count unknown prefixes (e.g. dbpedia:, schema:, ex:)
    for token in set(re.findall(r"(\w+):\w+", sparql)):
        if token.upper() not in _SPARQL_BUILTINS and token not in _KNOWN_PREFIXES:
            count += 1

    return count


def get_result_count(execution_result: dict) -> int:
    if not execution_result.get("success"):
        return 0
    data = execution_result.get("data") or {}
    return len(data.get("results", {}).get("bindings", []))


# ── Answer Accuracy Comparison ─────────────────────────────────────────────


def _normalize_value(val: str) -> str:
    """Normalize a SPARQL binding value for comparison.

    Strips namespace prefixes from IRIs, lowercases, and rounds floats
    to 2 decimal places so that minor numeric differences don't cause
    false negatives.
    """
    # Strip GEMR namespace from IRIs
    if "gemr-kg.org/ontology#" in val:
        val = val.split("#")[-1]

    # Try parsing as a number and rounding
    try:
        f = float(val)
        return str(round(f, 2))
    except (ValueError, TypeError):
        pass

    return val.strip().lower()


def _binding_to_tuple(binding: dict) -> tuple:
    """Convert a SPARQL result binding to a normalized, hashable tuple.

    Each binding is a dict like {"name": {"value": "Brazil", "type": "literal"}, ...}.
    We extract just the values, normalize them, and sort by variable name
    so column ordering doesn't matter.
    """
    return tuple(
        _normalize_value(v["value"])
        for k, v in sorted(binding.items())
    )


def compare_results(
    generated_data: dict | None,
    reference_data: dict | None,
) -> dict:
    """Compare generated query results against gold-standard reference results.

    Returns:
        {
            "answer_accurate": bool,    # True if generated matches reference
            "match_type": str,          # "exact", "partial", "empty", "wrong", "no_reference"
            "ref_row_count": int,
            "gen_row_count": int,
            "precision": float,         # fraction of generated rows that are correct
            "recall": float,            # fraction of reference rows that were found
        }
    """
    if reference_data is None:
        return {
            "answer_accurate": False,
            "match_type": "no_reference",
            "ref_row_count": 0,
            "gen_row_count": 0,
            "precision": 0.0,
            "recall": 0.0,
        }

    ref_bindings = reference_data.get("results", {}).get("bindings", [])

    if generated_data is None:
        return {
            "answer_accurate": False,
            "match_type": "empty",
            "ref_row_count": len(ref_bindings),
            "gen_row_count": 0,
            "precision": 0.0,
            "recall": 0.0,
        }

    gen_bindings = generated_data.get("results", {}).get("bindings", [])

    ref_count = len(ref_bindings)
    gen_count = len(gen_bindings)

    if gen_count == 0:
        return {
            "answer_accurate": False,
            "match_type": "empty",
            "ref_row_count": ref_count,
            "gen_row_count": 0,
            "precision": 0.0,
            "recall": 0.0,
        }

    # Normalize both result sets into sets of tuples for comparison.
    # Variables may differ (e.g. ?total vs ?totalRiskScore), so we compare
    # by value content, not variable names.
    ref_values = set()
    for b in ref_bindings:
        vals = tuple(sorted(_normalize_value(v["value"]) for v in b.values()))
        ref_values.add(vals)

    gen_values = set()
    for b in gen_bindings:
        vals = tuple(sorted(_normalize_value(v["value"]) for v in b.values()))
        gen_values.add(vals)

    # Column-set-robust matching, ONLY for small result sets (profile/
    # summary style queries where gen and ref may project slightly different
    # columns). For multi-row aggregates we rely on the stricter exact-tuple
    # comparison below, which prevents a gen that picks the wrong indicator
    # variant (e.g. GDP_CURR_USD vs GDP_CONST_2010_USD) from slipping through.
    if ref_count <= 3 and gen_count <= 3:
        def _row_vals(b: dict) -> set[str]:
            return {_normalize_value(v["value"]) for v in b.values()}

        gen_row_vals = [_row_vals(b) for b in gen_bindings]
        ref_row_vals = [_row_vals(b) for b in ref_bindings]

        def _rows_match(rv: set, gv: set) -> bool:
            if not rv or not gv:
                return False
            if rv.issubset(gv) or gv.issubset(rv):
                return True
            overlap = rv & gv
            smaller = min(len(rv), len(gv))
            return len(overlap) >= max(2, round(0.6 * smaller))

        matched_ref = sum(
            1 for rv in ref_row_vals
            if any(_rows_match(rv, gv) for gv in gen_row_vals)
        )
        if ref_count > 0 and matched_ref / ref_count >= 0.8:
            matched_gen = sum(
                1 for gv in gen_row_vals
                if any(_rows_match(rv, gv) for rv in ref_row_vals)
            )
            precision_subset = matched_gen / gen_count if gen_count else 0.0
            recall_subset = matched_ref / ref_count
            if precision_subset >= 0.5:
                return {
                    "answer_accurate": True,
                    "match_type": "exact" if recall_subset == 1.0 and precision_subset == 1.0 else "partial",
                    "ref_row_count": ref_count,
                    "gen_row_count": gen_count,
                    "precision": round(precision_subset, 4),
                    "recall": round(recall_subset, 4),
                }

    # Standard set comparison
    overlap = ref_values & gen_values
    precision = len(overlap) / len(gen_values) if gen_values else 0.0
    recall = len(overlap) / len(ref_values) if ref_values else 0.0

    if recall >= 0.8 and precision >= 0.5:
        match_type = "exact" if recall == 1.0 and precision == 1.0 else "partial"
        answer_accurate = recall >= 0.8
    else:
        match_type = "wrong"
        answer_accurate = False

    return {
        "answer_accurate": answer_accurate,
        "match_type": match_type,
        "ref_row_count": ref_count,
        "gen_row_count": gen_count,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
    }
