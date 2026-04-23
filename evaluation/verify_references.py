"""
Verify that every reference_sparql in questions.py executes successfully and
returns non-empty results. Prints a report of which questions are answerable
against the current KG vs. which are broken (HTTP error) or unanswerable
(empty result set).

Usage:
    python -m evaluation.verify_references
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_ROOT, "backend", ".env"))

from evaluation.questions import TEST_QUESTIONS
from evaluation.sparql_utils import execute_sparql, get_result_count


def main() -> None:
    print(f"Verifying {len(TEST_QUESTIONS)} reference SPARQL queries against GraphDB...\n")

    ok_nonempty = []
    ok_empty = []
    broken = []

    for q in TEST_QUESTIONS:
        if not q.reference_sparql.strip():
            print(f"  {q.id:5s} [{q.tier:7s}] — NO REFERENCE SPARQL")
            broken.append((q.id, "no reference"))
            continue

        result = execute_sparql(q.reference_sparql)
        if not result.get("success"):
            err = result.get("error", "?")[:120]
            print(f"  {q.id:5s} [{q.tier:7s}] ✗ ERROR  {err}")
            broken.append((q.id, err))
            continue

        n = get_result_count(result)
        if n == 0:
            print(f"  {q.id:5s} [{q.tier:7s}] ⚠ EMPTY  — {q.question[:70]}")
            ok_empty.append(q.id)
        else:
            print(f"  {q.id:5s} [{q.tier:7s}] ✓ {n:4d} rows")
            ok_nonempty.append(q.id)

    print()
    print("═" * 68)
    print(f"  ANSWERABLE (non-empty): {len(ok_nonempty):2d} / {len(TEST_QUESTIONS)}")
    print(f"  EXECUTABLE but empty:   {len(ok_empty):2d} / {len(TEST_QUESTIONS)}  {ok_empty}")
    print(f"  BROKEN (exec error):    {len(broken):2d} / {len(TEST_QUESTIONS)}")
    for qid, err in broken:
        print(f"    {qid}: {err[:100]}")
    print("═" * 68)


if __name__ == "__main__":
    main()
