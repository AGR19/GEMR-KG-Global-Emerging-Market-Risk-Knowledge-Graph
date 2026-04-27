"""
Answer Generator — produces a natural-language summary of GraphDB results.

Uses LiteLLM for the same provider-agnostic access as the SPARQL generator.
"""
import logging
import time

import litellm

from .sparql_generator import resolve_model

logger = logging.getLogger(__name__)


def generate_natural_language_answer(
    question: str,
    results: dict,
    model_key: str | None = None,
) -> str:
    """Ask the LLM to summarise what GraphDB returned.

    Args:
        question:   The user's original NL question.
        results:    Raw SPARQL JSON (head + bindings) returned by GraphDB.
        model_key:  Optional short key; defaults to the same one used for SPARQL gen.
    """
    bindings = results.get("results", {}).get("bindings", [])
    if not bindings:
        return ("I queried the database, but no data was found that matched your "
                "question. The data might not exist in the Knowledge Graph yet.")

    simplified_data: list[dict] = []
    for row in bindings[:50]:
        simplified_row: dict[str, str] = {}
        for var, val in row.items():
            value = val.get("value", "")
            if "https://gemr-kg.org/ontology#" in value:
                value = value.split("#")[-1]
            simplified_row[var] = value
        simplified_data.append(simplified_row)

    snippet_msg = ""
    if len(bindings) > 50:
        snippet_msg = f" (showing the first 50 of {len(bindings)} total rows)"

    prompt = f"""You are an expert AI assistant for a macroeconomic and political risk database called GEMR-KG.
The user asked a question, and we executed a graph-database query behind the scenes to fetch the following data.

USER QUESTION: {question}

DATA RETURNED{snippet_msg}:
{simplified_data}

INSTRUCTIONS:
1. Provide a clear natural-language summary that answers the user's question.
2. The user will also see the raw table below your answer, so DO NOT list every row.
3. Describe the big picture: overall trend, highest/lowest points, or the general conclusion.
4. Be plain, direct, and concise. Avoid heavy formatting.
5. DO NOT explain the graph database, the SPARQL query, or the pipeline."""

    model_id, _ = resolve_model(model_key)
    is_reasoning = any(x in model_id for x in ("o1", "o3", "gpt-5"))

    for attempt in range(3):
        try:
            kwargs: dict = {
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "drop_params": True,
            }
            if is_reasoning:
                kwargs["max_completion_tokens"] = 2000
            else:
                kwargs["temperature"] = 0.3
                kwargs["max_tokens"] = 800

            response = litellm.completion(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            err = str(e)
            if any(x in err for x in ("429", "rate_limit", "RESOURCE_EXHAUSTED", "529", "503")):
                wait = 10 * (attempt + 1)
                logger.warning("Rate-limited on %s, retrying in %ds (attempt %d/3)", model_id, wait, attempt + 1)
                time.sleep(wait)
                continue
            raise

    return ("I retrieved the results, but the language model is currently under "
            "heavy load and couldn't generate a summary.")
