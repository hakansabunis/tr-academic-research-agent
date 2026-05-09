"""Generate architecture + data-pipeline PNGs for the proposal."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
ARCH_PATH = HERE / "fig_architecture.png"
DATA_PATH = HERE / "fig_data_pipeline.png"

# Theme
PRIMARY = "#1F3A5F"
ACCENT = "#3AA2FF"
SOFT = "#E9F0F8"
TEXT = "#1B1B1B"
MUTED = "#5A6679"


def rounded_box(ax, x, y, w, h, label, *, fill=SOFT, edge=PRIMARY, fontsize=11, bold=True):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.6, edgecolor=edge, facecolor=fill, zorder=2,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2, y + h / 2, label,
        ha="center", va="center",
        fontsize=fontsize, color=TEXT,
        fontweight="bold" if bold else "normal",
        zorder=3,
    )


def arrow(ax, x1, y1, x2, y2, *, color=PRIMARY, style="-|>"):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style, mutation_scale=14,
        color=color, linewidth=1.6, zorder=1,
    ))


def build_architecture():
    fig, ax = plt.subplots(figsize=(11, 6.4), dpi=170)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.2)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # Title strip
    ax.text(
        7, 7.7, "TürkResearcher — LangGraph Multi-Agent Pipeline",
        ha="center", va="center", fontsize=15, fontweight="bold", color=PRIMARY,
    )

    # User input
    rounded_box(ax, 0.6, 5.6, 2.2, 1.2, "Question (TR)", fill="white", edge=ACCENT, fontsize=11)
    arrow(ax, 2.8, 6.2, 3.6, 6.2)

    # 5 main agents in horizontal row
    y_main = 5.6
    h_main = 1.2
    boxes = [
        ("Planner", 3.6),
        ("Retriever", 5.8),
        ("Synthesiser", 8.0),
        ("Critic", 10.2),
        ("Writer", 12.4),
    ]
    box_w = 1.8
    for label, x in boxes:
        edge = ACCENT if label == "Critic" else PRIMARY
        fill = "#FFF6E0" if label == "Critic" else SOFT
        rounded_box(ax, x, y_main, box_w, h_main, label, fill=fill, edge=edge)
    # arrows between main boxes
    for i in range(len(boxes) - 1):
        x_from = boxes[i][1] + box_w
        x_to = boxes[i + 1][1]
        arrow(ax, x_from, y_main + h_main / 2, x_to, y_main + h_main / 2)

    # Output
    rounded_box(ax, 12.4, 3.5, 1.8, 1.0, "IEEE-cited\nTurkish answer", fill="white", edge=ACCENT, fontsize=10, bold=False)
    arrow(ax, 13.3, y_main, 13.3, 4.5)

    # Critic loops
    # Back to Retriever (loop ≤ 2)
    ax.add_patch(FancyArrowPatch(
        (10.2 + box_w / 2, y_main + h_main),
        (5.8 + box_w / 2, y_main + h_main),
        arrowstyle="-|>", mutation_scale=14,
        color=ACCENT, linewidth=1.4, linestyle="--",
        connectionstyle="arc3,rad=-0.45", zorder=1,
    ))
    ax.text(
        8.0, 7.55, "coverage_ok = False  (loop ≤ 2)",
        ha="center", va="center", fontsize=9, color=ACCENT, style="italic",
    )

    # LiveSearch fallback (below Critic)
    rounded_box(ax, 10.2, 3.0, 1.8, 1.0, "LiveSearch", fill="#F1FFF6", edge="#3CB371", fontsize=10)
    ax.add_patch(FancyArrowPatch(
        (10.2 + box_w / 2, y_main),
        (10.2 + box_w / 2, 4.0),
        arrowstyle="-|>", mutation_scale=12,
        color="#3CB371", linewidth=1.2, linestyle="--", zorder=1,
    ))
    ax.add_patch(FancyArrowPatch(
        (10.2 + box_w, 3.5),
        (12.4, 4.4),
        arrowstyle="-|>", mutation_scale=12,
        color="#3CB371", linewidth=1.2, linestyle="--", zorder=1,
    ))
    ax.text(
        11.1, 2.65, "OpenAlex / SemanticScholar / DergiPark",
        ha="center", va="center", fontsize=8, color="#3CB371",
    )

    # State store band
    rounded_box(
        ax, 3.6, 1.0, 8.4, 0.9,
        "GraphState  ·  question · plan · chunks · synthesis · critic · iteration · final",
        fill="#F4F4F4", edge=MUTED, fontsize=9, bold=False,
    )

    # Legend
    legend_elems = [
        Line2D([0], [0], color=PRIMARY, lw=1.6, label="Deterministic edge"),
        Line2D([0], [0], color=ACCENT, lw=1.4, linestyle="--", label="Conditional loop"),
        Line2D([0], [0], color="#3CB371", lw=1.2, linestyle="--", label="Live-search fallback"),
    ]
    ax.legend(
        handles=legend_elems, loc="lower right",
        bbox_to_anchor=(0.985, 0.02), fontsize=8.5, frameon=False,
    )

    plt.tight_layout()
    plt.savefig(ARCH_PATH, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Wrote {ARCH_PATH}")


def build_data_pipeline():
    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=170)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6.0)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(
        7, 5.6, "Data Pipeline — Hugging Face Hub → Local Agent",
        ha="center", va="center", fontsize=14, fontweight="bold", color=PRIMARY,
    )

    # Stages
    stages = [
        ("HF Hub\nraw dataset\n(~1.56 GB)", 0.3, "white", PRIMARY),
        ("Filter\n≥50 words\n+ dedup", 2.7, SOFT, PRIMARY),
        ("Embed\n(mpnet,\nColab T4)", 5.1, SOFT, PRIMARY),
        ("Chroma\n(cosine,\n768-dim)", 7.5, SOFT, PRIMARY),
        ("HF Hub\nindex\n(15 GB)", 9.9, "white", PRIMARY),
        ("Local pull\n+ Agent\nruntime", 12.3, "#E8F8EC", "#3CB371"),
    ]
    box_w = 1.85
    box_h = 2.1
    y = 1.6
    for label, x, fill, edge in stages:
        rounded_box(ax, x, y, box_w, box_h, label, fill=fill, edge=edge, fontsize=10, bold=False)
    for i in range(len(stages) - 1):
        x_from = stages[i][1] + box_w
        x_to = stages[i + 1][1]
        arrow(ax, x_from, y + box_h / 2, x_to, y + box_h / 2)

    # Above row: labels
    captions = [
        ("umutertugrul/...", 0.3),
        ("scripts/02_filter.py", 2.7),
        ("scripts/03_build_index.py", 5.1),
        ("Chroma upsert", 7.5),
        ("hakansabunis/...", 9.9),
        ("scripts/run.py", 12.3),
    ]
    for cap, x in captions:
        ax.text(
            x + box_w / 2, y + box_h + 0.25, cap,
            ha="center", va="bottom", fontsize=8, color=MUTED, style="italic",
        )

    # Bottom band: counts
    counts = [
        ("650K rows", 0.3),
        ("→ ~600K", 2.7),
        ("→ 768-dim", 5.1),
        ("→ HNSW", 7.5),
        ("public", 9.9),
        ("offline", 12.3),
    ]
    for cap, x in counts:
        ax.text(
            x + box_w / 2, y - 0.35, cap,
            ha="center", va="top", fontsize=8.5, color=ACCENT, fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig(DATA_PATH, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Wrote {DATA_PATH}")


if __name__ == "__main__":
    build_architecture()
    build_data_pipeline()
