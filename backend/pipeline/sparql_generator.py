"""
SPARQL Generator — calls the configured LLM to generate SPARQL from a structured prompt.

Uses LiteLLM for provider-agnostic access (Gemini, Anthropic, OpenAI, etc.).
"""
import logging
import re
import time

import litellm

from ..config import AVAILABLE_MODELS, DEFAULT_MODEL_KEY

logger = logging.getLogger(__name__)

# Suppress LiteLLM's verbose default output
litellm.suppress_debug_info = True


def resolve_model(model_key: str | None) -> tuple[str, str]:
    """Map a short UI key (or None) to the LiteLLM model id.

    Returns (litellm_model_id, resolved_short_key).
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
    """Call the chosen LLM via LiteLLM to produce SPARQL.

    Args:
        system_prompt: The static ontology-aware system prompt.
        query_prompt:  The per-question prompt (includes grounded IRIs).
        model_key:     Optional short key from AVAILABLE_MODELS; None → default.
    """
    model_id, _ = resolve_model(model_key)
    # Reasoning models (o1/o3/gpt-5 family) reject temperature and use max_completion_tokens
    is_reasoning = any(x in model_id for x in ("o1", "o3", "gpt-5"))

    for attempt in range(3):
        try:
            kwargs: dict = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query_prompt},
                ],
                "drop_params": True,  # silently drop params unsupported by the provider
            }
            if is_reasoning:
                kwargs["max_completion_tokens"] = 6000
            else:
                kwargs["temperature"] = 0.1
                kwargs["max_tokens"] = 2048

            response = litellm.completion(**kwargs)
            raw = response.choices[0].message.content or ""
            return _extract_sparql(raw)
        except Exception as e:
            err = str(e)
            if any(x in err for x in ("429", "rate_limit", "RESOURCE_EXHAUSTED", "529", "503")):
                wait = 10 * (attempt + 1)
                logger.warning("Rate-limited on %s, retrying in %ds (attempt %d/3)", model_id, wait, attempt + 1)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"SPARQL generation failed after 3 attempts ({model_id})")
