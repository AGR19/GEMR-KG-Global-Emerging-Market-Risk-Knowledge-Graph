"""
Configuration loader for the GEMR-KG NL→SPARQL pipeline.
Reads settings from .env and resolves file paths.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend directory
BACKEND_DIR = Path(__file__).parent
load_dotenv(BACKEND_DIR / ".env")

# Project root (one level up from backend/)
PROJECT_ROOT = BACKEND_DIR.parent

# --- Gemini API (still used for embeddings, cached on disk) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")  # legacy; not used by runtime any more
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

# --- OpenRouter API (primary LLM provider, matches the evaluation pipeline) ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model registry — short keys the frontend picks from, mapped to OpenRouter IDs.
# 'gemini-2.5-flash' is the default because it scored 78.1% AA (vs best baseline
# 5.5%) on the 73-question benchmark while being the fastest system (2.5s avg).
AVAILABLE_MODELS: dict[str, dict] = {
    "gemini-2.5-flash": {
        "id": "google/gemini-2.5-flash",
        "display_name": "Gemini 2.5 Flash (default, best AA)",
        "notes": "Fastest and highest answer-accuracy in benchmark.",
    },
    "claude-haiku": {
        "id": "anthropic/claude-haiku-4.5",
        "display_name": "Claude Haiku 4.5",
        "notes": "Fast and cheap; strong syntactic compliance.",
    },
    "claude-sonnet": {
        "id": "anthropic/claude-sonnet-4.6",
        "display_name": "Claude Sonnet 4.6",
        "notes": "Most accurate Claude; slower.",
    },
    "claude-opus": {
        "id": "anthropic/claude-opus-4.6",
        "display_name": "Claude Opus 4.6",
        "notes": "Largest Claude.",
    },
    "gpt-5-mini": {
        "id": "openai/gpt-5-mini",
        "display_name": "GPT-5 Mini (reasoning)",
        "notes": "OpenAI reasoning model; cheaper than GPT-5.",
    },
    "gpt-5": {
        "id": "openai/gpt-5",
        "display_name": "GPT-5 (reasoning)",
        "notes": "Slowest in benchmark (~45 s/q); reasoning-first.",
    },
}
DEFAULT_MODEL_KEY = os.getenv("DEFAULT_MODEL_KEY", "gemini-2.5-flash")

# --- GraphDB ---
GRAPHDB_URL = os.getenv("GRAPHDB_URL", "http://localhost:7200")
GRAPHDB_REPO = os.getenv("GRAPHDB_REPO", "GEMR")
SPARQL_ENDPOINT = f"{GRAPHDB_URL}/repositories/{GRAPHDB_REPO}"

# --- Data files ---
OWL_FILE = PROJECT_ROOT / "ontology" / "final-gemr-fibo-reasoned.owl"
TTL_FILE = PROJECT_ROOT / "Final_GEMR_Submission.ttl"

# --- Pipeline settings ---
MAX_HEAL_ATTEMPTS = 3          # Self-healing retries
TOP_K_IRIS = 15                # Number of IRIs to retrieve per query
EMBEDDING_CACHE_FILE = BACKEND_DIR / "cache" / "predicate_embeddings.json"
