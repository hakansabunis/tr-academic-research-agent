"""TürkResearcher — HF Space (REAL system, free tier).

No external DB: memory-store artifacts + abstracts are pulled from the
public HF index dataset at first request and searched in-process (numpy).
This IS the measured system — trakad-embed-v2 + cross-encoder reranker
over 633K theses (uint8 ≈ float, 97% top-10 parity).

Startup is INSTANT (Gradio launches immediately so the Space is healthy);
the ~2 GB download + index warm happens lazily on the first query — hence
the first request takes a few minutes (shown in the UI).

Each user enters their own DeepSeek API key (never stored by the Space).
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

import gradio as gr

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR / "src"))           # Space layout: /app/src

DATASET = os.environ.get("HF_INDEX_REPO",
                         "hakansabunis/tr-academic-research-agent-index")

_READY = False
_GRAPH = None
_LOCK = threading.Lock()


def _ensure_ready(progress=None):
    """One-time heavy init: pull artifacts, set product env, warm stores,
    build the graph. Guarded so concurrent requests wait, not duplicate."""
    global _READY, _GRAPH
    if _READY:
        return
    with _LOCK:
        if _READY:
            return
        from huggingface_hub import hf_hub_download

        def _pull(fn):
            return hf_hub_download(repo_id=DATASET, repo_type="dataset",
                                   filename=f"memstore/{fn}")

        if progress is not None:
            progress(0.15, desc="İndeks indiriliyor (~2 GB, ilk istek)…")
        vec = _pull("vectors_uint8.npy")
        _pull("payload.parquet")                    # same snapshot dir as vec
        abs_ = _pull("abstracts_filtered_clean.parquet")

        os.environ.update(
            VECTOR_BACKEND="memory",
            MEMSTORE_DIR=str(Path(vec).parent),
            ABSTRACT_PARQUET=abs_,
            EMBEDDING_MODEL="hakansabunis/trakad-embed-v2",
            TRRESEARCHER_RERANK="1",
            RERANK_MODEL="BAAI/bge-reranker-base",
            RERANK_TOP_N="10",
            TRRESEARCHER_LIVE="0",
        )

        if progress is not None:
            progress(0.5, desc="İndeks + abstract store RAM'e yükleniyor…")
        from turk_researcher.graph import build_graph
        from turk_researcher.tools import abstract_store, memory_store

        memory_store.warm()
        abstract_store.warm()
        _GRAPH = build_graph()
        _READY = True


def run(question: str, api_key: str, progress=gr.Progress()):
    q = (question or "").strip()
    if not api_key or not api_key.strip():
        return ("### ⚠️ DeepSeek API key gerekli\n\nplatform.deepseek.com/"
                "api_keys · ~$0.005-0.01/sorgu · Space key'inizi saklamaz.",
                "", "", "")
    if not q:
        return "### Lütfen bir Türkçe soru girin.", "", "", ""

    try:
        _ensure_ready(progress)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"### ❌ Başlatma hatası\n\n```\n{e}\n```", "", "", ""

    os.environ["DEEPSEEK_API_KEY"] = api_key.strip()
    progress(0.6, desc="Pipeline çalışıyor (retriever+reranker→…) ~2-4 dk…")
    try:
        state = _GRAPH.invoke({"question": q})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"### ❌ Hata\n\n```\n{e}\n```", "", "", ""
    finally:
        os.environ["DEEPSEEK_API_KEY"] = ""

    final = state.get("final")
    chunks = state.get("chunks", [])
    plan = state.get("plan")
    plan_md = "\n".join(f"- {sq.text}" for sq in plan.sub_questions) if plan else "—"
    src_md = "\n\n".join(
        f"**[{i}]** {c.author} ({c.year or '?'}) — *{c.title_tr}* · skor={c.score:.3f}"
        for i, c in enumerate(chunks, 1)) or "—"
    if final is None:
        return "### Yanıt üretilemedi.", plan_md, src_md, ""
    conf = (f"\n\n---\n*{len(chunks)} tez kaynağı"
            + (f", en yüksek skor {chunks[0].score:.3f}" if chunks else "") + ".*")
    return final.answer_md + conf, plan_md, src_md, "\n".join(final.citations_ieee)


EXAMPLES = [
    "Türkçe doğal dil işlemede son yıllardaki ana yaklaşımlar nelerdir?",
    "Türkçe metin sınıflandırmada derin öğrenme yöntemleri tezlerde nasıl uygulanmıştır?",
    "Derin öğrenme yöntemleri Türkiye'deki sel ve taşkın tahmininde nasıl uygulanmıştır?",
]

with gr.Blocks(title="TürkResearcher") as demo:
    gr.Markdown("# 🔍 TürkResearcher — Türkçe Akademik Araştırma Ajanı")
    gr.Markdown("**Gerçek sistem**: 633K+ YÖK tezi · trakad-embed-v2 + "
                "cross-encoder reranker · çok-ajanlı RAG. **İlk istek** "
                "~birkaç dk (indeks indirilip RAM'e yüklenir); sonraki "
                "sorgular ~2-4 dk.")
    api_key_box = gr.Textbox(label="🔑 DeepSeek API Key (kendi key'iniz)",
                             type="password", placeholder="sk-...")
    with gr.Row():
        qbox = gr.Textbox(label="Soru (Türkçe)", lines=2, scale=4)
        btn = gr.Button("Sor", variant="primary", size="lg", scale=1)
    gr.Examples(EXAMPLES, inputs=[qbox], label="Örnek sorular")
    with gr.Tab("📝 Yanıt"):
        ans = gr.Markdown()
    with gr.Tab("🗂️ Plan + Kaynaklar"):
        plan_o = gr.Markdown()
        src_o = gr.Markdown()
    with gr.Tab("📚 IEEE Atıflar"):
        cit_o = gr.Markdown()
    btn.click(run, [qbox, api_key_box], [ans, plan_o, src_o, cit_o])
    gr.Markdown("---\nKod: [GitHub](https://github.com/hakansabunis/"
                "tr-academic-research-agent) · MIT / veri CC-BY-4.0")

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=1).launch()
