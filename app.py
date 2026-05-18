"""TürkResearcher — LOCAL product UI (the real system).

Unlike `space/app.py` (a lite live-API demo: no thesis corpus, no
fine-tuned embedder, no reranker — HF Spaces can't host the 14.8 GB index),
this runs the **actual measured-best pipeline** over 633K+ Turkish theses:

    Planner → Retriever (trakad-embed-v2 + cross-encoder reranker)
            → Synthesizer → Critic → Writer

Config comes from product defaults (config.py / .env): trakad-embed-v2 +
chroma_db_v2 + reranker ON + live search OFF. The DeepSeek key is read from
.env (no key box — this is your local machine).

Run:
    pip install -r requirements.txt        # includes gradio
    python app.py                          # → http://127.0.0.1:7860
"""
from __future__ import annotations

import sys
from pathlib import Path

import gradio as gr

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from turk_researcher.config import load_settings  # noqa: E402
from turk_researcher.graph import build_graph  # noqa: E402
from turk_researcher.tools.reranker import RERANK_ENABLED  # noqa: E402

_GRAPH = None


def _graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def _config_banner() -> str:
    s = load_settings()
    emb = "trakad-embed-v2" if "trakad-embed-v2" in s.embedding_model else s.embedding_model
    idx = "chroma_db_v2" if str(s.chroma_persist_dir).endswith("chroma_db_v2") else s.chroma_persist_dir.name
    rr = "ON" if RERANK_ENABLED else "OFF"
    key = "var" if s.deepseek_api_key else "**YOK (.env'e DEEPSEEK_API_KEY ekle)**"
    return (f"**Aktif config:** embedder=`{emb}` · indeks=`{idx}` · "
            f"reranker={rr} · DeepSeek key={key}")


def run(question: str, progress=gr.Progress()):
    q = (question or "").strip()
    if not q:
        return "### Lütfen bir Türkçe soru girin.", "", "", ""
    if not load_settings().deepseek_api_key:
        return ("### ⚠️ DeepSeek API anahtarı yok\n\n`.env` dosyasına "
                "`DEEPSEEK_API_KEY=...` ekleyin.", "", "", "")

    progress(0.1, desc="Pipeline çalışıyor (planner→retriever+reranker→…)…")
    try:
        state = _graph().invoke({"question": q})
    except Exception as e:  # surface, don't fabricate
        return f"### ❌ Hata\n\n```\n{e}\n```", "", "", ""

    final = state.get("final")
    chunks = state.get("chunks", [])
    plan = state.get("plan")

    plan_md = "\n".join(f"- {sq.text}" for sq in plan.sub_questions) if plan else "—"
    src_md = "\n\n".join(
        f"**[{i}]** {c.author} ({c.year or '?'}) — *{c.title_tr}*  ·  skor={c.score:.3f}"
        for i, c in enumerate(chunks, 1)
    ) or "—"
    if final is None:
        return "### Yanıt üretilemedi.", plan_md, src_md, ""
    conf = (f"\n\n---\n*{len(chunks)} tez kaynağı"
            + (f", en yüksek skor {chunks[0].score:.3f}" if chunks else "")
            + ".*")
    return final.answer_md + conf, plan_md, src_md, "\n".join(final.citations_ieee)


EXAMPLES = [
    "Türkçe doğal dil işlemede son yıllardaki ana yaklaşımlar nelerdir?",
    "Türkçe metin sınıflandırmada derin öğrenme yöntemleri tezlerde nasıl uygulanmıştır?",
    "Derin öğrenme yöntemleri Türkiye'deki sel ve taşkın tahmininde nasıl uygulanmıştır?",
]

_THEME = gr.themes.Soft(primary_hue="blue", neutral_hue="slate")

with gr.Blocks(title="TürkResearcher (Local)") as demo:
    gr.Markdown("# 🔍 TürkResearcher — Yerel Sürüm (gerçek sistem)")
    gr.Markdown("633K+ YÖK tezi · trakad-embed-v2 + cross-encoder reranker · "
                "çok-ajanlı RAG. *(Halka açık HF Space sadece lite demo'dur.)*")
    gr.Markdown(_config_banner())

    with gr.Row():
        qbox = gr.Textbox(label="Soru (Türkçe)", lines=2,
                          placeholder="Örn: Türkçe doğal dil işlemede son yıllardaki ana yaklaşımlar nelerdir?")
        btn = gr.Button("Sor", variant="primary", size="lg", scale=0)
    gr.Examples(EXAMPLES, inputs=[qbox], label="Örnek sorular")

    with gr.Tab("📝 Yanıt"):
        ans = gr.Markdown()
    with gr.Tab("🗂️ Plan + Kaynaklar"):
        gr.Markdown("### Planner — alt sorular")
        plan_o = gr.Markdown()
        gr.Markdown("### Reranked kaynaklar")
        src_o = gr.Markdown()
    with gr.Tab("📚 IEEE Atıflar"):
        cit_o = gr.Markdown()

    btn.click(run, inputs=[qbox], outputs=[ans, plan_o, src_o, cit_o])

if __name__ == "__main__":
    # The pipeline runs 2–4 min (rerank on CPU + multi-agent DeepSeek calls).
    # Without queue(), Gradio silently times out long requests → "no answer".
    demo.queue(default_concurrency_limit=2)
    try:
        demo.launch(theme=_THEME)
    except TypeError:
        # Older Gradio: theme belongs on Blocks, not launch — fall back.
        demo.theme = _THEME
        demo.launch()
