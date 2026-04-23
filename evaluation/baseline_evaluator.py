"""
Baseline evaluator: All models via OpenRouter.
Uses an identical minimal GEMR-KG system prompt — no IRI grounding,
no ontology schema dump, no self-healing retry loop.

Supported models:
  - anthropic/claude-haiku-4.5
  - anthropic/claude-sonnet-4.6
  - anthropic/claude-opus-4.6
  - google/gemma-4-26b-a4b-it
  - google/gemma-4-31b-it
  - openai/gpt-5
  - openai/gpt-5-mini
"""

import re
import time
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from evaluation.sparql_utils import execute_sparql

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ── Model Registry ──────────────────────────────────────────────────────────
# Maps short condition names → OpenRouter model IDs
MODEL_REGISTRY: dict[str, str] = {
    "claude_haiku":   "anthropic/claude-haiku-4.5",
    "claude_sonnet":  "anthropic/claude-sonnet-4.6",
    "claude_opus":    "anthropic/claude-opus-4.6",
    "gemma_26b":      "google/gemma-4-26b-a4b-it",
    "gemma_31b":      "google/gemma-4-31b-it",
    "gpt5":           "openai/gpt-5",
    "gpt5_mini":      "openai/gpt-5-mini",
}

ALL_BASELINE_CONDITIONS = list(MODEL_REGISTRY.keys())

BASELINE_SYSTEM_PROMPT = """\
You are a SPARQL query generator for the GEMR-KG (Global Emerging Markets Risk Knowledge Graph).

GEMR-KG ontology namespace: https://gemr-kg.org/ontology# (prefix: gemr:)
Countries: Brazil, China, Mexico, Philippines, Poland, Thailand
Time range: 2002-2023 (annual data)

Main concepts:
- gemr:RiskScore: composite country risk scores
  Properties: gemr:totalRiskScore, gemr:governanceScore, gemr:economicHealthScore, gemr:externalVulnerabilityScore, gemr:contagionRiskScore
- gemr:Observation: economic and credit observations
  Property: gemr:observationValue (numeric)
- Country links: gemr:hasCountry, gemr:countryName (string literal)
- Year links: gemr:hasYear, gemr:yearValue (string literal e.g. "2023")

Standard prefixes:
  PREFIX gemr: <https://gemr-kg.org/ontology#>
  PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
  PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

Output ONLY a valid SPARQL query. No explanation, no markdown fences, no code blocks.\
"""

_openrouter_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _openrouter_client
    if _openrouter_client is None:
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")
        _openrouter_client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )
    return _openrouter_client


def _extract_sparql(text: str) -> str:
    block = re.search(r"```(?:sparql)?\s*\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if block:
        return block.group(1).strip()
    lines, capturing, out = text.strip().splitlines(), False, []
    for line in lines:
        if line.strip().upper().startswith(("PREFIX", "SELECT", "ASK", "CONSTRUCT", "DESCRIBE")):
            capturing = True
        if capturing:
            out.append(line)
    return "\n".join(out).strip() if out else text.strip()


def _call_model(model_id: str, question: str) -> str:
    """Call a model via OpenRouter with the baseline system prompt."""
    client = _get_client()
    # GPT-5 family reasoning models require `max_completion_tokens` and reject
    # `max_tokens`. Also they ignore `temperature` != 1 — leave it at default.
    is_gpt5 = "gpt-5" in model_id
    for attempt in range(3):
        try:
            kwargs = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
                    {"role": "user", "content": f"QUESTION: {question}\n\nGenerate the SPARQL query:"},
                ],
            }
            if is_gpt5:
                kwargs["max_completion_tokens"] = 6000
            else:
                kwargs["temperature"] = 0.1
                kwargs["max_tokens"] = 600
            response = client.chat.completions.create(**kwargs)
            raw = response.choices[0].message.content or ""
            return _extract_sparql(raw)
        except Exception as e:
            err = str(e)
            if any(x in err for x in ("429", "rate_limit", "RESOURCE_EXHAUSTED", "529", "503")):
                wait = 15 * (attempt + 1)
                print(f"    [rate limit] waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    [error] {err[:150]}")
                raise
    return ""


def evaluate_baseline_question(question: str, condition: str) -> dict:
    """
    Run one question through the chosen baseline model via OpenRouter.

    Args:
        question:  The natural language question.
        condition: One of the keys in MODEL_REGISTRY (e.g. "claude_haiku", "gpt5").

    Returns:
        {sparql, execution, elapsed_seconds}
    """
    if condition not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown condition '{condition}'. "
            f"Valid: {', '.join(MODEL_REGISTRY.keys())}"
        )

    model_id = MODEL_REGISTRY[condition]
    t0 = time.time()

    try:
        sparql = _call_model(model_id, question)
    except Exception as e:
        return {
            "sparql": "",
            "execution": {"success": False, "data": None, "error": str(e)[:200], "status_code": 0},
            "elapsed_seconds": round(time.time() - t0, 2),
        }

    if sparql:
        execution = execute_sparql(sparql)
    else:
        execution = {"success": False, "data": None, "error": "Empty SPARQL generated", "status_code": 0}

    return {
        "sparql": sparql,
        "execution": execution,
        "elapsed_seconds": round(time.time() - t0, 2),
    }
