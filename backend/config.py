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

# --- Gemini API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

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
