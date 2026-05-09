"""Aggregate eval results into a summary table for the academic report.

Reads:
    data/eval/runs/*.json        (agent outputs)
    data/eval/judgments/*.json   (LLM-as-judge outputs)

Writes:
    data/eval/summary.json       — aggregate metrics
    data/eval/summary.md         — markdown report (paste-ready for paper)
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, default=ROOT / "data" / "eval" / "runs")
    parser.add_argument("--judgments", type=Path, default=ROOT / "data" / "eval" / "judgments")
    parser.add_argument("--out-json", type=Path, default=ROOT / "data" / "eval" / "summary.json")
    parser.add_argument("--out-md", type=Path, default=ROOT / "data" / "eval" / "summary.md")
    args = parser.parse_args()

    if not args.runs.exists():
        print(f"[!] Runs dir missing: {args.runs}", file=sys.stderr)
        return 1

    runs = {p.stem: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(args.runs.glob("*.json"))}
    judgments = {p.stem: json.loads(p.read_text(encoding="utf-8"))
                 for p in sorted(args.judgments.glob("*.json"))} if args.judgments.exists() else {}

    rows = []
    by_category: dict[str, list[dict]] = defaultdict(list)

    for qid, run in runs.items():
        res = run.get("result")
        err = run.get("error")
        judg = judgments.get(qid, {}).get("judgment")

        row = {
            "id": qid,
            "category": run.get("category", ""),
            "type": run.get("type", ""),
            "question": run["question"][:80],
            "ok": err is None and res is not None,
            "latency_s": res["latency_seconds"] if res else None,
            "n_chunks": res["retrieval"]["n_chunks"] if res else None,
            "max_score": res["retrieval"]["max_score"] if res else None,
            "n_citations": res["final"]["n_citations"] if res and res.get("final") else None,
            "iteration_count": res.get("iteration_count", 0) if res else None,
            "citation_accuracy": judg["citation_accuracy"] if judg else None,
            "faithfulness": judg["faithfulness"] if judg else None,
            "coverage": judg["coverage"] if judg else None,
            "holistic_score": judg["holistic_score"] if judg else None,
        }
        rows.append(row)
        by_category[row["category"]].append(row)

    # Aggregate stats
    def _stats(values: list[float]) -> dict:
        nv = [v for v in values if v is not None]
        if not nv:
            return {"n": 0, "mean": None, "median": None, "min": None, "max": None}
        return {
            "n": len(nv),
            "mean": round(statistics.mean(nv), 3),
            "median": round(statistics.median(nv), 3),
            "min": round(min(nv), 3),
            "max": round(max(nv), 3),
        }

    overall = {
        "n_questions": len(rows),
        "n_ok": sum(1 for r in rows if r["ok"]),
        "n_failed": sum(1 for r in rows if not r["ok"]),
        "latency_seconds": _stats([r["latency_s"] for r in rows]),
        "n_chunks":       _stats([r["n_chunks"] for r in rows]),
        "max_score":      _stats([r["max_score"] for r in rows]),
        "n_citations":    _stats([r["n_citations"] for r in rows]),
        "citation_accuracy": _stats([r["citation_accuracy"] for r in rows]),
        "faithfulness":     _stats([r["faithfulness"] for r in rows]),
        "coverage":         _stats([r["coverage"] for r in rows]),
        "holistic_score":   _stats([r["holistic_score"] for r in rows]),
    }

    summary = {
        "overall": overall,
        "by_category": {
            cat: {
                "n": len(items),
                "citation_accuracy": _stats([r["citation_accuracy"] for r in items]),
                "faithfulness":     _stats([r["faithfulness"] for r in items]),
                "coverage":         _stats([r["coverage"] for r in items]),
                "holistic_score":   _stats([r["holistic_score"] for r in items]),
                "latency_seconds":  _stats([r["latency_s"] for r in items]),
            }
            for cat, items in by_category.items()
        },
        "rows": rows,
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] Wrote {args.out_json}")

    # Markdown report
    md = []
    md.append("# TürkResearcher — Evaluation Summary\n")
    md.append(f"- **Questions:** {overall['n_questions']} (ok: {overall['n_ok']}, failed: {overall['n_failed']})\n")
    md.append("")
    md.append("## Overall Metrics\n")
    md.append("| Metric | Mean | Median | Min | Max | n |")
    md.append("|---|---|---|---|---|---|")
    for k in ["citation_accuracy", "faithfulness", "coverage", "holistic_score",
              "n_citations", "n_chunks", "max_score", "latency_seconds"]:
        s = overall[k]
        md.append(f"| {k} | {s['mean']} | {s['median']} | {s['min']} | {s['max']} | {s['n']} |")
    md.append("")

    md.append("## By Category\n")
    md.append("| Category | n | Cite Acc | Faithfulness | Coverage | Holistic | Latency (s) |")
    md.append("|---|---|---|---|---|---|---|")
    for cat, info in summary["by_category"].items():
        md.append(
            f"| {cat} | {info['n']} | "
            f"{info['citation_accuracy']['mean']} | "
            f"{info['faithfulness']['mean']} | "
            f"{info['coverage']['mean']} | "
            f"{info['holistic_score']['mean']} | "
            f"{info['latency_seconds']['mean']} |"
        )
    md.append("")

    md.append("## Per-Question\n")
    md.append("| ID | Category | Type | Lat (s) | #Cite | CitAcc | Faith | Cov | Hol |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        md.append(
            f"| {r['id']} | {r['category']} | {r['type']} | "
            f"{r['latency_s'] or '-'} | {r['n_citations'] or '-'} | "
            f"{r['citation_accuracy'] if r['citation_accuracy'] is not None else '-'} | "
            f"{r['faithfulness'] if r['faithfulness'] is not None else '-'} | "
            f"{r['coverage'] if r['coverage'] is not None else '-'} | "
            f"{r['holistic_score'] if r['holistic_score'] is not None else '-'} |"
        )
    md.append("")

    args.out_md.write_text("\n".join(md), encoding="utf-8")
    print(f"[+] Wrote {args.out_md}")

    print()
    print("=== Overall ===")
    for k in ["citation_accuracy", "faithfulness", "coverage", "holistic_score",
              "n_citations", "latency_seconds"]:
        s = overall[k]
        print(f"  {k:22s}  mean={s['mean']!s:>6}  median={s['median']!s:>6}  n={s['n']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
