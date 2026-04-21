"""
GEMR-KG NL→SPARQL Evaluation Harness

Usage (from repo root):
    python -m evaluation.evaluate

Options:
    --conditions gpt4o claude pipeline   (default: all 3)
    --question-ids S01 M03 C01           (run a subset)
    --delay 2.0                          (seconds between questions, default 2.0)
    --output-dir evaluation/results      (default)

Required in backend/.env:
    GEMINI_API_KEY      for pipeline
    OPENAI_API_KEY      for gpt4o baseline
    OPENROUTER_API_KEY  for claude baseline
    GRAPHDB_URL / GRAPHDB_REPO  for SPARQL execution
"""

import argparse
import sys
import os
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_ROOT, "backend", ".env"))

from evaluation.questions import TEST_QUESTIONS
from evaluation.baseline_evaluator import evaluate_baseline_question
from evaluation.pipeline_evaluator import initialize_pipeline, evaluate_pipeline_question
from evaluation.metrics import compute_question_metrics, compute_summary
from evaluation.report import save_results, print_summary_table, print_question_detail

ALL_CONDITIONS = ["gpt4o", "claude", "pipeline"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GEMR-KG NL→SPARQL Evaluation Harness")
    parser.add_argument(
        "--conditions", nargs="+", choices=ALL_CONDITIONS, default=ALL_CONDITIONS,
        help="Which conditions to evaluate (default: all 3)",
    )
    parser.add_argument(
        "--question-ids", nargs="*",
        help="Run only specific question IDs e.g. S01 M03 C01",
    )
    parser.add_argument(
        "--delay", type=float, default=2.0,
        help="Seconds to sleep between questions (rate limit buffer, default 2.0)",
    )
    parser.add_argument(
        "--output-dir", default="evaluation/results",
        help="Directory for JSON output (default: evaluation/results)",
    )
    return parser.parse_args()


def _banner(title: str, n: int) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}  —  {n} questions")
    print("=" * 60)


def _progress(metrics: dict) -> None:
    ok = "OK" if metrics["execution_success"] else "FAIL"
    empty = " EMPTY" if metrics["empty_result"] else ""
    h = f"  hallucinations={metrics['hallucination_count']}" if metrics["hallucination_count"] else ""
    print(f"  → {ok}{empty}{h}  ({metrics['elapsed_seconds']}s)")


def main() -> None:
    args = parse_args()

    questions = TEST_QUESTIONS
    if args.question_ids:
        ids = set(args.question_ids)
        questions = [q for q in questions if q.id in ids]
        if not questions:
            print(f"[Error] No questions matched: {args.question_ids}")
            sys.exit(1)

    all_metrics: list[dict] = []
    conditions: list[str] = args.conditions

    # Initialise pipeline once if needed
    if "pipeline" in conditions:
        _banner("Initialising Pipeline", 0)
        initialize_pipeline()

    # ── Baseline: GPT-4o ────────────────────────────────────────────────────
    if "gpt4o" in conditions:
        _banner("BASELINE  GPT-4o  (no grounding)", len(questions))
        for i, q in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}] {q.id} ({q.tier}): {q.question[:75]}...")
            raw = evaluate_baseline_question(q.question, condition="gpt4o")
            metrics = compute_question_metrics(q, raw, condition="gpt4o")
            all_metrics.append(metrics)
            _progress(metrics)
            if i < len(questions) and args.delay > 0:
                time.sleep(args.delay)

    # ── Baseline: Claude ────────────────────────────────────────────────────
    if "claude" in conditions:
        _banner("BASELINE  Claude  (no grounding, via OpenRouter)", len(questions))
        for i, q in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}] {q.id} ({q.tier}): {q.question[:75]}...")
            raw = evaluate_baseline_question(q.question, condition="claude")
            metrics = compute_question_metrics(q, raw, condition="claude")
            all_metrics.append(metrics)
            _progress(metrics)
            if i < len(questions) and args.delay > 0:
                time.sleep(args.delay)

    # ── Full Pipeline ────────────────────────────────────────────────────────
    if "pipeline" in conditions:
        _banner("FULL PIPELINE  Gemini + Grounding + Self-Healing", len(questions))
        for i, q in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}] {q.id} ({q.tier}): {q.question[:75]}...")
            raw = evaluate_pipeline_question(q.question)
            metrics = compute_question_metrics(q, raw, condition="pipeline")
            all_metrics.append(metrics)
            _progress(metrics)
            if i < len(questions) and args.delay > 0:
                time.sleep(args.delay)

    # ── Output ───────────────────────────────────────────────────────────────
    summaries = [compute_summary(all_metrics, c) for c in conditions if any(m["condition"] == c for m in all_metrics)]
    print_summary_table(summaries)
    print_question_detail(all_metrics)
    save_results(all_metrics, summaries, args.output_dir)


if __name__ == "__main__":
    main()
