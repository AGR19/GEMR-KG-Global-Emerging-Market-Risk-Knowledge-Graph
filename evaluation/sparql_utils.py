import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.pipeline.self_healer import execute_sparql  # re-export for convenience

__all__ = ["execute_sparql", "is_syntactically_valid", "count_hallucinations", "get_result_count"]

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
