# Project Proposal — TürkResearcher
### A Multi-Agent LLM Research Assistant for Turkish Academic Literature

**Student:** Hakan Sabuniş
**Course:** Large Language Models — Spring 2026
**Institution:** Istanbul Medipol University
**Track:** Track 1 — Novel Idea
**Date:** 9 May 2026

---

## 1. Problem Statement

While English-language researchers benefit from grounded, evidence-based
LLM tools such as **Elicit**, **Consensus.app**, and **scite.ai**, no
comparable system exists for the Turkish academic ecosystem. Turkish
researchers are stuck between two unsatisfactory options: general-purpose
chatbots that hallucinate confidently in Turkish, or English-only academic
search tools that ignore the Turkish corpus entirely.

This gap is significant. Turkey hosts **more than 600 active peer-reviewed
journals on DergiPark** and releases tens of thousands of theses every
year through YÖK Ulusal Tez Merkezi. None of this Turkish-language
scholarly output is accessible through current LLM-based research
assistants.

## 2. Proposed System

I propose **TürkResearcher**: an open-source, multi-agent research
assistant for Turkish academic literature, built on LangChain and
LangGraph.

Given a research question in Turkish, the agent will:

1. **Decompose** the question into 3–5 specific sub-questions
2. **Retrieve** evidence from a corpus of 500K+ Turkish thesis abstracts
   using multi-query similarity search
3. **Synthesise** the retrieved findings, flagging contradictions
4. **Self-critique** for coverage, looping back to retrieval if
   sub-questions are not adequately addressed
5. **Write** a Turkish academic answer with IEEE-style citations linked
   to public YÖK PDFs

## 3. Data

**Primary corpus.** [`umutertugrul/turkish-academic-theses-dataset`](https://huggingface.co/datasets/umutertugrul/turkish-academic-theses-dataset)
on Hugging Face Hub: a 650K-row bilingual abstract dataset under
CC-BY-4.0 licence, derived from YÖK Ulusal Tez Merkezi.

Quality filters (`abstract_tr` ≥ 50 words, non-empty title,
deduplication on `tez_no`) will retain approximately 500K–600K records
for indexing.

**Optional extension.** Turkish journal articles harvested from
**DergiPark** via the OAI-PMH protocol (`https://dergipark.org.tr/api/public/oai/`),
to broaden coverage beyond theses.

## 4. System Design

| Component | Choice | Rationale |
|---|---|---|
| Embedder | `paraphrase-multilingual-mpnet-base-v2` (768-dim) | Strong multilingual sentence representation, good Turkish coverage, modest VRAM footprint |
| Vector store | ChromaDB | Open-source, well-supported by LangChain, persistent on disk |
| Distance metric | Cosine similarity | Standard for sentence-transformer embeddings |
| LLM backbone | DeepSeek (`deepseek-chat`) | OpenAI-compatible API, strong Turkish, low cost |
| Orchestration | LangChain + LangGraph | Composable RAG primitives plus a state machine for the multi-agent loop |

The five agents (Planner, Retriever, Synthesiser, Critic, Writer) will
be wired into a directed graph with a conditional edge from Critic back
to Retriever for coverage failures.

## 5. Evaluation

A 30-question Turkish benchmark spanning ten subject categories
(computer science, education, health, engineering, social sciences,
business, agriculture, linguistics, law, multi-domain). Four
**LLM-as-judge** metrics:

- **Citation accuracy** — do cited sources actually support the claims?
- **Faithfulness** — is the generated answer grounded in retrieved context?
- **Coverage** — fraction of planned sub-questions substantively addressed
- **Holistic score (1–5)** — overall academic quality (structure, register, reasoning)

Per-category breakdown will surface domains where the system performs
well versus domains where corpus coverage limits performance, supporting
an honest analysis of where Turkish academic NLP infrastructure is strong
and where gaps remain.

## 6. Deliverables

1. **GitHub repository** under MIT licence, with reproducible pipeline
   (`pip install`-and-go) and full eval harness.
2. **Public Hugging Face Hub dataset** hosting the prebuilt vector index,
   so anyone cloning the repo can reproduce the system without rebuilding
   the index from scratch.
3. **IEEE-format academic report** (2–6 pages): abstract, introduction,
   related work, methodology, experiments, discussion / error analysis,
   conclusion.
4. **10–15 minute class presentation** with a live demo.

## 7. Timeline

| Phase | Weeks |
|---|---|
| Data pipeline (fetch, filter, embed, index) | 1–2 |
| Multi-agent system design and integration | 3 |
| Evaluation framework and analysis | 4 |
| Report and presentation | 5 |

## 8. Why this is novel

To the best of my knowledge, **TürkResearcher would be the first
open-source multi-agent academic research assistant for Turkish**.
The novelty lies not in inventing new model architectures, but in
combining state-of-the-art LLM orchestration techniques with a
language-specific academic corpus that has been largely invisible to
the modern LLM ecosystem — and in doing so openly, with full
reproducibility.
