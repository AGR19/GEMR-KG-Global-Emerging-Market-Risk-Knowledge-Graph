"""
Self-Healer — Executes SPARQL against GraphDB and retries on failure.

Implements the paper's "Self-Healing Refinement Loop":
  1. Execute the generated SPARQL against GraphDB
  2. If it succeeds → return results
  3. If it fails → compress the error, build a repair prompt, call the LLM again
  4. Repeat up to MAX_HEAL_ATTEMPTS times
"""
import requests

from ..config import SPARQL_ENDPOINT, MAX_HEAL_ATTEMPTS
from .prompt_builder import build_repair_prompt
from .sparql_generator import generate_sparql


def execute_sparql(sparql: str) -> dict:
    """
    Execute a SPARQL query against GraphDB.

    Returns:
        {
            "success": bool,
            "data": {...} or None,     # SPARQL results JSON on success
            "error": str or None,       # Error message on failure
            "status_code": int,
        }
    """
    try:
        response = requests.get(
            SPARQL_ENDPOINT,
            params={"query": sparql},
            headers={"Accept": "application/sparql-results+json"},
            timeout=30,
        )

        if response.ok:
            data = response.json()
            return {
                "success": True,
                "data": data,
                "error": None,
                "status_code": response.status_code,
            }
        else:
            # Extract meaningful error from GraphDB response
            error_text = response.text[:500]  # Compress to first 500 chars
            return {
                "success": False,
                "data": None,
                "error": f"HTTP {response.status_code}: {error_text}",
                "status_code": response.status_code,
            }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "data": None,
            "error": "Could not connect to GraphDB. Is the Docker container running on port 7200?",
            "status_code": 0,
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "data": None,
            "error": "GraphDB query timed out after 30 seconds.",
            "status_code": 408,
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Unexpected error: {str(e)}",
            "status_code": 0,
        }


def heal_and_execute(
    question: str,
    initial_sparql: str,
    system_prompt: str,
    grounded_iris: list[dict],
    model_key: str | None = None,
) -> dict:
    """
    Execute SPARQL with self-healing retry loop.

    Args:
        question: Original user question.
        initial_sparql: The first SPARQL attempt.
        system_prompt: The static system prompt for repair calls.
        grounded_iris: The grounded IRIs for context in repair prompts.

    Returns:
        {
            "success": bool,
            "sparql": str,              # The final (possibly repaired) SPARQL
            "data": {...} or None,
            "attempts": int,            # How many attempts it took
            "history": [                # Log of all attempts
                {"attempt": 1, "sparql": "...", "success": bool, "error": "..."},
                ...
            ]
        }
    """
    current_sparql = initial_sparql
    history = []

    for attempt in range(1, MAX_HEAL_ATTEMPTS + 1):
        print(f"  [Self-Healer] Attempt {attempt}/{MAX_HEAL_ATTEMPTS}...")

        result = execute_sparql(current_sparql)

        history.append({
            "attempt": attempt,
            "sparql": current_sparql,
            "success": result["success"],
            "error": result["error"],
        })

        if result["success"]:
            # Check for empty results — might be using the wrong IRI
            bindings = result["data"].get("results", {}).get("bindings", [])

            if len(bindings) > 0:
                # Real success with data
                print(f"  [Self-Healer] ✓ Success on attempt {attempt} ({len(bindings)} results)")
                return {
                    "success": True,
                    "sparql": current_sparql,
                    "data": result["data"],
                    "attempts": attempt,
                    "history": history,
                }

            # Empty results — treat as soft failure and retry
            if attempt < MAX_HEAL_ATTEMPTS:
                print(f"  [Self-Healer] ⚠ Query succeeded but returned 0 results, attempting repair...")
                # Build a specific error message for empty results
                iri_hints = ", ".join(f"gemr:{g['local_name']}" for g in grounded_iris[:10])
                empty_error = (
                    f"The query executed successfully but returned ZERO results. "
                    f"This usually means the indicator IRI is wrong. "
                    f"The available IRIs for this question are: {iri_hints}. "
                    f"Use the EXACT indicator IRI from this list, not a generic one like gemr:GDP."
                )
                history[-1]["error"] = empty_error
                history[-1]["success"] = False

                repair_prompt = build_repair_prompt(
                    question=question,
                    failed_sparql=current_sparql,
                    error_message=empty_error,
                    grounded_iris=grounded_iris,
                )
                current_sparql = generate_sparql(system_prompt, repair_prompt, model_key=model_key)
                print(f"  [Self-Healer]   Generated repaired query")
                continue
            else:
                # Last attempt, return empty results as-is
                print(f"  [Self-Healer] ✓ Query valid but 0 results on final attempt")
                return {
                    "success": True,
                    "sparql": current_sparql,
                    "data": result["data"],
                    "attempts": attempt,
                    "history": history,
                }

        # Connection errors shouldn't trigger repair — the query might be fine
        if result["status_code"] == 0:
            print(f"  [Self-Healer] ✗ Infrastructure error, skipping repair: {result['error']}")
            return {
                "success": False,
                "sparql": current_sparql,
                "data": None,
                "attempts": attempt,
                "history": history,
            }

        # Query error — attempt repair
        if attempt < MAX_HEAL_ATTEMPTS:
            print(f"  [Self-Healer] ✗ Query failed, attempting repair...")
            repair_prompt = build_repair_prompt(
                question=question,
                failed_sparql=current_sparql,
                error_message=result["error"],
                grounded_iris=grounded_iris,
            )
            current_sparql = generate_sparql(system_prompt, repair_prompt, model_key=model_key)
            print(f"  [Self-Healer]   Generated repaired query")

    # All attempts exhausted
    print(f"  [Self-Healer] ✗ All {MAX_HEAL_ATTEMPTS} attempts failed")
    return {
        "success": False,
        "sparql": current_sparql,
        "data": None,
        "attempts": MAX_HEAL_ATTEMPTS,
        "history": history,
    }
