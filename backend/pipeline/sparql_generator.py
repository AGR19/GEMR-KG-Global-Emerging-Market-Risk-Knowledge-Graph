"""
SPARQL Generator — Calls Gemini to generate SPARQL from a structured prompt.

Handles the LLM call and extracts a clean SPARQL query from the response.
"""
import re
from google import genai

from ..config import GEMINI_API_KEY, GEMINI_MODEL


client = genai.Client(api_key=GEMINI_API_KEY)


def _extract_sparql(text: str) -> str:
    """
    Extract a SPARQL query from LLM output.
    Handles cases where the model wraps it in code fences or adds explanation.
    """
    # Try to extract from code fences first
    code_block = re.search(r"```(?:sparql)?\s*\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if code_block:
        return code_block.group(1).strip()

    # Look for content starting with PREFIX or SELECT/ASK/CONSTRUCT
    lines = text.strip().splitlines()
    sparql_lines = []
    capturing = False

    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith(("PREFIX", "SELECT", "ASK", "CONSTRUCT", "DESCRIBE")):
            capturing = True
        if capturing:
            sparql_lines.append(line)

    if sparql_lines:
        return "\n".join(sparql_lines).strip()

    # Fallback: return the whole text (hope for the best)
    return text.strip()


def generate_sparql(
    system_prompt: str,
    query_prompt: str,
) -> str:
    """
    Call Gemini to generate a SPARQL query.

    Args:
        system_prompt: The static ontology-aware system prompt.
        query_prompt: The per-query prompt with grounded IRIs and question.

    Returns:
        The extracted SPARQL query string.
    """
    import time
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    {"role": "user", "parts": [{"text": system_prompt}]},
                    {"role": "model", "parts": [{"text": "I understand the GEMR-KG ontology schema and rules. I will generate valid SPARQL queries using only the provided IRIs and patterns. Send me a question."}]},
                    {"role": "user", "parts": [{"text": query_prompt}]},
                ],
                config={
                    "temperature": 0.1,  # Low temperature for deterministic structured output
                    "max_output_tokens": 2048,
                },
            )
            raw_text = response.text
            return _extract_sparql(raw_text)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "503" in error_str or "UNAVAILABLE" in error_str:
                wait = 10 * (attempt + 1)
                print(f"  [Generator] API busy/rate-limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("SPARQL generation failed after 3 attempts")
