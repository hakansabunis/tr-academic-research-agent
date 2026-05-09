from __future__ import annotations

from typing import Annotated, TypedDict

from pydantic import BaseModel, Field


class SubQuestion(BaseModel):
    text: str = Field(..., description="Türkçe alt soru")
    rationale: str = Field("", description="Neden bu alt soru sorulmalı")


class Plan(BaseModel):
    sub_questions: list[SubQuestion]


class RetrievedChunk(BaseModel):
    tez_no: str
    title_tr: str
    author: str
    year: int | None = None
    advisor: str | None = None
    location: str | None = None
    abstract_tr: str
    score: float = 0.0
    pdf_url: str | None = None


class Finding(BaseModel):
    claim: str
    citations: list[str] = Field(default_factory=list)
    supporting_chunks: list[int] = Field(default_factory=list)


class Synthesis(BaseModel):
    findings: list[Finding]
    contradictions: list[str] = Field(default_factory=list)


class CriticReport(BaseModel):
    coverage_ok: bool
    missing_aspects: list[str] = Field(default_factory=list)
    requery_terms: list[str] = Field(default_factory=list)
    notes: str = ""


class FinalAnswer(BaseModel):
    answer_md: str
    citations_ieee: list[str]


def _merge_chunks(left: list[RetrievedChunk], right: list[RetrievedChunk]) -> list[RetrievedChunk]:
    seen: dict[str, RetrievedChunk] = {c.tez_no: c for c in left}
    for c in right:
        if c.tez_no not in seen:
            seen[c.tez_no] = c
    return list(seen.values())


class GraphState(TypedDict, total=False):
    """LangGraph state for the research pipeline."""
    question: str
    plan: Plan
    chunks: Annotated[list[RetrievedChunk], _merge_chunks]
    synthesis: Synthesis
    critic: CriticReport
    iteration: int
    final: FinalAnswer
