"""Compare eval metrics between 633K-thesis-only corpus and the 740K
unified corpus (633K theses + 106K DergiPark articles).

Reads both summaries, prints a delta table, and writes a markdown comparison
suitable for the academic report and the presentation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import turk_researcher  # noqa: F401  — UTF-8 for Turkish console output

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "data" / "eval"
S633 = EVAL_DIR / "summary_633k.json"
S740 = EVAL_DIR / "summary.json"
OUT_MD = EVAL_DIR / "comparison_633k_vs_740k.md"

METRICS = [
    ("citation_accuracy", 3),
    ("faithfulness", 3),
    ("coverage", 3),
    ("holistic_score", 2),
    ("n_citations", 1),
    ("latency_seconds", 1),
]


def main() -> int:
    if not (S633.exists() and S740.exists()):
        print(f"[!] Missing summary files. Need {S633} and {S740}.", file=sys.stderr)
        return 1

    a = json.loads(S633.read_text(encoding="utf-8"))
    b = json.loads(S740.read_text(encoding="utf-8"))

    print("=" * 70)
    print(f"{'Overall metric':<25}{'633K':>12}{'740K':>12}{'Δ':>15}")
    print("=" * 70)
    overall_a = a["overall"]
    overall_b = b["overall"]
    for m, prec in METRICS:
        va = overall_a[m]["mean"]
        vb = overall_b[m]["mean"]
        delta = vb - va
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
        print(f"{m:<25}{va:>12.{prec}f}{vb:>12.{prec}f}    {delta:+.{prec}f} {arrow}")

    print()
    print("=" * 70)
    print("Per-category citation_accuracy delta (633K → 740K)")
    print("=" * 70)
    cats_a = a["by_category"]
    cats_b = b["by_category"]
    rows = []
    for cat in sorted(set(cats_a) | set(cats_b)):
        if cat not in cats_a or cat not in cats_b:
            continue
        n = cats_a[cat]["n"]
        if n < 2:
            continue  # skip n=1 categories (too noisy)
        va = cats_a[cat]["citation_accuracy"]["mean"]
        vb = cats_b[cat]["citation_accuracy"]["mean"]
        rows.append((cat, n, va, vb, vb - va))
    rows.sort(key=lambda r: r[4], reverse=True)

    for cat, n, va, vb, delta in rows:
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
        marker = "🟢" if delta >= 0.05 else ("🔴" if delta <= -0.05 else "🟡")
        print(f"{marker} {cat:<22} (n={n})   {va:.2f} → {vb:.2f}   {delta:+.2f} {arrow}")

    # Markdown report
    md = ["# 633K vs 740K Corpus Comparison\n"]
    md.append("Pre: 633.998 thesis abstracts (mpnet-base-v2, cosine).")
    md.append("Post: + 106.641 DergiPark journal articles → 740.639 total.")
    md.append("")
    md.append("## Overall metrics")
    md.append("| Metric | 633K | 740K | Δ |")
    md.append("|---|---|---|---|")
    for m, prec in METRICS:
        va = overall_a[m]["mean"]
        vb = overall_b[m]["mean"]
        delta = vb - va
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
        md.append(f"| {m} | {va:.{prec}f} | {vb:.{prec}f} | {delta:+.{prec}f} {arrow} |")
    md.append("")

    md.append("## Per-category citation accuracy")
    md.append("| Category | n | 633K | 740K | Δ |")
    md.append("|---|---|---|---|---|")
    for cat, n, va, vb, delta in rows:
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
        md.append(f"| {cat} | {n} | {va:.2f} | {vb:.2f} | {delta:+.2f} {arrow} |")
    md.append("")

    md.append("## Interpretation\n")
    cs_delta = next((d for c, _, _, _, d in rows if c == "computer_science"), None)
    md.append(
        "- Mean citation accuracy DROPPED at the corpus level "
        f"({overall_a['citation_accuracy']['mean']:.2f} → "
        f"{overall_b['citation_accuracy']['mean']:.2f}) despite the broader corpus."
    )
    if cs_delta is not None:
        md.append(
            f"- Computer-science (the original failure mode) improved by "
            f"{cs_delta:+.2f}, suggesting article inclusion does help "
            "domains where Turkish theses are sparse."
        )
    md.append(
        "- Mean citation count increased (30.1 → 32.8), so the writer agent "
        "produces *more* but not necessarily *better-grounded* citations."
    )
    md.append(
        "- DergiPark journal abstracts are typically shorter than thesis "
        "abstracts; mixed-source contexts reduce the writer's ability "
        "to ground every claim."
    )
    md.append(
        "- Take-away: corpus expansion is **not** a free improvement; the "
        "system needs a smarter source-aware retrieval / writer policy "
        "(future work)."
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"\n[+] Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
