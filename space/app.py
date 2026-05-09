"""TürkResearcher — Hugging Face Spaces demo (live-API edition).

This is the public demo of TürkResearcher. Because the full 15 GB Chroma
index does not fit in HF Spaces free tier, this demo runs the agent in
*live-only* mode: retrieval is done through public academic APIs
(OpenAlex, Semantic Scholar). The local-corpus version of the agent is
in the GitHub repo (`hakansabunis/tr-academic-research-agent`).

Pipeline:
    Question (TR) → Planner → LiveSearch → Synthesiser → Writer
"""
from __future__ import annotations

import os
import re
import time
from typing import Iterable
from urllib.parse import urlencode

import gradio as gr
import requests
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


# ───────────── Configuration ─────────────


DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

USER_AGENT = "tr-academic-research-agent-demo/0.1 (HF Space)"
DEFAULT_TIMEOUT = 15


# ───────────── Schemas ─────────────


class SubQuestion(BaseModel):
    text: str = Field(..., description="Türkçe alt soru")


class Plan(BaseModel):
    sub_questions: list[SubQuestion]


class FinalAnswer(BaseModel):
    answer_md: str
    citations_ieee: list[str] = Field(default_factory=list)


# ───────────── LLM ─────────────


def build_llm(temperature: float = 0.2) -> ChatOpenAI:
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY not set in HF Space secrets.")
    return ChatOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        model=DEEPSEEK_MODEL,
        temperature=temperature,
    )


# ───────────── Live retrieval ─────────────


def reconstruct_abstract(inverted_idx: dict | None) -> str:
    if not inverted_idx:
        return ""
    pairs = []
    for word, positions in inverted_idx.items():
        for p in positions:
            pairs.append((p, word))
    pairs.sort()
    return " ".join(w for _, w in pairs)


def search_openalex(query: str, k: int = 6, language: str | None = None) -> list[dict]:
    params = {
        "search": query,
        "per-page": k,
        "select": "id,doi,display_name,publication_year,authorships,abstract_inverted_index,language,primary_location",
    }
    if language:
        params["filter"] = f"language:{language}"
    try:
        r = requests.get(
            "https://api.openalex.org/works",
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code != 200:
            return []
        out = []
        for w in r.json().get("results", []):
            title = w.get("display_name") or ""
            abstract = reconstruct_abstract(w.get("abstract_inverted_index"))
            if not (title or abstract):
                continue
            authors = ", ".join(
                (a.get("author") or {}).get("display_name", "")
                for a in (w.get("authorships") or [])
            )
            primary = w.get("primary_location") or {}
            source = (primary.get("source") or {}) if primary else {}
            venue = source.get("display_name") or ""
            url = w.get("doi") or w.get("id", "")
            out.append({
                "id": w.get("id", ""),
                "title": title,
                "authors": authors,
                "year": w.get("publication_year"),
                "venue": venue,
                "abstract": abstract,
                "url": url,
                "source_kind": "OpenAlex",
            })
        return out
    except (requests.RequestException, ValueError):
        return []


def search_semantic_scholar(query: str, k: int = 6) -> list[dict]:
    try:
        r = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": k,
                "fields": "paperId,title,abstract,authors,year,url,venue",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 429:
            time.sleep(2)
            r = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": query,
                    "limit": k,
                    "fields": "paperId,title,abstract,authors,year,url,venue",
                },
                headers={"User-Agent": USER_AGENT},
                timeout=DEFAULT_TIMEOUT,
            )
        if r.status_code != 200:
            return []
        out = []
        for p in r.json().get("data", []):
            out.append({
                "id": p.get("paperId", ""),
                "title": p.get("title") or "",
                "authors": ", ".join((a or {}).get("name", "") for a in (p.get("authors") or [])),
                "year": p.get("year"),
                "venue": p.get("venue") or "",
                "abstract": p.get("abstract") or "",
                "url": p.get("url") or "",
                "source_kind": "SemanticScholar",
            })
        return out
    except (requests.RequestException, ValueError):
        return []


def retrieve_live(queries: Iterable[str], k_each: int = 5) -> list[dict]:
    seen: dict[str, dict] = {}
    for q in queries:
        if not q.strip():
            continue
        for chunk in search_openalex(q, k=k_each, language="tr") + search_openalex(q, k=k_each):
            if chunk["id"] not in seen:
                seen[chunk["id"]] = chunk
        for chunk in search_semantic_scholar(q, k=k_each):
            if chunk["id"] not in seen:
                seen[chunk["id"]] = chunk
    # Cap to keep token budget reasonable
    return list(seen.values())[:24]


# ───────────── Agents ─────────────


PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Sen Türkçe akademik araştırma asistanısın. Soruyu 3-5 özgül alt soruya "
        "böl. Her alt soru farklı bir kavramsal açıyı kapsasın (yöntem, bulgu, "
        "sınırlılık, uygulama). Çıktı yalnızca yapılandırılmış JSON.",
    ),
    ("human", "Soru: {question}"),
])


WRITER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Sen Türkçe akademik yazım uzmanısın. Sana verilen kaynaklara dayanarak "
        "kullanıcının sorusuna kapsamlı, akıcı ve akademik üslupta bir yanıt yaz. "
        "Kurallar:\n"
        "1. Yalnızca getirilen kaynaklara dayan; uydurma yapma.\n"
        "2. Cümle bazlı atıf kullan: '[n]' formatında, n verilen kaynak numarası.\n"
        "3. Markdown kullan: kısa giriş, alt-başlıklarla bulgular, sonuç paragrafı.\n"
        "4. Sonunda 'Kaynaklar' eklemenin sistem otomatik yapacak; sen ekleme.\n"
        "Çıktı yalnızca yapılandırılmış JSON."
    ),
    (
        "human",
        "Soru: {question}\n\nKaynaklar:\n{chunks}",
    ),
])


def plan_agent(question: str) -> Plan:
    llm = build_llm(temperature=0.1)
    chain = PLANNER_PROMPT | llm.with_structured_output(Plan, method="function_calling")
    return chain.invoke({"question": question})


def format_chunks_for_writer(chunks: list[dict]) -> str:
    lines = []
    for i, c in enumerate(chunks, 1):
        head = (
            f"[{i}] ({c['source_kind']}) "
            f"{c['authors'][:50] or '?'} "
            f"({c.get('year') or '?'}) — {c['title'][:90]}"
        )
        body = (c.get("abstract") or "")[:600].replace("\n", " ")
        lines.append(f"{head}\n{body}")
    return "\n\n".join(lines)


def build_ieee_citation(c: dict, idx: int) -> str:
    parts = [f"[{idx}] {c['authors']},", f'"{c["title"]},"']
    if c.get("venue"):
        parts.append(f"{c['venue']},")
    if c.get("year"):
        parts.append(f"{c['year']}.")
    if c.get("url"):
        parts.append(f"[Online]. {c['url']}")
    return " ".join(parts).strip()


def writer_agent(question: str, chunks: list[dict]) -> FinalAnswer:
    llm = build_llm(temperature=0.3)
    chain = WRITER_PROMPT | llm.with_structured_output(FinalAnswer, method="function_calling")
    drafted = chain.invoke({
        "question": question,
        "chunks": format_chunks_for_writer(chunks),
    })

    # Build IEEE citations deterministically from chunk metadata
    ieee = [build_ieee_citation(c, i) for i, c in enumerate(chunks, 1)]

    # Strip any [n] in answer that exceeds available chunk count
    n_max = len(chunks)
    answer = drafted.answer_md
    answer = re.sub(
        r"\[(\d+)\]",
        lambda m: m.group(0) if int(m.group(1)) <= n_max else "",
        answer,
    )

    return FinalAnswer(answer_md=answer, citations_ieee=ieee)


# ───────────── End-to-end orchestration ─────────────


def run_agent(question: str, progress=gr.Progress()) -> tuple[str, str, str, str]:
    if not question.strip():
        return ("", "", "", "")

    progress(0.1, desc="Sorgu planlanıyor…")
    try:
        plan = plan_agent(question.strip())
    except Exception as e:
        return ("", "", "", f"❌ Plan hatası: {e}")
    plan_md = "\n".join(f"- {sq.text}" for sq in plan.sub_questions)

    progress(0.4, desc="Kaynaklar aranıyor (OpenAlex + Semantic Scholar)…")
    queries = [question.strip()] + [sq.text for sq in plan.sub_questions]
    chunks = retrieve_live(queries, k_each=4)

    if not chunks:
        return (plan_md, "", "", "❌ Hiçbir kaynak bulunamadı; lütfen sorguyu farklı şekilde dene.")

    chunks_md = "\n\n".join(
        f"**[{i}]** ({c['source_kind']}) {c['authors']} — *{c['title']}* ({c.get('year','?')}) — {c.get('venue','')}"
        for i, c in enumerate(chunks, 1)
    )

    progress(0.75, desc="Yanıt yazılıyor…")
    try:
        final = writer_agent(question.strip(), chunks)
    except Exception as e:
        return (plan_md, chunks_md, "", f"❌ Yazım hatası: {e}")

    citations_md = "\n".join(final.citations_ieee)
    progress(1.0, desc="Bitti")
    return plan_md, chunks_md, final.answer_md, citations_md


# ───────────── UI ─────────────


THEME = gr.themes.Soft(
    primary_hue="blue",
    neutral_hue="slate",
).set(
    body_background_fill="*neutral_50",
)

EXAMPLES = [
    "Türkçe doğal dil işlemede son yıllardaki ana yaklaşımlar nelerdir?",
    "Derin öğrenme yöntemleri Türkiye'deki sel ve taşkın tahmininde nasıl uygulanmıştır?",
    "Türkiye'de uzaktan eğitimde öğrenci motivasyonunu artıran pedagojik stratejiler nelerdir?",
    "Yenilenebilir enerji kaynaklarından rüzgar türbinlerinin Türkiye'deki potansiyeli nedir?",
    "İklim değişikliğinin Türkiye'deki tarımsal üretim üzerindeki ekonomik etkileri nelerdir?",
]


with gr.Blocks(title="TürkResearcher Demo") as demo:
    gr.Markdown(
        """
        # 🔍 TürkResearcher — Türkçe Akademik Araştırma Ajanı
        ### Multi-agent LLM, OpenAlex + Semantic Scholar'dan kanıt çekerek IEEE atıflı Türkçe yanıt üretir.

        Bu demo, projenin **canlı API versiyonudur** (Hugging Face Spaces sınırı).
        Tam 740K Türkçe tez + dergi makalesi indeksli versiyonu için
        [GitHub repo](https://github.com/hakansabunis/tr-academic-research-agent) ve
        [HF Hub index](https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index).
        """
    )

    with gr.Row():
        with gr.Column(scale=4):
            question = gr.Textbox(
                label="Soru (Türkçe)",
                placeholder="Örn: Türkçe doğal dil işlemede son yıllardaki ana yaklaşımlar nelerdir?",
                lines=2,
            )
        with gr.Column(scale=1, min_width=120):
            submit = gr.Button("Sor", variant="primary", size="lg")

    gr.Examples(
        examples=EXAMPLES,
        inputs=[question],
        label="Örnek sorular",
    )

    with gr.Tab("📝 Yanıt"):
        answer_out = gr.Markdown(label="Akademik Özet")
    with gr.Tab("🗂️ Plan + Kaynaklar"):
        gr.Markdown("### 1. Planner — alt sorular")
        plan_out = gr.Markdown()
        gr.Markdown("### 2. Retrieved kaynaklar")
        chunks_out = gr.Markdown()
    with gr.Tab("📚 IEEE Atıflar"):
        citations_out = gr.Markdown()

    submit.click(
        fn=run_agent,
        inputs=[question],
        outputs=[plan_out, chunks_out, answer_out, citations_out],
    )

    gr.Markdown(
        """
        ---
        **Mimari:** Planner → LiveSearch (OpenAlex + Semantic Scholar) → Writer.
        **Lisans:** MIT (kod), CC-BY-4.0 (veri). Geliştirici: [Hakan Sabuniş](https://hakansabunis.com).
        """
    )


if __name__ == "__main__":
    demo.launch(theme=THEME)
