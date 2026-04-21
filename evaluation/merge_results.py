"""
Merge results from separate evaluation runs into one combined report.

Usage (from repo root):
    python -m evaluation.merge_results

Reads the two most recent JSON files from evaluation/results/ and combines them.
Or specify files explicitly:
    python -m evaluation.merge_results --files eval_results_A.json eval_results_B.json
"""

import json
import os
import argparse
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_ROOT, "backend", ".env"))

from evaluation.metrics import compute_summary
from evaluation.report import save_results, print_summary_table, print_question_detail


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_latest_files(results_dir: str, n: int = 3) -> list[str]:
    files = [
        os.path.join(results_dir, f)
        for f in os.listdir(results_dir)
        if f.startswith("eval_results_") and f.endswith(".json")
    ]
    files.sort(key=os.path.getmtime, reverse=True)
    return files[:n]


def main():
    parser = argparse.ArgumentParser(description="Merge evaluation result JSONs into one combined report")
    parser.add_argument("--files", nargs="*", help="Specific JSON filenames (just the filename, not full path)")
    parser.add_argument("--results-dir", default="evaluation/results")
    args = parser.parse_args()

    results_dir = os.path.join(REPO_ROOT, args.results_dir)

    if args.files:
        paths = [os.path.join(results_dir, f) for f in args.files]
    else:
        paths = find_latest_files(results_dir, n=5)
        print(f"Auto-detected {len(paths)} result file(s):")
        for p in paths:
            print(f"  {os.path.basename(p)}")
        print()

    # Load and merge all per_question_results, deduplicate by (condition, question_id)
    seen: set[tuple] = set()
    all_metrics: list[dict] = []

    for path in paths:
        data = load_json(path)
        for row in data.get("per_question_results", []):
            key = (row["condition"], row["question_id"])
            if key not in seen:
                seen.add(key)
                all_metrics.append(row)

    conditions_found = sorted(set(m["condition"] for m in all_metrics))
    print(f"Conditions found: {conditions_found}")
    print(f"Total questions: {len(all_metrics)}\n")

    summaries = [compute_summary(all_metrics, c) for c in conditions_found]
    print_summary_table(summaries)
    print_question_detail(all_metrics)
    save_results(all_metrics, summaries, results_dir)


if __name__ == "__main__":
    main()
