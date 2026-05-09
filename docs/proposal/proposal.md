# Project Proposal — TürkResearcher
### A Multi-Agent LLM Research Assistant for Turkish Academic Literature

**Student:** Hakan Sabuniş
**Course:** Large Language Models — Spring 2026
**Institution:** Istanbul Medipol University
**Track:** Track 1 — Novel Idea
**Date:** 9 May 2026

---

## 1. Problem & Motivation

English-language researchers benefit from grounded, evidence-based LLM
tools such as **Elicit**, **Consensus.app**, and **scite.ai**. None of
these systems serve the Turkish academic ecosystem. Turkey hosts more
than 600 active peer-reviewed journals on DergiPark and releases tens
of thousands of theses every year through YÖK Ulusal Tez Merkezi, yet
this Turkish-language scholarly output is invisible to current
LLM-based research assistants.

The novelty is therefore not architectural in isolation, but in
combining state-of-the-art LLM orchestration techniques with a
language-specific academic corpus that has been largely missing from
the modern LLM ecosystem.

## 2. System Architecture

The system is a directed-graph LangGraph state machine of six nodes
orchestrated by LangChain primitives. State is carried through typed
Pydantic objects; transitions between nodes are deterministic except
for one conditional edge from the Critic that branches based on
coverage assessment and an iteration counter.

The pipeline begins with a Turkish question and proceeds through five
LLM-using agents. The **Planner** decomposes the question into 3–5
targeted sub-questions. The **Retriever** issues a multi-query search
over the indexed corpus and returns the top-ranked chunks. The
**Synthesiser** clusters retrieved evidence into findings and flags
contradictions. The **Critic** assesses whether the planner's
sub-questions are adequately covered: if not, control loops back to
the Retriever (bounded to two iterations) or, after the second
failure, falls through to an optional **LiveSearch** node that calls
external academic APIs as a final fallback. The **Writer** then
produces the Turkish academic answer with IEEE-style citations.

Three architectural decisions shape this design. First, state is
modelled as a typed structure with reducer functions on append-style
fields, so retrieval iterations accumulate chunks rather than
overwriting them. Second, every LLM node uses schema-enforced output
through the OpenAI function-calling protocol, which DeepSeek supports
natively (DeepSeek does not support OpenAI's newer `json_schema`
response format). Third, the critic loop is bounded to a maximum of
two iterations, after which the system falls through to either the
live-search fallback or directly to the writer, preventing runaway
retrieval cycles.

## 3. Component Specifications

### 3.1 Embedding layer

| Property | Value | Rationale |
|---|---|---|
| Model | paraphrase-multilingual-mpnet-base-v2 | 768-dim multilingual sentence transformer; XLM-RoBERTa backbone with strong Turkish coverage |
| Document representation | Title concatenated with abstract | Title-aware indexing adds a strong lexical signal that abstract-only embeddings miss |
| Normalisation | L2 | Required for cosine similarity to be a valid metric |
| Inference target | CPU at query time | Local agent runs without GPU; ~50 ms per query after first load |

Alternatives considered and rejected: BERTurk-base (Turkish-only but
optimised for token-level NER, not sentence representation);
distiluse-multilingual (512-dim, faster but lower retrieval quality);
custom SimCSE fine-tune (deferred to future work).

### 3.2 Vector indexing

| Property | Value | Rationale |
|---|---|---|
| Backend | ChromaDB persistent client | Python-native, persistent on disk, mature LangChain integration |
| Index | HNSW with M=16 and ef_construction=200 | Sub-second similarity search on more than one hundred thousand vectors |
| Distance | Cosine | Standard for L2-normalised sentence embeddings |
| Identifier scheme | Thesis records use the YÖK identifier; journal records use an article prefix | Globally unique; supports source-aware filtering downstream |
| Metadata stored per chunk | Thirteen fields including author, advisor, location, year, subject, PDF URL, language, source type | Sufficient to construct IEEE citations without re-querying the source parquet |

Alternatives considered: FAISS (faster but no built-in persistence
abstraction); Weaviate or Pinecone (managed services, conflicting with
the "runs on a laptop" requirement).

### 3.3 LLM integration layer

The system uses DeepSeek's `deepseek-chat` model accessed through its
OpenAI-compatible REST endpoint. LangChain's `ChatOpenAI` wrapper is
configured with an overridden base URL so that the same client library
serves both vendors. Structured outputs are produced via the
function-calling protocol, since DeepSeek does not yet support the
newer `json_schema` response format. Per-agent temperature is tuned
deterministically: the Critic runs at zero temperature for stable
coverage decisions, the Planner at 0.1 for diverse but focused
sub-questions, the Synthesiser at 0.2, and the Writer at 0.3 for
fluent academic prose. Each agent node receives a Pydantic schema and
produces a validated instance of that schema, eliminating brittle JSON
parsing.

### 3.4 Retrieval strategy

The retriever runs the original question alongside each planner
sub-question, producing four to six independent queries per turn. For
each query, the top six chunks are retrieved by cosine similarity. The
results are deduplicated globally by their thesis identifier, with the
maximum similarity score retained when the same chunk appears across
multiple queries. The deduplicated set is truncated to the top
twenty-four chunks before being passed to the synthesiser. Cosine
distance returned by ChromaDB is converted to a similarity score in
the unit interval for downstream interpretability.

### 3.5 Citation subsystem

The writer emits inline numeric markers in Turkish prose, where each
number indexes one of the retrieved chunks delivered as context. The
IEEE reference list itself is constructed deterministically by the
system from chunk metadata (author, title, location, year, public PDF
URL), not by the LLM. This split keeps the writer free to reason about
narrative while guaranteeing that every reference resolves to a real
public URL on `tez.yok.gov.tr`. A post-processing safety check filters
any numeric marker that exceeds the available chunk count, preventing
hallucinated references from leaking into the final answer.

## 4. Data Pipeline

The corpus originates from `umutertugrul/turkish-academic-theses-dataset`
on Hugging Face Hub, a 650K-row bilingual abstract dataset under
CC-BY-4.0. The pipeline first fetches the raw parquet via the
`datasets` library. A filter stage then enforces three quality
criteria: each abstract must be at least fifty words, the Turkish
title must be non-empty, and duplicate thesis identifiers are
collapsed. The retained 500K–600K records are embedded with mpnet on
a Colab T4 GPU at batch size 256, then ingested into a Chroma
collection configured for cosine similarity. The persistent index is
uploaded as a public Hugging Face dataset, allowing any consumer to
reproduce the runtime by pulling the prebuilt index rather than
rebuilding it from scratch.

## 5. Evaluation Framework

A 30-question Turkish academic benchmark spans ten subject categories:
computer science, education, health, engineering, social sciences,
business, agriculture, linguistics, law, and multi-domain queries.
Four LLM-as-judge metrics are computed per question.

| Metric | Range | Captures |
|---|---|---|
| Citation accuracy | 0 to 1 | Whether cited chunks support the surrounding claim |
| Faithfulness | 0 to 1 | Whether every claim is grounded in retrieved context |
| Coverage | 0 to 1 | Fraction of planner sub-questions substantively addressed |
| Holistic | 1 to 5 | Overall academic quality (structure, register, reasoning) |

Mechanical metrics are also captured: end-to-end latency,
retrieved-chunk count, maximum cosine similarity, and critic
iteration count. A per-category breakdown surfaces domains where the
corpus is strong versus weak, supporting honest error analysis rather
than a single blended number.

## 6. Reproducibility & Deployment

All code will be released under MIT licence on GitHub. The prebuilt
Chroma index will be published as a public Hugging Face dataset so
that any consumer can reproduce the system end-to-end without
rebuilding the index. The runtime is designed to be a three-step
flow: install dependencies from the pinned requirements file, pull
the prebuilt index from Hugging Face Hub via a single helper script,
then run the agent CLI with a Turkish question.

## 7. Timeline

| Phase | Weeks | Output |
|---|---|---|
| Data pipeline (fetch, filter, embed, index, push) | 1–2 | Indexed Chroma collection on HF Hub |
| Multi-agent system implementation (LangGraph nodes, Pydantic schemas, citation subsystem) | 3 | Runnable agent CLI |
| Evaluation framework (benchmark questions, judge prompts, summary aggregation) | 4 | Quantitative results table |
| Academic report (IEEE 2–6 pages) and class presentation | 5 | PDF and slide deck |

## 8. Expected Deliverables

1. GitHub repository under MIT licence with reproducible pipeline
   and full evaluation harness.
2. Public Hugging Face dataset hosting the prebuilt vector index.
3. IEEE-format academic report (2–6 pages): abstract, introduction,
   related work, methodology, experiments, discussion / error analysis,
   conclusion.
4. 10–15 minute class presentation with a live demo.
