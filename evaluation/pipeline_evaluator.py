"""
Full pipeline evaluator: Gemini embeddings (cached) + IRI grounding + OpenRouter SPARQL generation + self-healing.
Uses OpenRouter for LLM calls since Gemini direct API is IP-throttled.
Embeddings are loaded from cache so no Gemini API calls needed.
"""

import sys
import os
import re
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from openai import OpenAI
from backend.config import OWL_FILE, TTL_FILE
from backend.pipeline.schema_loader import load_schema, GEMRSchema
from backend.pipeline.embedder import build_embeddings
from backend.pipeline.grounding import retrieve_relevant_iris
from backend.pipeline.prompt_builder import build_system_prompt, build_query_prompt, build_repair_prompt
from backend.pipeline.self_healer import execute_sparql

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("PIPELINE_MODEL", "google/gemini-2.0-flash-001")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MAX_HEAL_ATTEMPTS = 3

_schema: GEMRSchema | None = None
_embedded_entries: list[dict] = []
_system_prompt: str = ""
_or_client: OpenAI | None = None


def _get_or_client() -> OpenAI:
    global _or_client
    if _or_client is None:
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")
        _or_client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    return _or_client


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


def _generate_sparql_via_openrouter(system_prompt: str, query_prompt: str) -> str:
    client = _get_or_client()
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query_prompt},
                ],
                temperature=0.1,
                max_tokens=1500,
            )
            raw = response.choices[0].message.content or ""
            return _extract_sparql(raw)
        except Exception as e:
            err = str(e)
            if any(x in err for x in ("429", "rate_limit", "RESOURCE_EXHAUSTED", "529", "503")):
                wait = 15 * (attempt + 1)
                print(f"    [OpenRouter] Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("SPARQL generation via OpenRouter failed after 3 attempts")


def _heal_and_execute(question: str, initial_sparql: str, grounded_iris: list[dict]) -> dict:
    history = []
    current_sparql = initial_sparql

    for attempt in range(1, MAX_HEAL_ATTEMPTS + 1):
        result = execute_sparql(current_sparql)
        bindings = result.get("data", {}).get("results", {}).get("bindings", []) if result.get("data") else []

        history.append({
            "attempt": attempt,
            "sparql": current_sparql,
            "success": result["success"],
            "error": result.get("error"),
        })

        if result["success"] and bindings:
            return {"success": True, "sparql": current_sparql, "data": result["data"],
                    "attempts": attempt, "history": history}

        if result.get("status_code") == 0:
            break

        if attempt >= MAX_HEAL_ATTEMPTS:
            break

        if result["success"] and not bindings:
            error_msg = "Query returned ZERO results. The indicator or property IRI is likely wrong. Use the grounded IRIs provided."
        else:
            error_msg = result.get("error", "Unknown error")[:500]

        repair_prompt = build_repair_prompt(question, current_sparql, error_msg, grounded_iris)
        current_sparql = _generate_sparql_via_openrouter(_system_prompt, repair_prompt)

    return {"success": False, "sparql": current_sparql, "data": None,
            "attempts": len(history), "history": history}


def initialize_pipeline() -> None:
    global _schema, _embedded_entries, _system_prompt

    if _schema is not None:
        return

    print("[Pipeline] Loading ontology schema...")
    _schema = load_schema(OWL_FILE, TTL_FILE)
    print(f"  {len(_schema.classes)} classes, {len(_schema.properties)} properties, "
          f"{len(_schema.observation_types)} observation types, {len(_schema.countries)} countries")

    print("[Pipeline] Building embeddings (uses cache if available)...")
    _embedded_entries = build_embeddings(_schema)
    print(f"  {len(_embedded_entries)} entries embedded")

    print("[Pipeline] Building system prompt...")
    _system_prompt = build_system_prompt(_schema)
    print(f"  System prompt ready ({len(_system_prompt)} chars)")
    print(f"  LLM: OpenRouter → {OPENROUTER_MODEL}\n")


def evaluate_pipeline_question(question: str) -> dict:
    if _schema is None:
        raise RuntimeError("Call initialize_pipeline() before evaluating questions.")

    t0 = time.time()

    grounded = retrieve_relevant_iris(question, _embedded_entries)
    query_prompt = build_query_prompt(question, grounded, conversation_history=None)
    initial_sparql = _generate_sparql_via_openrouter(_system_prompt, query_prompt)
    result = _heal_and_execute(question, initial_sparql, grounded)

    return {
        "sparql": result["sparql"],
        "initial_sparql": initial_sparql,
        "grounded_iris": [
            {"iri": g["iri"], "label": g["label"], "type": g["type"], "score": round(g["score"], 4)}
            for g in grounded[:8]
        ],
        "execution": {
            "success": result["success"],
            "data": result["data"],
            "error": result["history"][-1]["error"] if not result["success"] else None,
            "status_code": 200 if result["success"] else 0,
        },
        "attempts": result["attempts"],
        "history": result["history"],
        "elapsed_seconds": round(time.time() - t0, 2),
    }
