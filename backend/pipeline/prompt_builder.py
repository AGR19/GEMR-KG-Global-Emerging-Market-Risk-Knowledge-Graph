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
STRICT RULES
═══════════════════════════════════════

1. Output ONLY a valid SPARQL query — no explanation, no markdown, no code fences.
2. Use ONLY the IRIs and properties listed above or provided in the grounded IRIs.
3. Do NOT invent or hallucinate IRIs that are not in the schema.
4. Always include ORDER BY and LIMIT (default LIMIT 100).
5. For country names, use exact case: "Brazil", "China", "Mexico", "Philippines", "Poland", "Thailand".
6. For year arithmetic, always cast to xsd:integer first.
7. Use OPTIONAL for properties that may not exist on every entity.
8. When the question asks for a specific country, filter by gemr:countryName.
9. When the question asks about risk, use the RiskScore pattern.
10. When the question asks about economic indicators, use the Observation pattern with the correct type."""


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

    return f"""{iris_section}
The following SPARQL query FAILED when executed against the GEMR-KG database:

FAILED QUERY:
{failed_sparql}

ERROR:
{error_message}

ORIGINAL QUESTION: {question}

Fix the query. Output ONLY the corrected SPARQL query — no explanation."""
