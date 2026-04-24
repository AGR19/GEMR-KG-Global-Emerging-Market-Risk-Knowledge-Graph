"""
GEMR-KG NL→SPARQL API Server

Implements the ontology-aware pipeline from the paper:
  1. Embedding-Guided IRI Grounding
  2. Ontology-Constrained Prompting
  3. Self-Healing Refinement Loop

Endpoints:
  POST /api/ask  — Translate natural language to SPARQL and execute
  GET  /api/health — Health check
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import OWL_FILE, TTL_FILE, AVAILABLE_MODELS, DEFAULT_MODEL_KEY
from .pipeline.schema_loader import load_schema, GEMRSchema
from .pipeline.embedder import build_embeddings
from .pipeline.grounding import retrieve_relevant_iris
from .pipeline.prompt_builder import build_system_prompt, build_query_prompt
from .pipeline.sparql_generator import generate_sparql, resolve_model
from .pipeline.self_healer import heal_and_execute
from .pipeline.answer_generator import generate_natural_language_answer


# ─── Global State ───────────────────────────────────────────
schema: GEMRSchema | None = None
embedded_entries: list[dict] = []
system_prompt: str = ""
conversation_history: list[dict] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load schema and build embeddings at startup."""
    global schema, embedded_entries, system_prompt

    print("=" * 60)
    print("  GEMR-KG NL→SPARQL Pipeline — Starting up...")
    print("=" * 60)

    # Step 1: Load ontology schema
    print("\n[1/3] Loading ontology schema...")
    schema = load_schema(OWL_FILE, TTL_FILE)
    print(f"  ✓ {len(schema.classes)} classes")
    print(f"  ✓ {len(schema.properties)} properties")
    print(f"  ✓ {len(schema.indicators)} indicators")
    print(f"  ✓ {len(schema.countries)} countries: {', '.join(schema.countries)}")
    print(f"  ✓ {len(schema.observation_types)} observation types")

    # Step 2: Build/load embeddings
    print("\n[2/3] Building embeddings...")
    embedded_entries = build_embeddings(schema)
    print(f"  ✓ {len(embedded_entries)} entries embedded")

    # Step 3: Build system prompt
    print("\n[3/3] Building system prompt...")
    system_prompt = build_system_prompt(schema)
    print(f"  ✓ System prompt ready ({len(system_prompt)} chars)")

    print("\n" + "=" * 60)
    print("  ✓ Pipeline ready! Accepting requests.")
    print("=" * 60 + "\n")

    yield  # App runs here

    print("\nShutting down...")


# ─── FastAPI App ────────────────────────────────────────────
app = FastAPI(
    title="GEMR-KG NL→SPARQL API",
    description="Ontology-aware natural language to SPARQL pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow CORS for the Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Models ───────────────────────────────

class AskRequest(BaseModel):
    question: str
    use_history: bool = True                # Include conversation context for follow-ups
    model: str | None = None                # Short key from AVAILABLE_MODELS; None → default


class AskResponse(BaseModel):
    success: bool
    question: str
    sparql: str
    nl_answer: str | None = None
    results: dict | None = None
    attempts: int = 1
    grounded_iris: list[dict] = []
    elapsed_seconds: float = 0.0
    error: str | None = None
    history: list[dict] = []
    model: str | None = None                # The short key actually used to produce this answer


# ─── Endpoints ──────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """Health check — confirms the pipeline is loaded and ready."""
    return {
        "status": "ok",
        "schema_loaded": schema is not None,
        "entries_embedded": len(embedded_entries),
        "countries": schema.countries if schema else [],
    }


@app.get("/api/models")
async def list_models():
    """Return the catalogue of LLMs the pipeline can be run against.

    The frontend uses this to populate the model picker. `default` is the
    key pre-selected in the UI (Gemini 2.5 Flash — highest AA in the
    benchmark, see evaluation/EVALUATION_REPORT.md).
    """
    return {
        "default": DEFAULT_MODEL_KEY,
        "models": [
            {"key": key, "display_name": info["display_name"],
             "openrouter_id": info["id"], "notes": info["notes"]}
            for key, info in AVAILABLE_MODELS.items()
        ],
    }


@app.post("/api/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    Main endpoint: translate a natural language question to SPARQL,
    execute it against GraphDB, and return results.
    """
    global conversation_history

    start = time.time()
    question = request.question.strip()
    _, model_key = resolve_model(request.model)  # normalises None / unknown → default

    print(f"\n{'─' * 50}")
    print(f"Question: {question}")
    print(f"Model:    {model_key}")
    print(f"{'─' * 50}")

    try:
        # Step 1: Embedding-Guided IRI Grounding
        print("[Pipeline] Step 1: IRI Grounding...")
        grounded = retrieve_relevant_iris(question, embedded_entries)
        print(f"  Retrieved {len(grounded)} IRIs (top: {grounded[0]['local_name']} @ {grounded[0]['score']})")

        # Step 2: Build Ontology-Constrained Prompt
        print("[Pipeline] Step 2: Building prompt...")
        history_ctx = conversation_history if request.use_history else None
        query_prompt = build_query_prompt(question, grounded, history_ctx)

        # Step 3: Generate SPARQL
        print("[Pipeline] Step 3: Generating SPARQL...")
        sparql = generate_sparql(system_prompt, query_prompt, model_key=model_key)
        print(f"  Generated query ({len(sparql)} chars)")

        # Step 4: Self-Healing Execution
        print("[Pipeline] Step 4: Execute + Self-Heal...")
        result = heal_and_execute(question, sparql, system_prompt, grounded, model_key=model_key)

        nl_answer = None
        if result["success"]:
            print(f"[Pipeline] ✓ Done in {round(time.time() - start, 2)}s ({result['attempts']} attempt(s)). Generating NL Answer...")
            nl_answer = generate_natural_language_answer(question, result["data"], model_key=model_key)

        elapsed = round(time.time() - start, 2)

        # Update conversation history
        conversation_history.append({"role": "user", "content": question})
        conversation_history.append({
            "role": "assistant",
            "content": f"Generated SPARQL query ({result['attempts']} attempt(s)): {result['sparql'][:200]}..."
        })
        # Keep history bounded
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]

        # Simplify grounded IRIs for response (strip embeddings)
        grounded_clean = [
            {"iri": g["iri"], "label": g["label"], "type": g["type"], "score": g["score"]}
            for g in grounded[:8]
        ]

        if result["success"]:
            print(f"[Pipeline] ✓ Finished in {elapsed}s")
        else:
            print(f"[Pipeline] ✗ Failed after {result['attempts']} attempts in {elapsed}s")

        return AskResponse(
            success=result["success"],
            question=question,
            sparql=result["sparql"],
            nl_answer=nl_answer,
            results=result["data"],
            attempts=result["attempts"],
            grounded_iris=grounded_clean,
            elapsed_seconds=elapsed,
            error=result["history"][-1]["error"] if not result["success"] else None,
            history=result["history"],
            model=model_key,
        )

    except Exception as e:
        elapsed = round(time.time() - start, 2)
        print(f"[Pipeline] ✗ Error: {e}")
        return AskResponse(
            success=False,
            question=question,
            sparql="",
            error=str(e),
            elapsed_seconds=elapsed,
            model=model_key,
        )


@app.post("/api/reset")
async def reset_history():
    """Clear conversation history."""
    global conversation_history
    conversation_history = []
    return {"status": "ok", "message": "Conversation history cleared"}
