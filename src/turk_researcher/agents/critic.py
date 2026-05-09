from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from ..llm import build_llm
from ..schemas import CriticReport, GraphState

PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Sen bir akademik gözden geçirme uzmanısın. Bir araştırma sentezini "
        "kapsam ve sağlamlık açısından eleştirel bir gözle değerlendir. "
        "Kullanıcının sorusundaki hangi alt-açıların örtülmediğini tespit et. "
        "Eğer ek arama (re-query) gerekiyorsa, korpusta arama yapmaya uygun "
        "**Türkçe** anahtar kelime/öbekleri öner — soyut değil somut. "
        "Coverage zaten yeterliyse coverage_ok=true ver ve requery_terms boş "
        "bırak. Çıktı JSON: "
        '{{"coverage_ok":true,"missing_aspects":["..."],"requery_terms":["..."],"notes":"..."}}',
    ),
    (
        "human",
        "Soru: {question}\n\nMevcut sentez:\n{synthesis}\n\nİterasyon: {iteration}",
    ),
])


def _fmt_synth(synthesis) -> str:
    if synthesis is None:
        return "(henüz sentez yok)"
    out = []
    for f in synthesis.findings:
        out.append(f"- {f.claim}  [src: {', '.join(f.citations) or '-'}]")
    if synthesis.contradictions:
        out.append("Çelişkiler:")
        out.extend(f"  ! {c}" for c in synthesis.contradictions)
    return "\n".join(out)


def critic_node(state: GraphState) -> GraphState:
    llm = build_llm(temperature=0.0)
    chain = PROMPT | llm.with_structured_output(CriticReport, method="function_calling")
    report: CriticReport = chain.invoke({
        "question": state["question"],
        "synthesis": _fmt_synth(state.get("synthesis")),
        "iteration": state.get("iteration", 0),
    })
    return {
        "critic": report,
        "iteration": state.get("iteration", 0) + 1,
    }
