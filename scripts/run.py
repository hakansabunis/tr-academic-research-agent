"""CLI entry point: ask TürkResearcher a Turkish academic question."""
from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from turk_researcher.graph import build_graph

console = Console()


@click.command()
@click.argument("question", nargs=-1, required=True)
@click.option("--show-trace/--no-show-trace", default=False, help="Print intermediate state.")
def main(question: tuple[str, ...], show_trace: bool) -> None:
    q = " ".join(question).strip()
    console.print(Panel.fit(q, title="Soru", border_style="cyan"))

    graph = build_graph()
    state = graph.invoke({"question": q})

    if show_trace:
        plan = state.get("plan")
        if plan:
            console.print(Panel.fit(
                "\n".join(f"• {sq.text}" for sq in plan.sub_questions),
                title="Plan (alt sorular)", border_style="yellow",
            ))
        chunks = state.get("chunks", [])
        console.print(Panel.fit(
            f"{len(chunks)} kaynak bulundu (en yüksek skor: {chunks[0].score:.3f})" if chunks
            else "Kaynak bulunamadı",
            title="Retrieval", border_style="yellow",
        ))
        critic = state.get("critic")
        if critic:
            console.print(Panel.fit(
                f"coverage_ok={critic.coverage_ok}\nmissing={critic.missing_aspects}\n"
                f"requery={critic.requery_terms}\nnotes={critic.notes}",
                title=f"Critic (iter {state.get('iteration', '?')})", border_style="yellow",
            ))

    final = state.get("final")
    if final is None:
        console.print("[red]Yanıt üretilemedi.[/red]")
        return

    console.print(Panel(Markdown(final.answer_md), title="Yanıt", border_style="green"))
    console.print(Panel(
        "\n".join(final.citations_ieee),
        title="Kaynaklar (IEEE)", border_style="blue",
    ))


if __name__ == "__main__":
    main()
