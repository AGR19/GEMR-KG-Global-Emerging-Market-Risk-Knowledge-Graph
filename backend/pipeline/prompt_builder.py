"""
Prompt Builder — Constructs ontology-constrained prompts for SPARQL generation.

Combines the GEMR-KG ontology schema, grounded IRIs from the retrieval step,
and the user's question into a structured prompt that constrains the LLM to
generate valid, schema-compliant SPARQL.

This is the paper's "Ontology-Constrained Prompting" step.
"""
from .schema_loader import GEMRSchema


def build_system_prompt(schema: GEMRSchema) -> str:
    """
    Build the static system prompt containing the full ontology schema.
    This is sent once and stays constant across queries.
    """
    # Build class hierarchy
    class_lines = []
    for cls in schema.classes:
        line = f"  - {cls.local_name}"
        if cls.label != cls.local_name:
            line += f' (label: "{cls.label}")'
        if cls.parent:
            line += f" → subClassOf {cls.parent}"
        class_lines.append(line)

    # Build property schema with domains and ranges
    prop_lines = []
    for prop in schema.properties:
        line = f"  - gemr:{prop.local_name}"
        if prop.label != prop.local_name:
            line += f' (label: "{prop.label}")'
        if prop.domain:
            line += f" | domain: {prop.domain}"
        if prop.range:
            line += f" | range: {prop.range}"
        line += f" [{prop.prop_type}]"
        prop_lines.append(line)

    # Country list
    countries_str = ", ".join(schema.countries)

    # Observation types (these are the RDF types used with `a gemr:XXX`)
    obs_types = ", ".join(f"gemr:{t}" for t in schema.observation_types[:40])

    return f"""You are a SPARQL query generator for the GEMR-KG (Global Emerging Markets Risk Knowledge Graph).
Your job is to translate natural language questions into valid, executable SPARQL queries.

═══════════════════════════════════════
ONTOLOGY SCHEMA
═══════════════════════════════════════

PREFIXES (always include these):
  PREFIX gemr: <https://gemr-kg.org/ontology#>
  PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
  PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

CLASSES:
{chr(10).join(class_lines)}

PROPERTIES:
{chr(10).join(prop_lines)}

COUNTRIES: {countries_str}
  Access via: ?country gemr:countryName "Brazil" .

YEARS: gemr:Year2002 to gemr:Year2023
  Access via: ?yearEntity gemr:yearValue ?year .
  NOTE: yearValue has TWO datatypes — xsd:gYear and xsd:integer.
  For arithmetic (year + 1, year - 1), ALWAYS use:
    BIND(xsd:integer(STR(?year)) AS ?yearInt)

OBSERVATION TYPES (use with `a gemr:XXX`):
  {obs_types}

═══════════════════════════════════════
CORE QUERY PATTERNS
═══════════════════════════════════════

1. BASIC OBSERVATION:
   ?obs a gemr:SomeObservationType ;
        gemr:hasCountry ?country ;
        gemr:hasIndicator gemr:SomeIndicator ;
        gemr:hasYear ?yearEntity ;
        gemr:observationValue ?value .

2. RISK SCORE:
   ?rs a gemr:RiskScore ;
       gemr:hasCountry ?country ;
       gemr:hasYear ?yearEntity ;
       gemr:totalRiskScore ?total .
   OPTIONAL {{ ?rs gemr:governanceScore ?gov }}
   OPTIONAL {{ ?rs gemr:economicHealthScore ?econ }}

3. YEAR-OVER-YEAR (temporal lag):
   ?yearEntity gemr:yearValue ?yLit .
   BIND(xsd:integer(STR(?yLit)) AS ?yearInt)
   BIND(?yearInt + 1 AS ?nextYearInt)
   ?nextYearEntity gemr:yearValue ?nextYLit .
   FILTER(xsd:integer(STR(?nextYLit)) = ?nextYearInt)

═══════════════════════════════════════
DIRECTIONALITY (common hallucination source)
═══════════════════════════════════════

The edges between Country ↔ RiskScore and Country ↔ Observation
go FROM the scored/observed entity TO the Country, not the other way.

  CORRECT:    ?rs   gemr:hasCountry ?country .
  CORRECT:    ?obs  gemr:hasCountry ?country .
  WRONG:      ?country gemr:hasRiskScore ?rs .   ← this property does NOT exist
  WRONG:      ?country gemr:hasObservation ?obs . ← this property does NOT exist

There is NO inverse property. To go "from country to its risk score",
bind the country first, then look up the RiskScore via hasCountry:

  ?country gemr:countryName "Poland" .
  ?rs a gemr:RiskScore ; gemr:hasCountry ?country ; gemr:totalRiskScore ?total .

═══════════════════════════════════════
FILTER / AGGREGATE GRAMMAR
═══════════════════════════════════════

FILTER expressions take BOOLEAN expressions only — NOT triple patterns
and NOT aggregate functions.

  WRONG:  FILTER (?s gemr:hasX ?o)              ← triple pattern in FILTER
  WRONG:  FILTER (?x = MAX(?x))                 ← aggregate in FILTER
  WRONG:  FILTER (?obs gemr:value = ?v)         ← mixing pattern + comparison

  CORRECT: use a triple pattern, then FILTER on a plain expression:
    ?s gemr:hasX ?o .
    FILTER (?o > 5)

For "max per group" use a subquery with GROUP BY + MAX, then join it back:

  SELECT ?country ?year ?rate WHERE {{
    {{ SELECT ?country (MAX(?r) AS ?maxR) WHERE {{
         ?o gemr:hasCountry ?c ; gemr:observationValue ?r .
         ?c gemr:countryName ?country .
       }} GROUP BY ?country }}
    ?o2 gemr:hasCountry ?c2 ; gemr:observationValue ?maxR ; gemr:hasYear ?ye .
    ?c2 gemr:countryName ?country .
    ?ye gemr:yearValue ?year .
    BIND(?maxR AS ?rate)
  }}

Every non-aggregated variable in an aggregate subquery MUST be in GROUP BY.

═══════════════════════════════════════
YEAR FILTERING (yearValue has MIXED datatypes)
═══════════════════════════════════════

Because yearValue is stored as both xsd:gYear AND xsd:integer, prefer
string-based comparisons which work for both:

  PREFERRED:  ?y gemr:yearValue ?yv .
              FILTER (STR(?yv) = "2020")

  RANGE:      FILTER (xsd:integer(STR(?yv)) >= 2010 &&
                      xsd:integer(STR(?yv)) <= 2020)

  AVOID:      FILTER (?yv = "2020"^^xsd:gYear)   ← misses integer half
  AVOID:      FILTER (?yv IN ("2015", "2020"))   ← plain string misses both

═══════════════════════════════════════
STRICT RULES
═══════════════════════════════════════

1. Output ONLY a valid SPARQL query — no explanation, no markdown, no code fences.
2. Use ONLY the IRIs and properties listed above or provided in the grounded IRIs.
3. Do NOT invent or hallucinate IRIs that are not in the schema.
   In particular: gemr:hasRiskScore and gemr:hasObservation do NOT exist.
4. LIMIT guidance:
     - Single-value / superlative queries: LIMIT 1 or LIMIT 10
     - Multi-year time-series for ONE country: no LIMIT, or LIMIT 100
     - Multi-country AND multi-year range queries: LIMIT 2000 (or omit LIMIT)
     - Aggregation / GROUP BY queries: omit LIMIT entirely
   Do not impose a tight LIMIT that would truncate a time-series or
   cross-country result set. When in doubt, omit LIMIT.
5. Only add ORDER BY when the question explicitly asks for ordering or a
   "top/highest/lowest/rank" answer — don't add ORDER BY on a single-value
   lookup.
6. For country names, use exact case: "Brazil", "China", "Mexico", "Philippines", "Poland", "Thailand".
7. For year arithmetic, always cast to xsd:integer first.
8. Do NOT add triple patterns the question did not ask for. In particular:
     - Do NOT fetch rdfs:label, rdfs:comment, or descriptions unless the
       question asks for them.  Adding a mandatory label triple will make
       the query return 0 rows for indicators that have no label.
9. Use OPTIONAL (not mandatory joins) for properties/entities that may not
   exist on every member of the result set:
     - RiskScore entities only exist for Brazil and Poland (2023 only).
       If a question joins observation data with a RiskScore for countries
       OTHER than Brazil / Poland, wrap the RiskScore part in OPTIONAL,
       otherwise the whole result set collapses to empty.
     - Component scores (governanceScore, economicHealthScore, …) only
       exist on Poland_RiskScore_2023 — always OPTIONAL them.
10. WGI governance sub-indicators (ControlOfCorruption, GovernmentEffectiveness,
    PoliticalStability, RegulatoryQuality, RuleOfLaw, VoiceAndAccountability)
    are Observation IRIs, NOT RiskScore component properties. When the
    question names one of these WGI terms (even phrased as "effectiveness
    score" or "corruption score"), use the Observation pattern:
      ?obs a gemr:Observation ; gemr:hasCountry ?c ;
           gemr:hasIndicator gemr:GovernmentEffectiveness ; ...
    Do NOT try to read it as ?rs gemr:governanceScore ?score.
11. When the question asks for a specific country, filter by gemr:countryName.
12. When the question asks about composite risk (totalRiskScore, tiering,
    overall risk across all dimensions), use the RiskScore pattern.
13. When the question asks about a specific named economic indicator, use
    the Observation pattern with the correct indicator IRI.
14. FILTER takes only boolean expressions — never put triple patterns or
    aggregates inside it.
15. When the question asks for a "profile", "summary", "overview", or lists
    multiple scores/metrics for an entity, ALWAYS include ?countryName and
    ?year in the SELECT — AND make sure they are *bound* as variables in
    WHERE. A pattern like `?c gemr:countryName "Poland"` filters by literal
    and does NOT bind a variable named ?countryName. To project the country
    name, bind it explicitly:
      ?c gemr:countryName ?countryName . FILTER(STR(?countryName) = "Poland")
    Same for year:
      ?yearEntity gemr:yearValue ?year . FILTER(STR(?year) = "2023")
    Unbound SELECT variables appear as NULL/UNDEF in results and make the
    row ambiguous."""


def build_query_prompt(
    question: str,
    grounded_iris: list[dict],
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Build the user-side prompt for a specific query.

    Includes the grounded IRIs retrieved by the embedding step and the
    user's natural language question.
    """
    # Format grounded IRIs
    iris_section = "RELEVANT IRIs (retrieved from ontology for this question):\n"
    for entry in grounded_iris:
        iris_section += f'  - gemr:{entry["local_name"]} ({entry["type"]}) — {entry["description"]} [relevance: {entry["score"]}]\n'

    # Format conversation history for follow-up context
    history_section = ""
    if conversation_history:
        history_section = "\nPREVIOUS CONVERSATION:\n"
        for msg in conversation_history[-4:]:  # Keep last 4 exchanges
            role = msg["role"].upper()
            content = msg["content"]
            if len(content) > 300:
                content = content[:300] + "..."
            history_section += f"  [{role}]: {content}\n"
        history_section += "\n"

    return f"""{history_section}{iris_section}
QUESTION: {question}

Generate the SPARQL query:"""


def _diagnose_error(failed_sparql: str, error_message: str) -> str:
    """Produce targeted repair hints based on the error message and query shape."""
    hints: list[str] = []
    err_low = (error_message or "").lower()
    sparql_low = (failed_sparql or "").lower()

    # Triple pattern inside FILTER — very common LLM mistake
    import re
    filter_bodies = re.findall(r"filter\s*\(([^)]*)\)", sparql_low, flags=re.IGNORECASE)
    for body in filter_bodies:
        if re.search(r"\?\w+\s+(gemr:|<https?:|rdf:|rdfs:)", body):
            hints.append(
                "A FILTER contains a triple pattern (e.g. FILTER (?s gemr:hasX ?o)). "
                "FILTER takes only boolean expressions. Move the triple pattern out "
                "of the FILTER clause into the WHERE body."
            )
            break

    # Aggregate inside FILTER
    if re.search(r"filter\s*\([^)]*\b(max|min|avg|sum|count)\s*\(", sparql_low):
        hints.append(
            "A FILTER uses an aggregate (MAX/MIN/AVG/SUM/COUNT). Aggregates are "
            "only allowed in SELECT / HAVING / subqueries. Compute the aggregate "
            "in a sub-SELECT with GROUP BY, then join it back in the outer query."
        )

    # Missing GROUP BY variable
    if "not in the group by" in err_low or "not a group by" in err_low:
        hints.append(
            "Every non-aggregated variable in a SELECT with aggregates must appear "
            "in GROUP BY. Either add the variable to GROUP BY or wrap it in an "
            "aggregate like SAMPLE(?x)."
        )

    # Hallucinated inverse property
    if "gemr:hasriskscore" in sparql_low or "gemr:hasobservation" in sparql_low:
        hints.append(
            "Your query uses gemr:hasRiskScore or gemr:hasObservation — these "
            "properties do NOT exist in the ontology. The direction is reversed: "
            "?rs gemr:hasCountry ?country (NOT ?country gemr:hasRiskScore ?rs)."
        )

    # gYear-typed literal in FILTER IN
    if "xsd:gyear" in sparql_low and ("filter" in sparql_low or " in " in sparql_low):
        hints.append(
            "Avoid literal comparisons like \"2020\"^^xsd:gYear because yearValue "
            "is also stored as xsd:integer. Use STR(?yearVar) comparisons instead: "
            "FILTER (STR(?yv) = \"2020\")."
        )

    if not hints:
        return ""
    return "REPAIR HINTS:\n" + "\n".join(f"  • {h}" for h in hints) + "\n\n"


def build_repair_prompt(
    question: str,
    failed_sparql: str,
    error_message: str,
    grounded_iris: list[dict],
) -> str:
    """
    Build a repair prompt for the self-healing loop.
    Includes the failed query and the error message from GraphDB.
    """
    iris_section = "AVAILABLE IRIs:\n"
    for entry in grounded_iris:
        iris_section += f'  - gemr:{entry["local_name"]} ({entry["type"]})\n'

    diagnosis = _diagnose_error(failed_sparql, error_message)

    return f"""{iris_section}
The following SPARQL query FAILED when executed against the GEMR-KG database:

FAILED QUERY:
{failed_sparql}

ERROR:
{error_message}

{diagnosis}ORIGINAL QUESTION: {question}

Fix the query. Output ONLY the corrected SPARQL query — no explanation."""
