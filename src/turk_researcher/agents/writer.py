from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from ..llm import build_llm
from ..schemas import FinalAnswer, GraphState, RetrievedChunk


def _ieee_citation(c: RetrievedChunk, idx: int) -> str:
    """Build a single IEEE-style reference for a Turkish thesis."""
    parts = [f"[{idx}] {c.author},"]
    parts.append(f'"{c.title_tr},"')
    parts.append("Yüksek Lisans/Doktora tezi,")
    if c.location:
        parts.append(f"{c.location},")
    if c.year:
        parts.append(f"{c.year}.")
    if c.pdf_url:
        parts.append(f"[Online]. {c.pdf_url}")
    return " ".join(parts).strip()


def _format_chunks_for_writer(chunks: list[RetrievedChunk]) -> tuple[str, list[str]]:
    """Return (chunks_block, ieee_list). The chunks_block is what the LLM sees,
    keyed by [n] which match the IEEE numbers."""
    text_lines: list[str] = []
    ieee_list: list[str] = []
    for i, c in enumerate(chunks, 1):
        text_lines.append(
            f"[{i}] (tez_no={c.tez_no}) {c.author} ({c.year or '?'}) — "
            f"{c.title_tr}\n    {c.abstract_tr[:500]}"
        )
        ieee_list.append(_ieee_citation(c, i))
    return "\n\n".join(text_lines), ieee_list


PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Sen Türkçe akademik yazım uzmanısın. Sana verilen bulguları "
        "kullanarak kullanıcı sorusuna kapsamlı, akıcı ve **akademik üslupta** "
        "bir yanıt yaz. Kurallar:\n"
        "1. Yalnızca getirilen kaynaklara dayan — hallüsinasyon yapma.\n"
        "2. Cümle bazlı atıf kullan: '[n]' formatında, n verilen kaynağın numarasıdır.\n"
        "3. Çelişkili bulgular varsa açıkça belirt.\n"
        "4. Çıktıyı Markdown akademik özet olarak yaz: kısa giriş, "
        "  alt-başlıklarla bulgular, sonuç paragrafı.\n"
        "5. Sonunda 'Kaynaklar' bölümü EKLEME — sistem otomatik ekleyecek.\n"
        "Çıktı JSON: "
        '{{"answer_md":"...","citations_ieee":[]}} '
        "(citations_ieee'yi boş bırak; sistem dolduracak)",
    ),
    (
        "human",
        "Soru: {question}\n\nBulgular sentezi:\n{synthesis}\n\nKaynaklar:\n{chunks}",
    ),
])


def _fmt_synth(synthesis) -> str:
    if synthesis is None:
        return "(boş)"
    out = []
    for f in synthesis.findings:
        out.append(f"- {f.claim} (kaynak: {', '.join(f.citations) or '-'})")
    if synthesis.contradictions:
        out.append("\nÇelişkiler:")
        out.extend(f"  ! {c}" for c in synthesis.contradictions)
    return "\n".join(out)


def writer_node(state: GraphState) -> GraphState:
    chunks = state.get("chunks", [])
    chunks_block, ieee_list = _format_chunks_for_writer(chunks)
    llm = build_llm(temperature=0.3)
    chain = PROMPT | llm.with_structured_output(FinalAnswer, method="function_calling")
    drafted: FinalAnswer = chain.invoke({
        "question": state["question"],
        "synthesis": _fmt_synth(state.get("synthesis")),
        "chunks": chunks_block,
    })
    final = FinalAnswer(answer_md=drafted.answer_md, citations_ieee=ieee_list)
    return {"final": final}
