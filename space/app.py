"""TürkResearcher — Hugging Face Spaces demo (live-API, BYO-key edition).

Each user enters their own DeepSeek API key in the UI. The Space owner's
key is never used or exposed.

Pipeline:  Question (TR) → Planner → LiveSearch → Writer
Retrieval: OpenAlex + Semantic Scholar (free public APIs).
"""
from __future__ import annotations

import os
import re
import time
from typing import Iterable
from urllib.parse import urlencode

import gradio as gr
import requests
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


# ───────────── Constants ─────────────


DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

USER_AGENT = "tr-academic-research-agent-demo/0.1 (HF Space)"
DEFAULT_TIMEOUT = 15

# Turkish diacritics → ASCII (OpenAlex/Semantic Scholar struggle with ç/ğ/ı/ö/ş/ü)
_TR_TO_ASCII = str.maketrans({
    "ı": "i", "İ": "I", "ş": "s", "Ş": "S",
    "ğ": "g", "Ğ": "G", "ü": "u", "Ü": "U",
    "ö": "o", "Ö": "O", "ç": "c", "Ç": "C",
})


def to_ascii(text: str) -> str:
    """Map Turkish diacritics to ASCII for fault-tolerant API queries."""
    return text.translate(_TR_TO_ASCII)


# ───────────── Schemas ─────────────


class SubQuestion(BaseModel):
    text: str = Field(..., description="Türkçe alt soru")


class Plan(BaseModel):
    sub_questions: list[SubQuestion]
    en_search_terms: list[str] = Field(
        default_factory=list,
        description="3-5 İngilizce akademik arama terimleri (OpenAlex/SS için)",
    )


class FinalAnswer(BaseModel):
    answer_md: str
    citations_ieee: list[str] = Field(default_factory=list)


# ───────────── LLM ─────────────


def build_llm(api_key: str, temperature: float = 0.2) -> ChatOpenAI:
    if not api_key:
        raise RuntimeError("Please enter your DeepSeek API key in the form above.")
    return ChatOpenAI(
        api_key=api_key,
        base_url=DEEPSEEK_BASE_URL,
        model=DEEPSEEK_MODEL,
        temperature=temperature,
    )


# ───────────── Live retrieval (no key needed) ─────────────


def reconstruct_abstract(inverted_idx: dict | None) -> str:
    if not inverted_idx:
        return ""
    pairs = [(p, w) for w, ps in inverted_idx.items() for p in ps]
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
    params = {
        "query": query,
        "limit": k,
        "fields": "paperId,title,abstract,authors,year,url,venue",
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params=params, headers=headers, timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 429:
            time.sleep(2)
            r = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params=params, headers=headers, timeout=DEFAULT_TIMEOUT,
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


def retrieve_live(queries: Iterable[str], k_each: int = 4) -> list[dict]:
    """For each query, also try its ASCII-transliterated variant. OpenAlex
    and Semantic Scholar tokenisers handle Latin-only queries far better
    than Turkish-diacritic queries (ç/ğ/ı/ö/ş/ü)."""
    seen: dict[str, dict] = {}
    for q in queries:
        q = q.strip()
        if not q:
            continue
        variants = {q, to_ascii(q)}  # original + ASCII transliteration
        for v in variants:
            for chunk in search_openalex(v, k=k_each):
                if chunk["id"] not in seen:
                    seen[chunk["id"]] = chunk
            for chunk in search_semantic_scholar(v, k=k_each):
                if chunk["id"] not in seen:
                    seen[chunk["id"]] = chunk
    return list(seen.values())[:24]


# ───────────── Agents ─────────────


_PLAN_PARSER = PydanticOutputParser(pydantic_object=Plan)
_ANSWER_PARSER = PydanticOutputParser(pydantic_object=FinalAnswer)


PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Sen Türkçe akademik araştırma asistanısın. İki şey üreteceksin:\n\n"
        "1. **sub_questions**: Soruyu 3-5 özgül alt soruya böl. Her alt soru "
        "farklı bir kavramsal açıyı kapsasın (yöntem, bulgu, sınırlılık, uygulama). "
        "Türkçe yaz.\n\n"
        "2. **en_search_terms**: Aynı konuyu kapsayan 3-5 İngilizce akademik "
        "arama terimi. OpenAlex ve Semantic Scholar API'leri İngilizce sorgularla "
        "çok daha iyi sonuç döner. Direkt çeviri değil, alanı tanımlayan kısa "
        "İngilizce keyword öbekleri olsun. Örneğin:\n"
        "   - Soru: 'Türkçe doğal dil işleme metodları' → "
        "['Turkish NLP transformer', 'BERT Turkish', 'Turkish text classification']\n"
        "   - Soru: 'Sel tahmini derin öğrenme' → "
        "['flood prediction deep learning', 'LSTM hydrology', 'flood forecasting neural network']\n\n"
        "{format_instructions}\n\n"
        "ÖNEMLİ: Yalnızca tek bir JSON nesnesi döndür, başka açıklama ekleme.",
    ),
    ("human", "Soru: {question}"),
]).partial(format_instructions=_PLAN_PARSER.get_format_instructions())


WRITER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Sen Türkçe akademik yazım uzmanısın. Sana verilen kaynaklara dayanarak "
        "kullanıcının sorusuna kapsamlı, akıcı ve akademik üslupta bir yanıt yaz. "
        "Kurallar:\n"
        "1. Yalnızca getirilen kaynaklara dayan; uydurma yapma.\n"
        "2. Cümle bazlı atıf kullan: '[n]' formatında, n verilen kaynak numarası.\n"
        "3. Markdown kullan: kısa giriş, alt-başlıklarla bulgular, sonuç paragrafı.\n"
        "4. citations_ieee alanını boş liste olarak bırak (sistem otomatik dolduracak).\n\n"
        "{format_instructions}\n\n"
        "ÖNEMLİ: Yalnızca tek bir JSON nesnesi döndür, başka açıklama ekleme.",
    ),
    (
        "human",
        "Soru: {question}\n\nKaynaklar:\n{chunks}",
    ),
]).partial(format_instructions=_ANSWER_PARSER.get_format_instructions())


def _strip_json_fence(text: str) -> str:
    """Remove markdown fences and surrounding prose from LLM output, keep JSON."""
    text = text.strip()
    # Try fenced ```json ... ``` block
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        return fence.group(1)
    # Otherwise: take first {...} blob
    blob = re.search(r"\{.*\}", text, re.DOTALL)
    if blob:
        return blob.group(0)
    return text


def plan_agent(question: str, api_key: str) -> Plan:
    llm = build_llm(api_key, temperature=0.1)
    raw = (PLANNER_PROMPT | llm).invoke({"question": question})
    raw_text = getattr(raw, "content", str(raw))
    try:
        return _PLAN_PARSER.parse(_strip_json_fence(raw_text))
    except Exception as e:
        raise RuntimeError(
            f"Planner output could not be parsed as Plan JSON. "
            f"Raw output (first 300 chars): {raw_text[:300]}"
        ) from e


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


def writer_agent(question: str, chunks: list[dict], api_key: str) -> FinalAnswer:
    llm = build_llm(api_key, temperature=0.3)
    raw = (WRITER_PROMPT | llm).invoke({
        "question": question,
        "chunks": format_chunks_for_writer(chunks),
    })
    raw_text = getattr(raw, "content", str(raw))
    try:
        drafted = _ANSWER_PARSER.parse(_strip_json_fence(raw_text))
    except Exception as e:
        raise RuntimeError(
            f"Writer output could not be parsed. Raw output (first 300 chars): {raw_text[:300]}"
        ) from e

    ieee = [build_ieee_citation(c, i) for i, c in enumerate(chunks, 1)]
    n_max = len(chunks)
    answer = re.sub(
        r"\[(\d+)\]",
        lambda m: m.group(0) if int(m.group(1)) <= n_max else "",
        drafted.answer_md,
    )
    return FinalAnswer(answer_md=answer, citations_ieee=ieee)


# ───────────── Orchestration ─────────────


def run_agent(question: str, api_key: str, progress=gr.Progress()):
    if not api_key or not api_key.strip():
        msg = (
            "### ⚠️ DeepSeek API key gerekli\n\n"
            "Lütfen yukarıdaki **DeepSeek API Key** kutusuna kendi key'inizi girin.\n\n"
            "API key almak için: https://platform.deepseek.com/api_keys\n\n"
            "Tahmini maliyet: sorgu başına yaklaşık **$0.005** (DeepSeek-Chat ücretlendirmesi)."
        )
        return ("", "", msg, "")

    if not question or not question.strip():
        return ("", "", "### Lütfen bir Türkçe soru girin.", "")

    progress(0.1, desc="Sorgu planlanıyor…")
    try:
        plan = plan_agent(question.strip(), api_key.strip())
    except Exception as e:
        return ("", "", f"### ❌ Plan hatası\n\n```\n{e}\n```", "")

    plan_md = "\n".join(f"- {sq.text}" for sq in plan.sub_questions)

    progress(0.4, desc="Kaynaklar aranıyor (OpenAlex + Semantic Scholar)…")
    # Use ENGLISH search terms for the APIs (they handle Turkish poorly),
    # but keep the Turkish question as a fallback.
    queries = list(plan.en_search_terms) + [question.strip()] + [sq.text for sq in plan.sub_questions]
    chunks = retrieve_live(queries, k_each=4)

    if not chunks:
        return (
            plan_md, "",
            "### ⚠️ Hiçbir kaynak bulunamadı\n\nLütfen sorguyu farklı şekilde dene.",
            "",
        )

    chunks_md = "\n\n".join(
        f"**[{i}]** ({c['source_kind']}) {c['authors']} — *{c['title']}* "
        f"({c.get('year','?')}) — {c.get('venue','')}"
        for i, c in enumerate(chunks, 1)
    )

    progress(0.75, desc="Yanıt yazılıyor…")
    try:
        final = writer_agent(question.strip(), chunks, api_key.strip())
    except Exception as e:
        return (plan_md, chunks_md, f"### ❌ Yazım hatası\n\n```\n{e}\n```", "")

    progress(1.0, desc="Bitti")
    return plan_md, chunks_md, final.answer_md, "\n".join(final.citations_ieee)


# ───────────── UI ─────────────


THEME = gr.themes.Soft(primary_hue="blue", neutral_hue="slate")

EXAMPLES = [
    "Türkçe doğal dil işlemede son yıllardaki ana yaklaşımlar nelerdir?",
    "Derin öğrenme yöntemleri Türkiye'deki sel ve taşkın tahmininde nasıl uygulanmıştır?",
    "Türkiye'de uzaktan eğitimde öğrenci motivasyonunu artıran pedagojik stratejiler nelerdir?",
    "Yenilenebilir enerji kaynaklarından rüzgar türbinlerinin Türkiye'deki potansiyeli nedir?",
    "İklim değişikliğinin Türkiye'deki tarımsal üretim üzerindeki ekonomik etkileri nelerdir?",
]


with gr.Blocks(title="TürkResearcher Demo", theme=THEME) as demo:
    gr.Markdown(
        """
        # 🔍 TürkResearcher — Türkçe Akademik Araştırma Ajanı

        **Multi-agent LLM**, OpenAlex + Semantic Scholar'dan kanıt çekerek IEEE atıflı Türkçe yanıt üretir.

        Bu demo projenin **canlı API versiyonudur** (HF Spaces sınırı). Tam 740K Türkçe tez + dergi makalesi
        indeksli versiyonu için → [GitHub repo](https://github.com/hakansabunis/tr-academic-research-agent)
        ve [HF Hub index](https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index).
        """
    )

    with gr.Row():
        api_key_box = gr.Textbox(
            label="🔑 DeepSeek API Key (kendi key'iniz)",
            type="password",
            placeholder="sk-...",
            info="Key alın: platform.deepseek.com/api_keys  ·  Tahmini maliyet: ~$0.005/sorgu  ·  Bu Space key'inizi saklamaz.",
        )

    with gr.Row():
        with gr.Column(scale=4):
            question_box = gr.Textbox(
                label="Soru (Türkçe)",
                placeholder="Örn: Türkçe doğal dil işlemede son yıllardaki ana yaklaşımlar nelerdir?",
                lines=2,
            )
        with gr.Column(scale=1, min_width=120):
            submit = gr.Button("Sor", variant="primary", size="lg")

    gr.Examples(
        examples=EXAMPLES,
        inputs=[question_box],
        label="Örnek sorular",
    )

    with gr.Tab("📝 Yanıt"):
        answer_out = gr.Markdown()
    with gr.Tab("🗂️ Plan + Kaynaklar"):
        gr.Markdown("### 1. Planner — alt sorular")
        plan_out = gr.Markdown()
        gr.Markdown("### 2. Retrieved kaynaklar")
        chunks_out = gr.Markdown()
    with gr.Tab("📚 IEEE Atıflar"):
        citations_out = gr.Markdown()

    submit.click(
        fn=run_agent,
        inputs=[question_box, api_key_box],
        outputs=[plan_out, chunks_out, answer_out, citations_out],
    )

    gr.Markdown(
        """
        ---
        **Mimari:** Planner → LiveSearch (OpenAlex + Semantic Scholar) → Writer.
        **Lisans:** MIT (kod), CC-BY-4.0 (veri).
        **Geliştirici:** [Hakan Sabuniş](https://hakansabunis.com).
        """
    )


if __name__ == "__main__":
    demo.launch()
