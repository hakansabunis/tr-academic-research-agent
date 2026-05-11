"""Compare v1 vs v2 retrieval for STEM questions where v2 regressed.

For each STEM question:
  - Show question + category
  - List top-5 retrieved titles in v1 vs v2 (overlap highlighted)
  - Show judge scores side-by-side
  - Print delta interpretation

Output: data/eval/stem_regression_analysis.md
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "data" / "eval" / "questions.json"
RUNS_V1 = ROOT / "data" / "eval" / "runs"
RUNS_V2 = ROOT / "data" / "eval" / "runs_v2"
JUDGE_V1 = ROOT / "data" / "eval" / "judgments"
JUDGE_V2 = ROOT / "data" / "eval" / "judgments_v2"
OUT = ROOT / "data" / "eval" / "stem_regression_analysis.md"

# STEM categories from our eval taxonomy
STEM_CATEGORIES = {
    "computer_science",
    "engineering",
    "chemistry",
    "biology",
    "physics",
    "agriculture",
    "veterinary",
    "health",
    "multi_domain",  # often STEM-leaning
}


def load_run(runs_dir: Path, qid: str) -> dict | None:
    p = runs_dir / f"{qid}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def load_judge(judge_dir: Path, qid: str) -> dict | None:
    p = judge_dir / f"{qid}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def top_titles(run: dict, k: int = 5) -> list[tuple[str, str, float]]:
    """Returns list of (tez_no, title_short, score) for top-K retrieved chunks."""
    if not run or not run.get("result"):
        return []
    chunks = run["result"]["retrieval"]["chunks"][:k]
    return [
        (c.get("tez_no", "?"), (c.get("title_tr") or "")[:100], c.get("score", 0))
        for c in chunks
    ]


def fmt_score_row(label, j):
    if not j or not j.get("judgment"):
        return f"  {label}: (no judgment)"
    jd = j["judgment"]
    return (
        f"  {label:<3s}: cit={jd['citation_accuracy']:.2f}  "
        f"faith={jd['faithfulness']:.2f}  cov={jd['coverage']:.2f}  "
        f"holistic={jd['holistic_score']}/5"
    )


def main():
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))

    # Filter STEM
    stem_qs = [q for q in questions if q.get("category", "") in STEM_CATEGORIES]
    print(f"Found {len(stem_qs)} STEM questions out of {len(questions)} total\n")

    lines = ["# STEM Regression Analysis — v1 vs v2 Side-by-Side", ""]
    lines.append(f"*{len(stem_qs)} STEM questions analyzed. For each, top-5 retrieved "
                 "thesis titles compared between v1 (mpnet) and v2 (trakad-embed-v2), "
                 "plus judge scores.*")
    lines.append("")

    for q in stem_qs:
        qid = q["id"]
        cat = q.get("category", "")
        v1_run = load_run(RUNS_V1, qid)
        v2_run = load_run(RUNS_V2, qid)
        v1_j = load_judge(JUDGE_V1, qid)
        v2_j = load_judge(JUDGE_V2, qid)

        v1_titles = top_titles(v1_run)
        v2_titles = top_titles(v2_run)

        v1_ids = {t[0] for t in v1_titles}
        v2_ids = {t[0] for t in v2_titles}
        overlap = v1_ids & v2_ids
        only_v1 = v1_ids - v2_ids
        only_v2 = v2_ids - v1_ids

        # Print to console
        print(f"\n=== {qid} [{cat}] ===")
        print(f"Q: {q['question'][:90]}")
        print(f"Retrieval overlap (top-5): {len(overlap)}/5")
        print(fmt_score_row("v1", v1_j))
        print(fmt_score_row("v2", v2_j))

        # Compute holistic delta
        v1_jd = v1_j.get("judgment") if v1_j else None
        v2_jd = v2_j.get("judgment") if v2_j else None
        if v1_jd and v2_jd:
            cit_delta = v2_jd["citation_accuracy"] - v1_jd["citation_accuracy"]
            cit_arrow = "UP" if cit_delta > 0.05 else ("DOWN" if cit_delta < -0.05 else "FLAT")
            print(f"  cit_acc delta: {cit_delta:+.2f} {cit_arrow}")

        # Markdown
        lines.append(f"## {qid} — `{cat}`")
        lines.append("")
        lines.append(f"**Question:** {q['question']}")
        lines.append("")

        if v1_jd and v2_jd:
            cit_delta = v2_jd["citation_accuracy"] - v1_jd["citation_accuracy"]
            faith_delta = v2_jd["faithfulness"] - v1_jd["faithfulness"]
            cov_delta = v2_jd["coverage"] - v1_jd["coverage"]
            holistic_delta = v2_jd["holistic_score"] - v1_jd["holistic_score"]
            lines.append("**Judge scores (v1 → v2):**")
            lines.append("")
            lines.append("| Metric | v1 | v2 | Δ |")
            lines.append("|---|---|---|---|")
            lines.append(f"| citation_accuracy | {v1_jd['citation_accuracy']:.2f} | {v2_jd['citation_accuracy']:.2f} | {cit_delta:+.2f} |")
            lines.append(f"| faithfulness | {v1_jd['faithfulness']:.2f} | {v2_jd['faithfulness']:.2f} | {faith_delta:+.2f} |")
            lines.append(f"| coverage | {v1_jd['coverage']:.2f} | {v2_jd['coverage']:.2f} | {cov_delta:+.2f} |")
            lines.append(f"| holistic | {v1_jd['holistic_score']} | {v2_jd['holistic_score']} | {holistic_delta:+d} |")
            lines.append("")

        lines.append(f"**Retrieval overlap (top-5):** {len(overlap)}/5 same chunks. "
                     f"{len(only_v1)} only in v1, {len(only_v2)} only in v2.")
        lines.append("")

        lines.append("**v1 top-5 retrieved:**")
        for tez_no, title, score in v1_titles:
            mark = "✓" if tez_no in overlap else " "
            lines.append(f"- {mark} `{tez_no}` [{score:.3f}] {title}")
        lines.append("")
        lines.append("**v2 top-5 retrieved:**")
        for tez_no, title, score in v2_titles:
            mark = "✓" if tez_no in overlap else " "
            lines.append(f"- {mark} `{tez_no}` [{score:.3f}] {title}")
        lines.append("")
        lines.append("---")
        lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[+] Wrote {OUT}")


if __name__ == "__main__":
    main()
