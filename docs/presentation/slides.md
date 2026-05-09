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

## Results — Two Corpus Configurations

We evaluate twice: 633K thesis-only vs 740K (+ 106K DergiPark articles).

| Metric | 633K | 740K | Δ |
|---|---|---|---|
| Citation accuracy | **0.60** | 0.51 | -0.10 |
| Faithfulness | **0.59** | 0.49 | -0.10 |
| Coverage | 0.49 | 0.47 | -0.03 |
| Holistic (1–5) | **2.63** | 2.40 | -0.23 |
| #Citations | 30.1 | **32.8** | +2.7 |
| Latency (s) | 105.8 | 111.4 | +5.6 |

**30/30 successful** in both runs. **Counter-intuitive:** more data ≠ better metrics.

---

## The Corpus-Expansion Paradox

| Category | n | 633K → 740K | |
|---|---|---|---|
| 🟢 business | 2 | 0.47 → 0.68 | **+0.20** |
| 🟢 computer_science | 4 | 0.21 → 0.26 | **+0.05** |
| 🔴 social_sciences | 2 | 0.78 → 0.70 | -0.08 |
| 🔴 education | 3 | 0.75 → 0.63 | -0.12 |
| 🔴 multi_domain | 2 | 0.85 → 0.70 | -0.15 |
| 🔴 engineering | 3 | 0.73 → 0.53 | -0.20 |
| 🔴 law | 2 | 0.62 → 0.40 | -0.22 |
| 🔴 health | 3 | 0.80 → 0.53 | -0.27 |

**Pattern:** under-served domains improved; well-covered domains regressed.

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

## Why CS Fails (633K corpus)

**1. "Türkçe" lexical confound** — query "Türkçe doğal dil işleme" → top hits are theses about *the Turkish language itself* (phonology, dialectology), not NLP.

**2. Corpus skew** — Turkish CS researchers publish predominantly in English; YÖK is filtered to TR abstracts only.

DergiPark partially fixed this (+0.05). OpenAlex has 1.16M TR papers — even bigger lever.

---

## Why Naive Expansion Hurt Other Domains

Three contributing factors:

1. **Abstract length shift.** Theses ≈ 1600 chars, journal articles ≈ 500 chars. Less surface to ground claims.

2. **Citation inflation.** Writer agent produces +2.7 more citations per answer; each extra citation is weaker.

3. **Source-mixing without source-aware writing.** Thesis claims are broad-coherent; journal claims are narrow-empirical. Writer prompt doesn't yet distinguish them.

→ **Take-away:** corpus expansion is *not* a free win. Need source-aware retrieval + writer.

---

## Limitations

- **Abstract-only retrieval** — full-text not indexed
- **Single LLM judge** — cross-judge agreement not measured (high variance)
- **Naive corpus expansion regressed well-covered domains** (paradox finding)
- **Latency 100–150 s** — sequential agent calls; could parallelise
- **No source-aware writing** — writer prompt unaware of thesis vs article rhetorical role

---

## Future Work — Near-term

- **Full-text** indexing via DergiPark PDF extraction
- **Cross-judge** evaluation (DeepSeek + Claude + GPT)
- **Latency**: parallel sub-question retrieval, Planner cache
- **Production**: web UI, conversational memory
- **Domain filters**: per-subject specialised collections

---

## Future Work — TürkResearcher-7B

> The same data is enough to train a domain-specific Turkish academic LLM.

| Stage | What | Cost | Output |
|---|---|---|---|
| **1** | Custom embedder (SimCSE on 633K abstracts) | T4 ~3–5 h | +15-25% retrieval |
| **2** | Synthetic 100–200K Q&A → QLoRA on Turkish 7B base | A100 ~6–12 h | `TürkResearcher-7B-instruct` |
| **3** | DPO using eval judgments as preference pairs | A100 ~6 h | Aligned, citation-honest |

→ End artefact: an **open-source Turkish academic LLM** — first of its kind. Strong fit for TÜBİTAK / YÖK initiatives and a natural MSc thesis continuation.

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
