# backend/ — GEMR-KG NL→SPARQL API

FastAPI server that turns a natural-language question into a SPARQL query, runs
it against GraphDB, self-heals on failure, and returns both the raw bindings
and a natural-language summary. This is the same pipeline as the one evaluated
in `evaluation/EVALUATION_REPORT.md` (78.1 % Answer Accuracy).

## Prerequisites

1. **GraphDB** running with the `GEMR` repository.
   ```bash
   docker start graphdb-instance          # first time: see Docker/ for image build
   curl http://localhost:7200/rest/repositories   # sanity check
   ```
2. **Python 3.12+** in the repo's `.venv` (created at project root).
3. **Environment** — copy or create `backend/.env` with:
   ```
   GEMINI_API_KEY=...            # used only for cached embeddings build
   OPENROUTER_API_KEY=sk-or-...  # primary LLM provider
   GRAPHDB_URL=http://localhost:7200
   GRAPHDB_REPO=GEMR
   DEFAULT_MODEL_KEY=gemini-2.5-flash   # optional; override the default LLM
   ```

## Run the API

From the repo root:

```bash
.venv/bin/python -m uvicorn backend.main:app --reload --port 8000
```

First boot does three things and prints progress:
1. Loads the ontology (classes, properties, indicators, countries).
2. Loads cached schema embeddings from `backend/cache/predicate_embeddings.json`
   (rebuilt only if missing).
3. Builds the static system prompt.

Once it prints `✓ Pipeline ready! Accepting requests.`, the API is live on
`http://localhost:8000`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/api/health`  | Reports schema-loaded state and the country list. |
| `GET`  | `/api/models`  | Returns the LLM catalogue and the default key (used by the frontend's picker). |
| `POST` | `/api/ask`     | Main entry point. Body: `{question, use_history?, model?}`. |
| `POST` | `/api/reset`   | Clears the rolling 10-turn conversation history. |

### `/api/ask` body

```json
{ "question": "What was Brazil's GDP in 2020?",
  "use_history": true,
  "model": "gemini-2.5-flash" }
```

`model` is one of the short keys from `/api/models`. Omit it, send `null`, or
send an unknown key and the server falls back to `DEFAULT_MODEL_KEY`.

### `/api/ask` response

```json
{
  "success": true,
  "question": "...",
  "sparql":  "PREFIX gemr: ... SELECT ?value WHERE { ... }",
  "nl_answer": "Brazil's GDP in 2020 was ...",
  "results":  { "head": {"vars": [...]}, "results": {"bindings": [...]} },
  "attempts": 1,
  "grounded_iris": [ {iri, label, type, score}, ... ],
  "elapsed_seconds": 2.4,
  "history": [ {attempt, success, error}, ... ],
  "model": "gemini-2.5-flash"
}
```

## Changing which LLM is default

All the LLM wiring is in `backend/config.py` (`AVAILABLE_MODELS` dict and
`DEFAULT_MODEL_KEY`). Everything else (SPARQL generation, self-healing repair,
natural-language answer) goes through `backend/pipeline/sparql_generator.py`
and `answer_generator.py`, which both use the same OpenRouter client and
respect the per-request `model` key.

To add a new model, add one entry to `AVAILABLE_MODELS`:

```python
"llama-3-70b": {
    "id": "meta-llama/llama-3.3-70b-instruct",
    "display_name": "Llama 3.3 70B",
    "notes": "Open weights via OpenRouter.",
},
```

The frontend picker populates itself from `/api/models`, so no frontend change
is needed.

## Why the default is Gemini 2.5 Flash

On our 73-question benchmark (see `evaluation/EVALUATION_REPORT.md`):

| Model (all grounded via the same pipeline) | AA | Avg time |
|---|---|---|
| **Gemini 2.5 Flash** | **78.1 %** | **2.5 s** |
| Baseline LLMs without grounding | 0 – 5.5 % | 2.5 – 46 s |

The pipeline's accuracy comes mostly from **IRI grounding**, not the LLM
choice; swapping Gemini 2.5 Flash for Claude Sonnet or GPT-5 produces similar
SPARQL at higher latency / cost. Ship the default, expose the picker for
experimentation.

## Troubleshooting

- **`OPENROUTER_API_KEY is not set`** — add it to `backend/.env` and restart uvicorn.
- **`Cannot connect to GraphDB`** — `docker start graphdb-instance`, then retry.
- **GraphDB becomes slow after many queries** — under heavy load (e.g. an
  evaluation sweep) it can wedge. `docker restart graphdb-instance` clears it.
- **Pipeline returns empty results** — the self-healer gets up to 3 attempts;
  the `history` array in the response shows each attempt's error.
