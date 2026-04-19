"""
Embedder — Creates and caches semantic embeddings for ontology predicates using Gemini.

Uses Gemini's text-embedding-004 model to embed enriched predicate descriptions.
Embeddings are cached to disk so they only need to be computed once.
"""
import json
import numpy as np
from pathlib import Path
from google import genai

from ..config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL, EMBEDDING_CACHE_FILE
from .schema_loader import GEMRSchema


# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


def _build_enriched_descriptions(schema: GEMRSchema) -> list[dict]:
    """
    Build enriched text descriptions for each property and observation type.
    These descriptions are what get embedded for semantic matching.
    """
    entries = []

    # Properties from OWL (hasCountry, hasYear, observationValue, etc.)
    for prop in schema.properties:
        entries.append({
            "iri": prop.iri,
            "local_name": prop.local_name,
            "label": prop.label,
            "description": prop.description,
            "type": "property",
        })

    # Observation types / Indicator classes (PrivateDefaultRate, GDP_CONST_2010_USD, etc.)
    for obs_type in schema.observation_types:
        readable = obs_type.replace("_", " ")
        entries.append({
            "iri": f"https://gemr-kg.org/ontology#{obs_type}",
            "local_name": obs_type,
            "label": readable,
            "description": f"{readable} — an observation type / indicator class in the GEMR knowledge graph",
            "type": "observation_type",
        })

    # Indicator URIs (these map to hasIndicator values)
    for indicator in schema.indicators:
        readable = indicator.replace("_", " ")
        entries.append({
            "iri": f"https://gemr-kg.org/ontology#{indicator}",
            "local_name": indicator,
            "label": readable,
            "description": f"{readable} — a data indicator tracking economic or risk metrics",
            "type": "indicator",
        })

    return entries


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using Gemini's embedding API."""
    # Gemini embedding API supports batching
    result = client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=texts,
    )
    return [emb.values for emb in result.embeddings]


def build_embeddings(schema: GEMRSchema, force_rebuild: bool = False) -> list[dict]:
    """
    Build or load cached embeddings for all ontology entries.

    Returns a list of dicts, each with:
      - iri, local_name, label, description, type
      - embedding: list[float]
    """
    cache_path = Path(EMBEDDING_CACHE_FILE)

    # Return cached if available
    if cache_path.exists() and not force_rebuild:
        print("[Embedder] Loading cached embeddings...")
        with open(cache_path, "r") as f:
            return json.load(f)

    print("[Embedder] Building enriched descriptions...")
    entries = _build_enriched_descriptions(schema)

    if not entries:
        print("[Embedder] WARNING: No entries to embed!")
        return []

    # Embed all descriptions in batches of 50
    print(f"[Embedder] Embedding {len(entries)} entries with {GEMINI_EMBEDDING_MODEL}...")
    descriptions = [e["description"] for e in entries]

    all_embeddings = []
    batch_size = 20  # Smaller batches to avoid rate limits
    for i in range(0, len(descriptions), batch_size):
        batch = descriptions[i : i + batch_size]

        # Retry with backoff for rate limits
        for attempt in range(5):
            try:
                batch_embeddings = _embed_texts(batch)
                all_embeddings.extend(batch_embeddings)
                print(f"  Embedded batch {i // batch_size + 1}/{(len(descriptions) - 1) // batch_size + 1}")
                break
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait = 15 * (attempt + 1)
                    print(f"  Rate limited, waiting {wait}s (attempt {attempt + 1}/5)...")
                    import time
                    time.sleep(wait)
                else:
                    raise

        # Small delay between batches to stay under rate limits
        if i + batch_size < len(descriptions):
            import time
            time.sleep(2)

    # Attach embeddings to entries
    for entry, embedding in zip(entries, all_embeddings):
        entry["embedding"] = embedding

    # Cache to disk
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(entries, f)
    print(f"[Embedder] Cached {len(entries)} embeddings to {cache_path}")

    return entries
