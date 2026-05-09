# TürkResearcher — 8-Week Post-Capstone Roadmap

> *From DeepSeek-API-bound RAG to a fully offline, open-source Turkish
> academic research LLM.*

This roadmap covers the work planned **after** the LLM course delivery. The
Capstone version of TürkResearcher is the v0 baseline — what follows is the
research-grade follow-up, designed to fit a typical MSc research timeline
(~8 weeks active) and to produce publishable artefacts at every stage.

---

## TL;DR

We currently have a working RAG agent over 740K Turkish academic abstracts
that calls DeepSeek for reasoning. Three stages turn this into a
self-contained, domain-specialised Turkish academic LLM:

| Stage | Focus | Time | Cost | Artefact |
|---|---|---|---|---|
| **0** | Capstone delivery | 1 week | — | Report PDF, slides PDF, TEAMS upload |
| **1** | Custom embedder | 2 weeks | ~$2 | `trakad-embed-v2` |
| **2** | SFT model | 4 weeks | ~$130-160 | `TürkResearcher-7B-instruct` |
| **3** | DPO alignment | 1 week | ~$10-30 | `TürkResearcher-7B-instruct-dpo` |

End-state: 5 open Hugging Face artefacts, 1 GitHub repo, 1 workshop paper
candidate.

---

## Mental model — the library analogy

The system is a **library with 740K Turkish academic books**:

- **Librarian** = the embedder (decides which books are relevant to a query)
- **Writer** = the LLM (reads the chosen books and writes the answer)
- **Books** = thesis + journal abstracts already indexed in Chroma

| Component | Today (v0) | After Stage 1 | After Stage 2 | After Stage 3 |
|---|---|---|---|---|
| Librarian | mpnet generic | `trakad-embed-v2` | `trakad-embed-v2` | `trakad-embed-v2` |
| Writer | DeepSeek API (rented) | DeepSeek API | `TürkResearcher-7B` (own) | `TürkResearcher-7B-dpo` |
| Cost / query | ~$0.005 | ~$0.005 | $0 (local) | $0 (local) |
| Offline? | No | No | **Yes** | **Yes** |
| Citation accuracy target | 0.51-0.60 | ≥ 0.70 | ≥ 0.75 | ≥ 0.80 |

We are **not** doing NER. NER (Named Entity Recognition) was the focus of an
earlier project (`tr-academic-nlp/trakad-ner-v1`); it is unrelated to this
roadmap.

---

## Stage 1 — Custom Embedder *(Weeks 1-2)*

### Goal

Replace the generic `paraphrase-multilingual-mpnet-base-v2` with a
domain-specialised embedder that understands Turkish academic register.

### Method

`MultipleNegativesRankingLoss` with **subject-aware hard negatives**:

```python
for thesis in 633k_filtered:
    anchor    = thesis.title_tr
    positive  = thesis.abstract_tr
    hard_neg  = sample_from_same_subject(
                    subject=thesis.subject,
                    exclude_id=thesis.tez_no
                ).abstract_tr
    yield InputExample(texts=[anchor, positive, hard_neg])
```

Why this is robust against the SimCSE collapse seen in the previous attempt
(`tr-academic-nlp/models/embed/train.py`):

- Larger effective batch size on T4 (64 vs the previous 8)
- Hard negatives provide stronger gradient signal than in-batch negatives alone
- `MultipleNegativesRankingLoss` is the standard sentence-transformers
  recipe and well-validated against collapse

### Configuration

| Parameter | Value |
|---|---|
| Base | `paraphrase-multilingual-mpnet-base-v2` (768-dim) |
| Loss | `MultipleNegativesRankingLoss` |
| Data | 633K thesis (title, abstract, hard_neg) triplets |
| Batch | 64 (Colab T4 16 GB) |
| Epochs | 1-2 |
| LR | 2e-5 |
| Hardware | Colab T4 |
| Wall time | ~3 hours |

### Week 1

- Day 1-2: write `models/embed/train_simcse.py` and Colab notebook
- Day 3: smoke run on 10K sample (~15 min)
- Day 4: full run on 633K (~3 hours)
- Day 5: push `hakansabunis/trakad-embed-v2` to HF Hub

### Week 2

- Day 1: rebuild Chroma index with new embedder (~1 hour on T4) → push
  `tr-academic-research-agent-index-v2`
- Day 2: re-run the 30-question eval + judge + summary
- Day 3-4: comparison report, draft blog post
- Day 5: **Go/No-Go decision** — proceed to Stage 2 only if retrieval
  recall@5 improves by ≥ 15% relative over mpnet

### Targets

| Metric | Current | Target |
|---|---|---|
| Citation accuracy | 0.51-0.60 | **≥ 0.70** |
| CS-category citation accuracy | 0.21 → 0.26 | **≥ 0.40** |
| Retrieval recall@5 | baseline | **+15% relative** |

### Risk

Low. If `MultipleNegativesRankingLoss` with subject-aware hard negatives
underperforms, the fallback is plain `MultipleNegativesRanking` without
hard negatives (still expected to beat the generic mpnet baseline by a
smaller margin).

---

## Stage 2 — SFT model *(Weeks 3-6)*

### Goal

Replace the rented DeepSeek API with our own 7B Turkish academic LLM that
runs locally.

### Sub-stage 2a — Synthetic Q&A dataset *(Weeks 3-4)*

For every thesis abstract, prompt DeepSeek to produce 2 grounded
question-answer pairs:

```
You are a Turkish academic Q&A trainer.

Given the abstract below, produce 2 specific Turkish academic questions.
For each, return:
  - question:        precise, academic register
  - evidence_excerpt: a quoted span from the abstract
  - grounded_answer: 2-3 sentences, only relying on the evidence
  - citation:        in [1] format
Output JSON.
```

| Field | Value |
|---|---|
| Source | 50K randomly-sampled theses (so 100K Q&A pairs total) |
| Filter | DeepSeek confidence ≥ 0.8, ≥ 1 citation per answer |
| Length | answer 50-300 tokens |
| Dedup | Jaccard < 0.7 between question pairs |
| Format | Alpaca-style `{instruction, input, output}` |
| Cost | ~$130 (DeepSeek API) |
| Output | `hakansabunis/turk-researcher-qa-100k` (HF dataset, CC-BY-4.0) |

### Sub-stage 2b — QLoRA fine-tune *(Weeks 5-6)*

| Parameter | Value |
|---|---|
| Base model | `Trendyol/Trendyol-LLM-7B-base-v4.0` (Apache 2.0) |
| Quantisation | 4-bit NF4 |
| LoRA rank | 16 |
| LoRA alpha | 32 |
| Target modules | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` |
| Epochs | 2 |
| LR | 2e-4 (cosine schedule, 3% warmup) |
| Effective batch | 16 (per-device 4 × accum 4) |
| Optimizer | `paged_adamw_32bit` |
| Hardware | Colab Pro+ A100 |
| Wall time | 6-12 hours |
| Output | `hakansabunis/turkresearcher-7b-instruct` (~70 MB adapter) |

### Why Trendyol-LLM-7B-base?

- Pre-trained on a large Turkish corpus by Trendyol (e-commerce + crawl) —
  sound Turkish grammar and vocabulary
- Apache 2.0 license (commercially redistributable)
- 7B fits in 4 GB VRAM after 4-bit quantisation, so the final model runs
  on consumer hardware (RTX 3050 Ti at ~10-15 tokens/s)

Backup candidates: `Cosmos-LLaMa-Turkish-8B`, `Qwen2.5-7B-Instruct`,
`Llama-3.2-3B-Instruct` (lighter alternative).

### Targets

| Metric | DeepSeek API baseline | TürkResearcher-7B-SFT target |
|---|---|---|
| Holistic score (1-5) | 2.4-2.6 | **≥ 3.5** |
| Citation accuracy | 0.51-0.60 | **≥ 0.75** |
| Hallucination rate | unknown | < 10% |
| Per-query cost | $0.005 | **$0** |
| Local inference | n/a | **≥ 10 tokens/s on RTX 3050 Ti (4-bit)** |

---

## Stage 3 — DPO alignment *(Week 7)*

### Goal

Sharpen the SFT model using preference pairs derived from our existing
30-question evaluation: prefer answers that scored higher on
citation-accuracy + faithfulness, reject answers that scored lower.

### Preference-pair extraction

```python
for q in eval_questions:
    runs = [run for run in eval_runs_633k + eval_runs_740k if run.q == q]
    judged = [(run, judge[run.id]) for run in runs]
    chosen   = max(judged, key=lambda x: x[1].citation_accuracy + x[1].faithfulness)
    rejected = min(judged, key=lambda x: x[1].citation_accuracy + x[1].faithfulness)
    yield {
      "prompt": q.text,
      "chosen": chosen[0].final.answer_md,
      "rejected": rejected[0].final.answer_md,
    }
```

For 30 questions × 2 corpus configs we already have ~5K candidate pairs
(after expanding chunks-level pairs). DPO should sharpen the bias toward
answers that ground every claim.

### Configuration

| Parameter | Value |
|---|---|
| Base | `hakansabunis/turkresearcher-7b-instruct` |
| Method | Direct Preference Optimization (DPO) |
| β (regularisation) | 0.1 |
| Epochs | 1 |
| Hardware | Colab Pro+ A100, 4-6 hours |
| Output | `hakansabunis/turkresearcher-7b-instruct-dpo` |

### Targets

| Metric | SFT (Stage 2) | DPO (Stage 3) |
|---|---|---|
| Citation accuracy | 0.75 | **≥ 0.80** |
| Faithfulness | 0.70 | **≥ 0.78** |
| Coverage | 0.65 | **≥ 0.70** |

---

## Week 8 — Release & academic dissemination

### Public artefacts (all open, MIT/CC-BY)

```
hakansabunis/
├── trakad-embed-v2                        (HF Hub model, 768-dim, TR academic)
├── tr-academic-research-agent-index-v2    (HF Hub dataset, 740K, new embedder)
├── turk-researcher-qa-100k                (HF Hub dataset, 100K Q&A)
├── turkresearcher-7b-instruct             (HF Hub model, SFT adapter)
├── turkresearcher-7b-instruct-dpo         (HF Hub model, DPO model)
├── turkresearcher-demo                    (HF Space, Gradio UI)
└── tr-academic-research-agent             (GitHub repo, full pipeline)
```

### Communication

| Channel | Content |
|---|---|
| `hakansabunis.com` | 3 blog posts (one per stage) |
| LinkedIn | Project announcement after each stage |
| Twitter/X | Threads with eval comparison plots |
| Workshop paper (4-pager) | EACL Workshop / EMNLP Findings / arXiv |
| GitHub Releases | Tagged versions: `v0.2-embedder`, `v0.3-sft`, `v1.0-dpo` |

---

## Risk register

| Stage | Risk | Likelihood | Mitigation |
|---|---|---|---|
| 1 | Embedder collapse | Low | Larger batch + hard negatives + standard loss |
| 1 | <15% retrieval gain | Med | Try BM25 + dense hybrid; fall back to plain MNR |
| 2a | Synthetic Q&A teaches hallucinations | Med | Strict filter, manual review of 100 samples |
| 2b | Trendyol-7B Turkish academic register weak | Low | Switch to Cosmos-LLaMa or Qwen2.5 |
| 2b | 4 GB VRAM insufficient at inference | Med | Drop to Llama-3.2-3B base if needed |
| 3 | DPO regresses metrics | Low | Lower β, more epochs, fall back to SFT v2 |

---

## Total budget

| Item | Cost |
|---|---|
| DeepSeek API (Stage 2a synthesis) | ~$130 |
| Colab Pro+ (A100 for SFT + DPO) | ~$10-30 |
| Embedder Colab T4 (Stage 1) | $0 |
| Total cash | **~$140-200** |
| Active researcher time | ~80-100 hours over 8 weeks |
| GPU hours | ~30-40 (mostly Colab Pro+) |

---

## Why this matters

Turkey produces tens of thousands of academic theses and journal articles
in Turkish each year, but the LLM ecosystem barely indexes them. Tools
like Elicit and Consensus.app are English-only. A locally-runnable,
domain-specialised Turkish academic LLM would be useful to:

- MSc / PhD students doing Turkish-language literature reviews
- TÜBİTAK researchers preparing project proposals
- University libraries building Turkish-aware search interfaces
- Any Turkish-language research workflow currently using English LLMs and
  losing source coverage

---

## Status

This roadmap is **planning**, not committed work. Stage 0 (Capstone
delivery) is the immediate priority. Stage 1 begins after delivery.

*Last updated: 2026-05-09*
