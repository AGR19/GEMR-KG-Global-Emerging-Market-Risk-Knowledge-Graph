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
    """Print the main summary table with paper-aligned metrics."""

    headers = [
        "Condition", "OSR %", "FASR %", "ERR %", "ACA", "AA %",
        "Empty %", "Halluc.", "Avg Time",
    ]
    rows = [
        [
            s["condition"].upper(),
            f"{s['osr_pct']}%",
            f"{s['fasr_pct']}%",
            f"{s.get('err_pct', round(s['osr_pct'] - s['fasr_pct'], 1))}%",
            s["avg_attempts"],
            f"{s['aa_pct']}%",
            f"{s['empty_result_rate_pct']}%",
            s["hallucination_total"],
            f"{s['avg_elapsed_seconds']:.1f}s",
        ]
        for s in summaries
    ]

    print("\n" + "=" * 84)
    print("  GEMR-KG  NL→SPARQL  EVALUATION  SUMMARY")
    print("  OSR = Ontology Structure Adherence  |  FASR = First-Attempt Success Rate")
    print("  ERR = Error Recovery Rate (OSR-FASR)|  ACA = Avg Correction Attempts")
    print("  AA  = Answer Accuracy (vs reference)|  Halluc. = Hallucinated IRIs")
    print("=" * 84)

    try:
        from tabulate import tabulate
        print(tabulate(rows, headers=headers, tablefmt="github"))
    except ImportError:
        print("  " + " | ".join(f"{h:10s}" for h in headers))
        print("  " + "-" * 84)
        for row in rows:
            print("  " + " | ".join(f"{str(c):10s}" for c in row))

    # ── Per-Tier Breakdown ──
    print("\n── Per-Tier Breakdown ──\n")
    for s in summaries:
        print(f"  [{s['condition'].upper()}]")
        for tier, stats in s.get("tier_breakdown", {}).items():
            print(
                f"    {tier:8s}: n={stats['n']:2d}  "
                f"OSR={stats['osr_pct']:5.1f}%  "
                f"FASR={stats['fasr_pct']:5.1f}%  "
                f"AA={stats['aa_pct']:5.1f}%  "
                f"empty={stats['empty_pct']:5.1f}%"
            )
        print()

    # ── Per-Category Breakdown ──
    has_categories = any(s.get("category_breakdown") for s in summaries)
    if has_categories:
        print("── Per-Category Breakdown ──\n")
        for s in summaries:
            cats = s.get("category_breakdown", {})
            if not cats:
                continue
            print(f"  [{s['condition'].upper()}]")
            for cat, stats in cats.items():
                print(
                    f"    {cat:18s}: n={stats['n']:2d}  "
                    f"OSR={stats['osr_pct']:5.1f}%  "
                    f"AA={stats['aa_pct']:5.1f}%"
                )
            print()


def print_question_detail(all_metrics: list[dict]) -> None:
    """Print per-question detail table with AA results."""
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
        # Status symbol
        if m["answer_accurate"]:
            sym = "AA✓"
        elif m["execution_success"]:
            sym = "EMPTY" if m["empty_result"] else f"WRONG({m['match_type']})"
        elif m["syntactically_valid"]:
            sym = "EXEC-ERR"
        else:
            sym = "BAD-SPARQL"
        h = f" H={m['hallucination_count']}" if m["hallucination_count"] else ""
        return f"{sym}{h} ({m['elapsed_seconds']}s)"

    conditions = sorted({m["condition"] for m in all_metrics})
    header = f"{'QID':5s} {'Tier':8s} {'Cat':16s} " + " ".join(f"{c.upper():22s}" for c in conditions)
    print("  " + header)
    print("  " + "-" * len(header))

    for qid in sorted(by_qid.keys()):
        entries = by_qid[qid]
        first = next(iter(entries.values()))
        tier = first["tier"]
        cat = first.get("category", "")[:14]
        cols = " ".join(f"{fmt(entries.get(c)):22s}" for c in conditions)
        print(f"  {qid:5s} {tier:8s} {cat:16s} {cols}")
