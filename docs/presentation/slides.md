---
marp: true
theme: gaia
paginate: true
class: lead
backgroundColor: #fff
---

<!-- _class: lead -->

# **TürkResearcher**

### A LangGraph Multi-Agent Research Assistant
### Grounded in 633K Turkish Theses

**Hakan Sabuniş** · İstanbul Medipol Üniversitesi
**LLM Final Project — Track 1 (Novel Idea)**

`hakansabunis/tr-academic-research-agent-index`

---

## The Gap

**Elicit, Consensus.app, scite.ai** revolutionised English academic search.

For Turkish? **Nothing comparable exists.**

- 600+ active Turkish journals on DergiPark
- Tens of thousands of theses on YÖK Ulusal Tez Merkezi
- Researchers stuck between hallucinating chatbots and English-only tools

> **TürkResearcher** fills this gap with grounded, citation-supported
> Turkish academic answers.

---

## Demo Question

> **"Türkçe doğal dil işlemede son yıllardaki ana yaklaşımlar nelerdir?"**

The agent:
1. Decomposes into 5 sub-questions
2. Retrieves 30 relevant theses from a 633K corpus
3. Synthesises findings, flags contradictions
4. Critic checks coverage; loops if needed
5. Drafts a Turkish academic answer with **38 IEEE citations**

Latency: ~60–90 s · End-to-end DeepSeek API + local Chroma

---

## Architecture

```
            Question (TR)
                 │
                 ▼
      ┌─────────────────────┐
      │      PLANNER        │  3–5 sub-questions
      └─────────────────────┘
                 │
                 ▼
      ┌─────────────────────┐
      │     RETRIEVER       │  multi-query over Chroma (633K)
      └─────────────────────┘
                 │
                 ▼
      ┌─────────────────────┐
      │    SYNTHESISER      │  cluster + contradictions
      └─────────────────────┘
                 │
                 ▼
      ┌─────────────────────┐    coverage_ok=False
      │       CRITIC        │ ─────────────────────► RETRIEVER (loop ≤2)
      └─────────────────────┘                         or LIVE_SEARCH
                 │ coverage_ok=True                   (OpenAlex / SS / DergiPark)
                 ▼
      ┌─────────────────────┐
      │       WRITER        │  IEEE-cited Turkish answer
      └─────────────────────┘
```

`LangGraph` state machine · 5 LLM nodes · 1 retrieval node · 1 live-search node

---

## Data Pipeline

| Stage | Input | Tool | Output |
|---|---|---|---|
| **Fetch** | HF Hub: `umutertugrul/turkish-academic-theses-dataset` | `datasets` | 650K rows |
| **Filter** | abstract ≥ 50 words, dedup by tez_no | pandas | **633.998** rows |
| **Embed** | title + abstract (concat) | mpnet-base-v2 (768-dim) | Chroma + cosine |
| **Push** | 14.8 GB index | `huggingface_hub` | `hakansabunis/tr-academic-research-agent-index` |

Built on **Colab T4/A100**, ~6 hours · Released openly for reproducibility.

---

## Why Title-Aware Embedding Mattered

| Query | Old index (abstract-only, L2) | New index (title+abstract, cosine) |
|---|---|---|
| "derin öğrenme sel tahmini" | ❌ AHP karar verme yöntemi | ✅ Makine öğrenimi akım tahmini |
| "Türkçe NLP yöntemleri" | ❌ Türkçe ikinci dil edinimi | ✅ Türkçe gövdeleme yöntemi |
| "kalp damar teşhis" | ✅ kalp ses analizi | ✅ kalp ekokardiyografi |

**Title contributes a strong lexical signal** that pure-abstract indexing misses.

---

## Multi-Agent Pipeline (Detail)

| Agent | Role | LLM Output |
|---|---|---|
| **Planner** | decompose question | `Plan { sub_questions[] }` |
| **Retriever** | multi-query Chroma | `RetrievedChunk[]` (top-24, dedup) |
| **Synthesiser** | cluster findings | `Synthesis { findings, contradictions }` |
| **Critic** | check coverage | `CriticReport { coverage_ok, missing, requery_terms }` |
| **Writer** | draft + IEEE refs | `FinalAnswer { answer_md, citations_ieee }` |

All structured via `with_structured_output(method="function_calling")` (DeepSeek-compatible).

---

## Live API Tools (Hybrid RAG)

When local corpus is insufficient, the **Critic** routes to `live_search`:

| Tool | Endpoint | Strength |
|---|---|---|
| **OpenAlex** | `api.openalex.org/works` | 250M works, real Turkish authors |
| **Semantic Scholar** | `api.semanticscholar.org/graph/v1/paper/search` | Recent (2024-2025), citation graph |
| **DergiPark** | OAI-PMH `/api/public/oai/` | Latest Turkish journal articles |

→ Static 633K corpus + dynamic real-time augmentation

---

## DergiPark OAI-PMH Harvest

Beyond theses, we harvest Turkish journal articles via the official
**OAI-PMH** endpoint:

```
GET https://dergipark.org.tr/api/public/oai/
    ?verb=ListRecords&metadataPrefix=oai_dc
    &resumptionToken=<state>
```

- **Resumable**, polite (0.4 s delay), retry-on-429
- 100 records per page × ~2 537 active journals
- **100K+ articles harvested** so far, embedding pending

Code: `scripts/05_harvest_dergipark.py`

---

## Evaluation

**30 Turkish questions** spanning 10 subject categories:
Computer Science · Education · Health · Engineering · Social Sciences ·
Business · Agriculture · Veterinary · Linguistics · Law · Sciences

**LLM-as-judge metrics** (DeepSeek):
- **Citation accuracy** (0–1): cited tez supports the claim?
- **Faithfulness** (0–1): is the answer grounded?
- **Coverage** (0–1): are sub-questions addressed?
- **Holistic score** (1–5): overall academic quality

---

## Results

<!-- TODO: replace with actual numbers from data/eval/summary.json -->

| Metric | Mean | Median | Min | Max |
|---|---|---|---|---|
| Citation accuracy | TBD | TBD | TBD | TBD |
| Faithfulness | TBD | TBD | TBD | TBD |
| Coverage | TBD | TBD | TBD | TBD |
| Holistic (1–5) | TBD | TBD | TBD | TBD |
| #Citations | TBD | TBD | TBD | TBD |
| Latency (s) | 46 | 78 | 46 | 90 |

---

## Live Demo

```bash
.\.venv\Scripts\python.exe scripts\run.py \
  "Türkçe doğal dil işlemede son trendler nelerdir?" \
  --show-trace
```

Generates:
- 5-question plan
- 30 retrieved theses (top score ~0.94 cosine sim)
- 9-section academic article
- 38 IEEE references with `tez.yok.gov.tr` URLs

---

## Limitations

- **Abstract-only retrieval** — full-text not indexed
- **Single LLM judge** — cross-judge agreement not measured
- **Static rebuild cycle** — live tools partially address this
- **Latency 60–90 s** — sequential agent calls; could parallelise
- **DergiPark live search** — OAI-PMH date filter is coarse

---

## Future Work

- **Full-text** indexing via DergiPark PDF extraction
- **Cross-judge** evaluation (DeepSeek + Claude + GPT) for inter-rater agreement
- **Latency**: parallel sub-question retrieval, Planner cache
- **Production**: web UI, conversational memory, user feedback loop
- **Domain filters**: per-subject specialised collections (Law, Medicine, etc.)

---

## Reproducibility

Everything open:

- **Code**: GitHub repo (final push pending)
- **Data**: `umutertugrul/turkish-academic-theses-dataset` (CC-BY-4.0)
- **Index**: `hakansabunis/tr-academic-research-agent-index` (14.8 GB)
- **Eval set**: `data/eval/questions.json` (30 questions)
- **Report**: IEEE LaTeX + BibTeX in `docs/report/`

Single command from clean repo:
```bash
pip install -r requirements.txt
python scripts/04_pull_index_from_hub.py
python scripts/run.py "<question in Turkish>"
```

---

<!-- _class: lead -->

## Thank you

**TürkResearcher** — first open multi-agent research assistant for Turkish.

`hakansabunis@gmail.com`
`https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index`

Questions?
