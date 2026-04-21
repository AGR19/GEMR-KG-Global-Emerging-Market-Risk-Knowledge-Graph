from evaluation.sparql_utils import is_syntactically_valid, count_hallucinations, get_result_count
from evaluation.questions import TestQuestion


def compute_question_metrics(
    question: TestQuestion,
    raw_result: dict,
    condition: str,
) -> dict:
    """
    Derive all per-question metrics from a raw evaluator result dict.

    Args:
        question:   TestQuestion metadata.
        raw_result: Dict from evaluate_baseline_question() or evaluate_pipeline_question().
        condition:  "gpt4o", "claude", or "pipeline".
    """
    sparql = raw_result.get("sparql", "")
    execution = raw_result.get("execution", {})

    syntactically_valid = is_syntactically_valid(sparql)
    execution_success = bool(execution.get("success", False))
    result_count = get_result_count(execution)
    empty_result = execution_success and result_count == 0
    hallucination_count = count_hallucinations(sparql)

    return {
        "condition": condition,
        "question_id": question.id,
        "tier": question.tier,
        "result_type": question.result_type,
        "question": question.question,
        "syntactically_valid": syntactically_valid,
        "execution_success": execution_success,
        "empty_result": empty_result,
        "result_count": result_count,
        "hallucination_count": hallucination_count,
        "attempts": raw_result.get("attempts", 1),
        "elapsed_seconds": raw_result.get("elapsed_seconds", 0.0),
        "sparql": sparql,
        "error": execution.get("error"),
        "initial_sparql": raw_result.get("initial_sparql"),
        "grounded_iris": raw_result.get("grounded_iris"),
    }


def compute_summary(all_metrics: list[dict], condition: str) -> dict:
    """Aggregate per-question metrics into a summary for one condition."""
    rows = [m for m in all_metrics if m["condition"] == condition]
    n = len(rows)
    if n == 0:
        return {}

    n_valid = sum(1 for r in rows if r["syntactically_valid"])
    n_exec = sum(1 for r in rows if r["execution_success"])
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
            "syntactic_validity_pct": round(100 * sum(1 for r in tr if r["syntactically_valid"]) / tn, 1),
            "execution_accuracy_pct": round(100 * sum(1 for r in tr if r["execution_success"]) / tn, 1),
            "empty_result_rate_pct": round(100 * sum(1 for r in tr if r["empty_result"]) / tn, 1),
        }

    return {
        "condition": condition,
        "n": n,
        "syntactic_validity_pct": round(100 * n_valid / n, 1),
        "execution_accuracy_pct": round(100 * n_exec / n, 1),
        "empty_result_rate_pct": round(100 * n_empty / n, 1),
        "hallucination_total": total_hallucinations,
        "avg_attempts": round(avg_attempts, 2),
        "avg_elapsed_seconds": round(avg_elapsed, 2),
        "tier_breakdown": tier_breakdown,
    }
