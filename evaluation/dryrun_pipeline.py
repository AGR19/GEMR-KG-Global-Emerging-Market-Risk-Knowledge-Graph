"""
Pipeline-only dry run across the full benchmark. Reports OSR, FASR, ACA, AA
for the pipeline condition alone so we can validate fixes before burning
OpenRouter credits on the full 8-condition sweep.

Usage:
    python -m evaluation.dryrun_pipeline                      # all questions
    python -m evaluation.dryrun_pipeline --split dev          # dev fold only
    python -m evaluation.dryrun_pipeline --split test         # held-out test fold
    python -m evaluation.dryrun_pipeline S01 S02 M01          # specific ids

The dev/test split (see evaluation/split.py) exists so prompt tuning only
reacts to DEV failures; the TEST fold stays unseen until the final sweep.
"""
import argparse
import os
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_ROOT, "backend", ".env"))

from evaluation.questions import TEST_QUESTIONS
from evaluation.metrics import compute_question_metrics, compute_summary, run_reference_query
from evaluation.pipeline_evaluator import initialize_pipeline, evaluate_pipeline_question
from evaluation.split import filter_questions, DEV_IDS, TEST_IDS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "test", "all"], default="all")
    parser.add_argument("ids", nargs="*", help="Explicit question IDs (overrides --split)")
    args = parser.parse_args()

    if args.ids:
        wanted = set(args.ids)
        questions = [q for q in TEST_QUESTIONS if q.id in wanted]
    else:
        questions = filter_questions(TEST_QUESTIONS, args.split)
        print(f"[split={args.split}] DEV={len(DEV_IDS)} TEST={len(TEST_IDS)} -> running {len(questions)}")

    print(f"Dry-running pipeline on {len(questions)} questions\n")

    initialize_pipeline()

    print("\n── Running reference queries ──")
    ref_cache = {}
    for q in questions:
        rd = run_reference_query(q)
        n = len(rd.get("results", {}).get("bindings", [])) if rd else 0
        ref_cache[q.id] = rd
        print(f"  {q.id}: {'✓' if rd else '✗'} ({n} rows)")

    print("\n── Running pipeline ──")
    all_metrics = []
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] {q.id} ({q.tier}): {q.question[:80]}")
        try:
            raw = evaluate_pipeline_question(q.question)
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            continue

        m = compute_question_metrics(q, raw, condition="pipeline",
                                     reference_data=ref_cache.get(q.id))
        all_metrics.append(m)

        sym = "AA✓" if m["answer_accurate"] else (
            "WRONG" if m["execution_success"] and not m["empty_result"] else
            "EMPTY" if m["execution_success"] else
            "EXEC-ERR" if m["syntactically_valid"] else "BAD-SPARQL"
        )
        print(f"  → {sym}  attempts={m['attempts']}  "
              f"match={m.get('match_type','-')}  "
              f"halluc={m['hallucination_count']}  "
              f"time={m['elapsed_seconds']}s")

        # Show SPARQL + error for failures so we can diagnose
        if not m["answer_accurate"]:
            print(f"  — ref_rows={m['ref_row_count']}, gen_rows={m['gen_row_count']}")
            if m.get("error"):
                print(f"  — error: {str(m['error'])[:180]}")
            print(f"  — SPARQL:")
            for line in (m.get("sparql") or "").splitlines()[:20]:
                print(f"      {line}")

        # Small pause to avoid rate limits
        if i < len(questions):
            time.sleep(2)

    summary = compute_summary(all_metrics, "pipeline")
    print("\n" + "═" * 68)
    print("  PIPELINE DRY-RUN SUMMARY")
    print("═" * 68)
    print(f"  N          : {summary['n']}")
    print(f"  OSR        : {summary['osr_pct']}%  (query parses + executes)")
    print(f"  FASR       : {summary['fasr_pct']}%  (success on attempt 1)")
    print(f"  ERR        : {summary.get('err_pct','-')}%  (self-healing benefit)")
    print(f"  ACA        : {summary['avg_attempts']}  (avg correction attempts)")
    print(f"  AA         : {summary['aa_pct']}%  (matches reference)")
    print(f"  Empty %    : {summary['empty_result_rate_pct']}%")
    print(f"  Halluc.    : {summary['hallucination_total']} total IRIs hallucinated")
    print(f"  Avg time   : {summary['avg_elapsed_seconds']}s")
    print()
    print("  Per tier:")
    for tier, stats in summary.get("tier_breakdown", {}).items():
        print(f"    {tier:8s} n={stats['n']:2d}  "
              f"OSR={stats['osr_pct']:5.1f}%  "
              f"FASR={stats['fasr_pct']:5.1f}%  "
              f"AA={stats['aa_pct']:5.1f}%  "
              f"empty={stats['empty_pct']:5.1f}%")
    print("═" * 68)

    # Per-question table
    print("\n── Per-question detail ──")
    for m in all_metrics:
        sym = "AA✓" if m["answer_accurate"] else (
            "WRONG" if m["execution_success"] and not m["empty_result"] else
            "EMPTY" if m["execution_success"] else
            "EXEC-ERR" if m["syntactically_valid"] else "BAD-SPARQL"
        )
        print(f"  {m['question_id']:4s} [{m['tier']:7s}] "
              f"{sym:10s} att={m['attempts']} "
              f"ref={m['ref_row_count']:3d} gen={m['gen_row_count']:3d}")


if __name__ == "__main__":
    main()
