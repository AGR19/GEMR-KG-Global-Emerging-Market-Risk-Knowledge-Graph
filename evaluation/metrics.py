from evaluation.sparql_utils import (
    is_syntactically_valid, count_hallucinations,
    get_result_count, compare_results, execute_sparql,
)
from evaluation.questions import TestQuestion


def run_reference_query(question: TestQuestion, max_retries: int = 3) -> dict | None:
    """Execute the gold-standard reference SPARQL and return the result data.

    Returns the raw SPARQL JSON data dict on success, or None on failure.
    Retries transient failures up to max_retries times with exponential backoff
    — a failed reference silently poisons AA for every condition on that question.
    """
    import time
    if not question.reference_sparql.strip():
        return None

    last_err: str | None = None
    for attempt in range(max_retries):
        result = execute_sparql(question.reference_sparql)
        if result.get("success"):
            data = result.get("data")
            # Guard: GraphDB can return 200 OK with an empty/invalid body under load
            if data and isinstance(data, dict) and "results" in data:
                return data
            last_err = f"success=True but data malformed: {str(data)[:120]}"
        else:
            last_err = result.get("error") or "unknown"

        if attempt < max_retries - 1:
            time.sleep(1.0 * (attempt + 1))  # 1s, 2s, 3s

    print(f"  [reference] {question.id} failed after {max_retries} tries: {last_err[:120]}")
    return None


def compute_question_metrics(
    question: TestQuestion,
    raw_result: dict,
    condition: str,
    reference_data: dict | None = None,
) -> dict:
    """
    Derive all per-question metrics from a raw evaluator result dict.

    Metrics align with Arvind's thesis terminology:
      - OSR  (Ontology Structure Adherence) → syntactically_valid + execution_success
      - FASR (First-Attempt Success Rate)   → derived from attempts == 1
      - ACA  (Average Correction Attempts)  → attempts
      - AA   (Answer Accuracy)              → answer_accurate (compared to reference)

    Args:
        question:       TestQuestion metadata (includes reference_sparql).
        raw_result:     Dict from evaluate_baseline_question() or evaluate_pipeline_question().
        condition:      "gpt4o", "claude", or "pipeline".
        reference_data: Pre-fetched reference query results (avoids re-querying per condition).
    """
    sparql = raw_result.get("sparql", "")
    execution = raw_result.get("execution", {})

    syntactically_valid = is_syntactically_valid(sparql)
    execution_success = bool(execution.get("success", False))
    result_count = get_result_count(execution)
    empty_result = execution_success and result_count == 0
    hallucination_count = count_hallucinations(sparql)

    # First-attempt success (pipeline only — baselines are always 1 attempt)
    attempts = raw_result.get("attempts", 1)
    first_attempt_success = execution_success and attempts == 1

    # Answer Accuracy — compare generated results to gold-standard reference
    generated_data = execution.get("data") if execution_success else None
    aa_result = compare_results(generated_data, reference_data)

    return {
        # Identity
        "condition": condition,
        "question_id": question.id,
        "tier": question.tier,
        "category": question.category,
        "result_type": question.result_type,
        "question": question.question,

        # Paper metrics (thesis-aligned names)
        "osr": syntactically_valid and execution_success,      # Ontology Structure Adherence
        "first_attempt_success": first_attempt_success,         # FASR
        "attempts": attempts,                                    # ACA
        "answer_accurate": aa_result["answer_accurate"],         # AA
        "match_type": aa_result["match_type"],
        "precision": aa_result["precision"],
        "recall": aa_result["recall"],
        "ref_row_count": aa_result["ref_row_count"],
        "gen_row_count": aa_result["gen_row_count"],

        # Legacy metrics (kept for backwards compatibility)
        "syntactically_valid": syntactically_valid,
        "execution_success": execution_success,
        "empty_result": empty_result,
        "result_count": result_count,
        "hallucination_count": hallucination_count,
        "elapsed_seconds": raw_result.get("elapsed_seconds", 0.0),

        # Debug data
        "sparql": sparql,
        "error": execution.get("error"),
        "initial_sparql": raw_result.get("initial_sparql"),
        "grounded_iris": raw_result.get("grounded_iris"),
    }


def compute_summary(all_metrics: list[dict], condition: str) -> dict:
    """Aggregate per-question metrics into a summary for one condition.

    Uses paper-aligned metric names:
      OSR  = Ontology Structure Adherence (valid + executable)
      FASR = First-Attempt Success Rate
      ACA  = Average Correction Attempts
      AA   = Answer Accuracy (matches gold-standard reference)
    """
    rows = [m for m in all_metrics if m["condition"] == condition]
    n = len(rows)
    if n == 0:
        return {}

    n_osr = sum(1 for r in rows if r["osr"])
    n_fasr = sum(1 for r in rows if r["first_attempt_success"])
    n_aa = sum(1 for r in rows if r["answer_accurate"])
    n_empty = sum(1 for r in rows if r["empty_result"])
    total_hallucinations = sum(r["hallucination_count"] for r in rows)
    avg_attempts = sum(r["attempts"] for r in rows) / n
    avg_elapsed = sum(r["elapsed_seconds"] for r in rows) / n

    tier_breakdown: dict[str, dict] = {}
    for tier in ("simple", "medium", "complex"):
        tr = [r for r in rows if r["tier"] == tier]
        if not tr:
            continue
        tn = len(tr)
        tier_breakdown[tier] = {
            "n": tn,
            "osr_pct": round(100 * sum(1 for r in tr if r["osr"]) / tn, 1),
            "fasr_pct": round(100 * sum(1 for r in tr if r["first_attempt_success"]) / tn, 1),
            "aa_pct": round(100 * sum(1 for r in tr if r["answer_accurate"]) / tn, 1),
            "empty_pct": round(100 * sum(1 for r in tr if r["empty_result"]) / tn, 1),
        }

    # Category breakdown
    categories = sorted({r["category"] for r in rows if r.get("category")})
    category_breakdown: dict[str, dict] = {}
    for cat in categories:
        cr = [r for r in rows if r.get("category") == cat]
        cn = len(cr)
        category_breakdown[cat] = {
            "n": cn,
            "osr_pct": round(100 * sum(1 for r in cr if r["osr"]) / cn, 1),
            "aa_pct": round(100 * sum(1 for r in cr if r["answer_accurate"]) / cn, 1),
        }

    osr_pct = round(100 * n_osr / n, 1)
    fasr_pct = round(100 * n_fasr / n, 1)

    return {
        "condition": condition,
        "n": n,
        "osr_pct": osr_pct,
        "fasr_pct": fasr_pct,
        "err_pct": round(osr_pct - fasr_pct, 1),      # Error Recovery Rate
        "aa_pct": round(100 * n_aa / n, 1),
        "empty_result_rate_pct": round(100 * n_empty / n, 1),
        "hallucination_total": total_hallucinations,
        "avg_attempts": round(avg_attempts, 2),
        "avg_elapsed_seconds": round(avg_elapsed, 2),
        "tier_breakdown": tier_breakdown,
        "category_breakdown": category_breakdown,
    }
