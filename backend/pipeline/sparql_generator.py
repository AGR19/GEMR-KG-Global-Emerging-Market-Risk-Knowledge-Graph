"""
SPARQL Generator — calls OpenRouter to generate SPARQL from a structured prompt.

Matches the evaluation pipeline in `evaluation/pipeline_evaluator.py`:
  - OpenRouter via OpenAI SDK (base_url = https://openrouter.ai/api/v1)
  - default model = AVAILABLE_MODELS[DEFAULT_MODEL_KEY] (Gemini 2.5 Flash)
  - caller may override per request via `model_key` arg
"""
import re
import time

from openai import OpenAI

from ..config import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL_KEY,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
)


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is not set in backend/.env")
        _client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    return _client


def resolve_model(model_key: str | None) -> tuple[str, str]:
    """Map a short UI key (or None) to the OpenRouter model id.

    Returns (openrouter_model_id, resolved_short_key).
    Falls back to the default if the key is unknown.
    """
    key = model_key or DEFAULT_MODEL_KEY
    if key not in AVAILABLE_MODELS:
        key = DEFAULT_MODEL_KEY
    return AVAILABLE_MODELS[key]["id"], key


def _extract_sparql(text: str) -> str:
    """Pull a SPARQL query out of arbitrary LLM output."""
    code_block = re.search(r"```(?:sparql)?\s*\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if code_block:
        return code_block.group(1).strip()

    lines = text.strip().splitlines()
    sparql_lines: list[str] = []
    capturing = False
    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith(("PREFIX", "SELECT", "ASK", "CONSTRUCT", "DESCRIBE")):
            capturing = True
        if capturing:
            sparql_lines.append(line)
    if sparql_lines:
        return "\n".join(sparql_lines).strip()
    return text.strip()


def generate_sparql(
    system_prompt: str,
    query_prompt: str,
    model_key: str | None = None,
) -> str:
    """Call the chosen LLM (via OpenRouter) to produce SPARQL.

    Args:
        system_prompt: The static ontology-aware system prompt.
        query_prompt: The per-question prompt (includes grounded IRIs).
        model_key:    Optional short key from AVAILABLE_MODELS; None → default.
    """
    model_id, _ = resolve_model(model_key)
    client = _get_client()

    # GPT-5 reasoning models reject `max_tokens` and `temperature != 1`.
    is_gpt5 = "gpt-5" in model_id

    for attempt in range(3):
        try:
            kwargs: dict = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query_prompt},
                ],
            }
            if is_gpt5:
                kwargs["max_completion_tokens"] = 6000
            else:
                kwargs["temperature"] = 0.1
                kwargs["max_tokens"] = 2048
            response = client.chat.completions.create(**kwargs)
            raw = response.choices[0].message.content or ""
            return _extract_sparql(raw)
        except Exception as e:
            err = str(e)
            if any(x in err for x in ("429", "rate_limit", "RESOURCE_EXHAUSTED", "529", "503")):
                wait = 10 * (attempt + 1)
                print(f"  [Generator] rate-limited on {model_id}, waiting {wait}s...")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"SPARQL generation failed after 3 attempts ({model_id})")
