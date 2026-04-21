import json
import os
from datetime import datetime


def save_results(all_metrics: list[dict], summaries: list[dict], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"eval_results_{timestamp}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"run_timestamp": timestamp, "summaries": summaries, "per_question_results": all_metrics},
            f,
            indent=2,
            default=str,
        )

    print(f"\n[Report] Results saved → {path}")
    return path


def print_summary_table(summaries: list[dict]) -> None:
    try:
        from tabulate import tabulate
        _has_tabulate = True
    except ImportError:
        _has_tabulate = False

    headers = ["Condition", "Syntactic %", "Exec Acc %", "Empty %", "Hallucinations", "Avg Attempts", "Avg Time(s)"]
    rows = [
        [
            s["condition"].upper(),
            f"{s['syntactic_validity_pct']}%",
            f"{s['execution_accuracy_pct']}%",
            f"{s['empty_result_rate_pct']}%",
            s["hallucination_total"],
            s["avg_attempts"],
            s["avg_elapsed_seconds"],
        ]
        for s in summaries
    ]

    print("\n" + "=" * 72)
    print("  GEMR-KG  NL→SPARQL  EVALUATION  SUMMARY")
    print("=" * 72)
    if _has_tabulate:
        print(tabulate(rows, headers=headers, tablefmt="github"))
    else:
        print("  " + " | ".join(f"{h:15s}" for h in headers))
        print("  " + "-" * 70)
        for row in rows:
            print("  " + " | ".join(f"{str(c):15s}" for c in row))

    print("\n── Per-Tier Breakdown ──\n")
    for s in summaries:
        print(f"  [{s['condition'].upper()}]")
        for tier, stats in s.get("tier_breakdown", {}).items():
            print(
                f"    {tier:8s}: n={stats['n']:2d}  "
                f"syntax={stats['syntactic_validity_pct']:5.1f}%  "
                f"exec={stats['execution_accuracy_pct']:5.1f}%  "
                f"empty={stats['empty_result_rate_pct']:5.1f}%"
            )
        print()


def print_question_detail(all_metrics: list[dict]) -> None:
    print("── Per-Question Detail ──\n")

    by_qid: dict[str, dict] = {}
    for m in all_metrics:
        qid = m["question_id"]
        if qid not in by_qid:
            by_qid[qid] = {}
        by_qid[qid][m["condition"]] = m

    def fmt(m: dict | None) -> str:
        if m is None:
            return "N/A"
        if m["execution_success"]:
            sym = "OK" + (" EMPTY" if m["empty_result"] else "")
        elif m["syntactically_valid"]:
            sym = "PARSE-ERR"
        else:
            sym = "BAD-SPARQL"
        h = f" H={m['hallucination_count']}" if m["hallucination_count"] else ""
        return f"{sym}{h} ({m['elapsed_seconds']}s)"

    conditions = list({m["condition"] for m in all_metrics})
    header = f"{'QID':5s} {'Tier':8s} " + " ".join(f"{c.upper():20s}" for c in sorted(conditions))
    print("  " + header)
    print("  " + "-" * len(header))

    for qid in sorted(by_qid.keys()):
        entries = by_qid[qid]
        tier = next(iter(entries.values()))["tier"]
        cols = " ".join(f"{fmt(entries.get(c)):20s}" for c in sorted(conditions))
        print(f"  {qid:5s} {tier:8s} {cols}")
