from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from ..llm import build_llm
from ..schemas import GraphState, Synthesis


def _format_chunks(chunks) -> str:
    lines = []
    for i, c in enumerate(chunks, 1):
        head = f"[{i}] tez_no={c.tez_no} | {c.author} ({c.year}) — {c.title_tr}"
        body = c.abstract_tr[:600].replace("\n", " ")
        lines.append(f"{head}\n{body}")
    return "\n\n".join(lines)


PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Türkçe akademik bulguları sentezleyen bir araştırma asistanısın. "
        "Sana getirilen tez özetlerini analiz et, tutarlı bulgular (findings) "
        "çıkar ve aralarındaki çelişkileri ayrı bir alanda listele. Her "
        "bulgunun `citations` alanına o bulguyu destekleyen kaynakların "
        "tez_no'larını yaz. Uydurma yapma — sadece getirilen kaynaklara "
        "dayan. Çıktı JSON: "
        '{{"findings":[{{"claim":"...","citations":["..."],"supporting_chunks":[1,2]}}],'
        '"contradictions":["..."]}}',
    ),
    (
        "human",
        "Soru: {question}\n\nGetirilen kaynaklar:\n{chunks}",
    ),
])


def synthesizer_node(state: GraphState) -> GraphState:
    llm = build_llm(temperature=0.2)
    chain = PROMPT | llm.with_structured_output(Synthesis, method="function_calling")
    synthesis: Synthesis = chain.invoke({
        "question": state["question"],
        "chunks": _format_chunks(state.get("chunks", [])),
    })
    return {"synthesis": synthesis}
