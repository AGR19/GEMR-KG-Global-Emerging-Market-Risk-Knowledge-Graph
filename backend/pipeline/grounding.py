"""
Grounding — Embedding-guided IRI retrieval.

Given a user's natural language question, embeds it with the same model
used for predicates, then retrieves the top-K most semantically relevant
ontology IRIs via cosine similarity.

This is the paper's "Embedding-Guided IRI Grounding" step.
"""
import numpy as np
from google import genai

from ..config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL, TOP_K_IRIS


client = genai.Client(api_key=GEMINI_API_KEY)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    dot = np.dot(a_arr, b_arr)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm == 0:
        return 0.0
    return float(dot / norm)


def embed_query(question: str) -> list[float]:
    """Embed a user question using the same model as the ontology entries."""
    import time
    for attempt in range(3):
        try:
            result = client.models.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                contents=[question],
            )
            return result.embeddings[0].values
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "503" in error_str or "UNAVAILABLE" in error_str:
                wait = 10 * (attempt + 1)
                print(f"  [Grounding] API busy/rate-limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Embedding query failed after 3 attempts")


def retrieve_relevant_iris(
    question: str,
    embedded_entries: list[dict],
    top_k: int = TOP_K_IRIS,
) -> list[dict]:
    """
    Retrieve the top-K most relevant ontology IRIs for a given question.

    Args:
        question: The user's natural language question.
        embedded_entries: List of entries from the embedder, each with an 'embedding' key.
        top_k: Number of entries to retrieve.

    Returns:
        List of top-K entries sorted by relevance (highest first), each with:
          iri, local_name, label, description, type, score
    """
    query_embedding = embed_query(question)

    # Compute similarity scores
    scored = []
    for entry in embedded_entries:
        score = _cosine_similarity(query_embedding, entry["embedding"])
        scored.append({
            "iri": entry["iri"],
            "local_name": entry["local_name"],
            "label": entry["label"],
            "description": entry["description"],
            "type": entry["type"],
            "score": round(score, 4),
        })

    # Sort by score descending, return top-K
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
