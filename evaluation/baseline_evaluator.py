"""
Baseline evaluator: GPT-4o (OpenAI) and Claude Sonnet (via OpenRouter).
Both use the identical minimal GEMR-KG system prompt — no IRI grounding,
no ontology schema dump, no self-healing retry loop.
"""

import re
import time
import os
import sys
from typing import Literal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from evaluation.sparql_utils import execute_sparql

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

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

_openai_client: OpenAI | None = None
_openrouter_client: OpenAI | None = None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


def _get_openrouter_client() -> OpenAI:
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


def _call_model(client: OpenAI, model: str, question: str) -> str:
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
                    {"role": "user", "content": f"QUESTION: {question}\n\nGenerate the SPARQL query:"},
                ],
                temperature=0.1,
                max_tokens=600,
            )
            raw = response.choices[0].message.content or ""
            return _extract_sparql(raw)
        except Exception as e:
            err = str(e)
            if any(x in err for x in ("429", "rate_limit", "RESOURCE_EXHAUSTED", "529")):
                wait = 15 * (attempt + 1)
                print(f"    [rate limit] waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    [error] {err[:120]}")
                raise
    return ""


def evaluate_baseline_question(
    question: str,
    condition: Literal["gpt4o", "claude"],
) -> dict:
    """
    Run one question through the chosen baseline condition.

    Returns:
        {sparql, execution, elapsed_seconds}
    """
    t0 = time.time()

    try:
        if condition == "gpt4o":
            sparql = _call_model(_get_openai_client(), OPENAI_MODEL, question)
        else:
            sparql = _call_model(_get_openrouter_client(), OPENROUTER_MODEL, question)
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
