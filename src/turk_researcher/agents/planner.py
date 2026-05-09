from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from ..llm import build_llm
from ..schemas import GraphState, Plan

PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Sen bir Türkçe akademik araştırma asistanısın. Kullanıcının sorduğu "
        "geniş soruyu, YÖK tezleri korpusu üzerinde RAG ile cevaplanabilecek "
        "3 ile 5 arasında **özgül** alt soruya böl. Her alt soru farklı bir "
        "kavramsal açıyı kapsasın (yöntem, bulgu, sınırlılık, karşılaştırma, "
        "uygulama vb.). Çıktı sadece JSON: "
        '{{"sub_questions":[{{"text":"...","rationale":"..."}}]}}',
    ),
    ("human", "Kullanıcı sorusu: {question}"),
])


def planner_node(state: GraphState) -> GraphState:
    llm = build_llm(temperature=0.1)
    # DeepSeek doesn't support response_format=json_schema; function_calling
    # is supported and gives the same Pydantic-validated output.
    structured = llm.with_structured_output(Plan, method="function_calling")
    chain = PROMPT | structured
    plan: Plan = chain.invoke({"question": state["question"]})
    return {"plan": plan, "iteration": 0}
