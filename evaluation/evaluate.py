"""
GEMR-KG NL→SPARQL Evaluation Harness

Usage (from repo root):
    python -m evaluation.evaluate

    # Run all 7 baselines + pipeline:
    python -m evaluation.evaluate

    # Run specific models only:
    python -m evaluation.evaluate --conditions claude_haiku gpt5 pipeline

    # Run specific questions:
    python -m evaluation.evaluate --question-ids S01 M03 C01

Available conditions:
    claude_haiku   → anthropic/claude-haiku-4.5
    claude_sonnet  → anthropic/claude-sonnet-4.6
    claude_opus    → anthropic/claude-opus-4.6
    gemma_26b      → google/gemma-4-26b-a4b-it
    gemma_31b      → google/gemma-4-31b-it
    gpt5           → openai/gpt-5
    gpt5_mini      → openai/gpt-5-mini
    pipeline       → Gemini 2.0 Flash + IRI Grounding + Self-Healing

Required in backend/.env:
    OPENROUTER_API_KEY  for all models
    GRAPHDB_URL / GRAPHDB_REPO  for SPARQL execution

Metrics (paper-aligned):
    OSR  = Ontology Structure Adherence  (query parses + executes)
    FASR = First-Attempt Success Rate    (no self-healing needed)
    ACA  = Average Correction Attempts   (avg retries)
    AA   = Answer Accuracy               (results match gold-standard)
"""

import argparse
import json
import sys
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_ROOT, "backend", ".env"))

from evaluation.questions import TEST_QUESTIONS
from evaluation.baseline_evaluator import evaluate_baseline_question, MODEL_REGISTRY, ALL_BASELINE_CONDITIONS
from evaluation.metrics import compute_question_metrics, compute_summary, run_reference_query
from evaluation.report import save_results, print_summary_table, print_question_detail
from evaluation.split import filter_questions, DEV_IDS, TEST_IDS

# Pipeline imports are lazy — only loaded if "pipeline" condition is used
# This avoids requiring google.genai for baseline-only evaluation runs
_pipeline_initialized = False

def _lazy_import_pipeline():
    global initialize_pipeline, evaluate_pipeline_question
    from evaluation.pipeline_evaluator import initialize_pipeline, evaluate_pipeline_question

ALL_CONDITIONS = ALL_BASELINE_CONDITIONS + ["pipeline"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GEMR-KG NL→SPARQL Evaluation Harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(
            f"  {name:16s} → {model_id}"
            for name, model_id in MODEL_REGISTRY.items()
        ) + "\n  pipeline         → Gemini 2.0 Flash + IRI Grounding + Self-Healing",
    )
    parser.add_argument(
        "--conditions", nargs="+", choices=ALL_CONDITIONS, default=ALL_CONDITIONS,
        help="Which conditions to evaluate (default: all 8)",
    )
    parser.add_argument(
        "--question-ids", nargs="*",
        help="Run only specific question IDs e.g. S01 M03 C01",
    )
    parser.add_argument(
        "--split", choices=["dev", "test", "all"], default="all",
        help="Frozen seed=42 split. 'dev' = tuning fold, 'test' = held-out (default: all)",
    )
    parser.add_argument(
        "--delay", type=float, default=2.0,
        help="Seconds to sleep between questions (rate limit buffer, default 2.0)",
    )
    parser.add_argument(
        "--output-dir", default="evaluation/results",
        help="Directory for JSON output (default: evaluation/results)",
    )
    parser.add_argument(
        "--max-parallel-conditions", type=int, default=7,
        help="How many baseline conditions to run concurrently (default 7)."
             " Pipeline always runs serially after baselines."
             " Set to 1 for fully sequential.",
    )
    return parser.parse_args()


def _banner(title: str, n: int) -> None:
    print("\n" + "=" * 68)
    print(f"  {title}  —  {n} questions")
    print("=" * 68)


def _status_symbol(metrics: dict) -> str:
    if metrics["answer_accurate"]:
        return "AA✓"
    if metrics["execution_success"]:
        return "EMPTY" if metrics["empty_result"] else "WRONG"
    if metrics["syntactically_valid"]:
        return "EXEC-ERR"
    return "BAD-SPARQL"


# Serializes writes/prints across threads so baselines can run in parallel
# without interleaving log output.
_metrics_lock = threading.Lock()
_print_lock = threading.Lock()


def _log(line: str) -> None:
    with _print_lock:
        print(line, flush=True)


def _run_condition(
    condition: str,
    questions: list,
    reference_cache: dict,
    all_metrics: list,
    delay: float,
    on_condition_done=None,
) -> None:
    """Run all questions for one condition and append metrics thread-safely."""
    if condition == "pipeline":
        label = "FULL PIPELINE  Gemini + Grounding + Self-Healing"
    else:
        model_id = MODEL_REGISTRY[condition]
        label = f"BASELINE  {condition}  ({model_id})"

    _log("\n" + "=" * 68)
    _log(f"  {label}  —  {len(questions)} questions")
    _log("=" * 68)

    for i, q in enumerate(questions, 1):
        if condition == "pipeline":
            raw = evaluate_pipeline_question(q.question)
        else:
            raw = evaluate_baseline_question(q.question, condition=condition)

        metrics = compute_question_metrics(
            q, raw, condition=condition,
            reference_data=reference_cache.get(q.id),
        )
        with _metrics_lock:
            all_metrics.append(metrics)
        sym = _status_symbol(metrics)
        h = f"  halluc={metrics['hallucination_count']}" if metrics["hallucination_count"] else ""
        match = f"  match={metrics['match_type']}" if metrics["execution_success"] and not metrics["empty_result"] else ""
        _log(f"[{condition}] [{i}/{len(questions)}] {q.id} ({q.tier}) → {sym}{match}{h}  ({metrics['elapsed_seconds']}s)")

        if i < len(questions) and delay > 0:
            time.sleep(delay)

    _log(f"[{condition}] ✓ finished all {len(questions)} questions")
    if on_condition_done:
        on_condition_done(condition)


def main() -> None:
    args = parse_args()

    questions = TEST_QUESTIONS
    if args.question_ids:
        ids = set(args.question_ids)
        questions = [q for q in questions if q.id in ids]
        if not questions:
            print(f"[Error] No questions matched: {args.question_ids}")
            sys.exit(1)
    else:
        questions = filter_questions(questions, args.split)
        print(f"  Split: {args.split}  (DEV={len(DEV_IDS)}, TEST={len(TEST_IDS)})")

    # ── Print run configuration ──────────────────────────────────────────────
    print("\n" + "=" * 68)
    print("  GEMR-KG NL→SPARQL EVALUATION")
    print("=" * 68)
    print(f"  Questions: {len(questions)}")
    print(f"  Conditions: {', '.join(args.conditions)}")
    for c in args.conditions:
        if c in MODEL_REGISTRY:
            print(f"    {c:16s} → {MODEL_REGISTRY[c]}")
        else:
            print(f"    {c:16s} → Gemini 2.0 Flash + IRI Grounding + Self-Healing")

    # ── Pre-fetch gold-standard reference results ────────────────────────────
    _banner("Running Gold-Standard Reference Queries", len(questions))
    reference_cache: dict[str, dict | None] = {}
    for i, q in enumerate(questions, 1):
        ref_data = run_reference_query(q)
        ref_rows = len(ref_data.get("results", {}).get("bindings", [])) if ref_data else 0
        reference_cache[q.id] = ref_data
        status = f"✓ {ref_rows} rows" if ref_data else "✗ no reference"
        print(f"  [{i}/{len(questions)}] {q.id}: {status}")
    n_ok = sum(1 for v in reference_cache.values() if v)
    print(f"\n  Reference queries: {n_ok}/{len(questions)} succeeded")

    all_metrics: list[dict] = []

    # ── Initialize pipeline if needed ────────────────────────────────────────
    if "pipeline" in args.conditions:
        _lazy_import_pipeline()
        _banner("Initialising Pipeline", 0)
        initialize_pipeline()

    # ── Partial-snapshot helper (survives a mid-sweep kill) ─────────────────
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(args.output_dir, exist_ok=True)
    partial_path = os.path.join(args.output_dir, f"eval_results_{run_ts}.partial.json")

    def _snapshot(reason: str) -> None:
        with _metrics_lock:
            snap_metrics = list(all_metrics)
        done = sorted({m["condition"] for m in snap_metrics})
        summaries_partial = [compute_summary(snap_metrics, c) for c in done]
        with open(partial_path, "w", encoding="utf-8") as f:
            json.dump(
                {"run_timestamp": run_ts, "partial": True,
                 "summaries": summaries_partial,
                 "per_question_results": snap_metrics},
                f, indent=2, default=str,
            )
        _log(f"[snapshot] {reason}: {len(snap_metrics)} rows across {len(done)} conditions → {partial_path}")

    # ── Run baselines in parallel, pipeline serial after ────────────────────
    baseline_conditions = [c for c in args.conditions if c != "pipeline"]
    pipeline_requested = "pipeline" in args.conditions

    if baseline_conditions:
        _log(f"\n  Running {len(baseline_conditions)} baselines in parallel "
             f"(max_workers={min(args.max_parallel_conditions, len(baseline_conditions))})")
        with ThreadPoolExecutor(max_workers=min(args.max_parallel_conditions, len(baseline_conditions))) as pool:
            futures = [
                pool.submit(_run_condition, c, questions, reference_cache,
                            all_metrics, args.delay,
                            lambda cond: _snapshot(f"{cond} done"))
                for c in baseline_conditions
            ]
            for f in futures:
                try:
                    f.result()
                except Exception as e:
                    _log(f"[ERROR] baseline thread raised: {e}")

    if pipeline_requested:
        _run_condition("pipeline", questions, reference_cache,
                       all_metrics, args.delay,
                       lambda cond: _snapshot(f"{cond} done"))

    # ── Output ───────────────────────────────────────────────────────────────
    active_conditions = [c for c in args.conditions if any(m["condition"] == c for m in all_metrics)]
    summaries = [compute_summary(all_metrics, c) for c in active_conditions]
    print_summary_table(summaries)
    print_question_detail(all_metrics)
    save_results(all_metrics, summaries, args.output_dir)
    # Clean up the .partial snapshot once the final file is written
    try:
        os.remove(partial_path)
    except OSError:
        pass


if __name__ == "__main__":
    main()
