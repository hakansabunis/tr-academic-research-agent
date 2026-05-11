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
| **1.5** | Data audit + pilot pre-train (decide what to add to Stage 2a corpus) | 1-2 weeks | ~$20-60 | `docs/data_audit.md` + go/no-go per source |
| **2** | Turkish academic writer (dual-use: internal RAG writer + MCP/API tool for foreign LLMs) | 4 weeks | ~$110-140 | `trakad-writer-7b` |
| **3** | DPO alignment | 1 week | ~$10-30 | `trakad-writer-7b-dpo` |

End-state: 5+ open Hugging Face artefacts, 1 GitHub repo, 1 MCP server,
1 workshop paper candidate.

---

## Mental model — the library analogy

The system is a **library with 740K Turkish academic books**:

- **Librarian** = the embedder (decides which books are relevant to a query)
- **Writer** = the LLM (reads the chosen books and writes the answer)
- **Books** = thesis + journal abstracts already indexed in Chroma

| Component | Today (v0) | After Stage 1 | After Stage 2 | After Stage 3 |
|---|---|---|---|---|
| Librarian | mpnet generic | `trakad-embed-v2` | `trakad-embed-v2` | `trakad-embed-v2` |
| Writer | DeepSeek API (rented) | DeepSeek API | `trakad-writer-7b` (own + MCP/API tool) | `trakad-writer-7b-dpo` |
| Cost / query | ~$0.005 | ~$0.005 | $0 (local) | $0 (local) |
| Offline? | No | No | **Yes** | **Yes** |
| Citation accuracy target | 0.51-0.60 | ≥ 0.70 | ≥ 0.75 | ≥ 0.80 |
| External usage | — | — | **MCP server + HF Space API → Claude / GPT / Gemini users** | Same, sharper |

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

## Stage 1.5 — Data Sourcing & Quality Audit *(Week 2.5, ~1-2 weeks)*

### Goal

Before committing Stage 2a to a specific corpus, systematically probe
candidate Turkish academic data sources. Stage 0 already taught us this
lesson the hard way (the "Corpus Expansion Paradox": expanding from 633K
to 740K theses *reduced* citation accuracy because the added DergiPark
content had a different register distribution). This stage is the
explicit, measured version of that decision.

The output is not a model, it is a *go/no-go decision per data source*
and a final corpus composition for Stage 2a.

### Sub-stage 1.5a — Inventory *(1-2 days)*

Catalog every candidate Turkish academic data source. For each, record:

| Field | Example |
|---|---|
| Source | DergiPark Türkçe full-text |
| Estimated volume | ~2-5B tokens after PDF parse |
| License | Mostly CC-BY / open access; per-journal check needed |
| Register quality (a priori) | High (peer-reviewed) |
| Acquisition cost | OAI-PMH free, PDF parse ~$0.001/page |
| Risks | OCR noise, layout artifacts, copyright minefield for newer issues |

Candidates to inventory (initial list, to extend):

| # | Source | Why interesting |
|---|---|---|
| 1 | DergiPark Türkçe abstracts (already harvested) | Native register, large, free |
| 2 | DergiPark full-text PDFs | ~10x volume vs abstracts; PDF parse needed |
| 3 | TÜBA Açık Ders (open courseware) | Editor-supervised teaching prose, smaller corpus |
| 4 | TÜBA Yayınlar (academic books) | Highest editorial quality; commercial license check |
| 5 | TÜBİTAK proceedings / TÜBİTAK Ulakbim | Government-funded research, native Turkish |
| 6 | METU / Boğaziçi / ITU open courseware (TR lectures) | Spoken academic register; transcript quality varies |
| 7 | Resmi Gazete teknik tebliğler | Formal Turkish but bureaucratic, not academic |
| 8 | TBMM komite raporları | Formal Turkish, technical domains, edited |
| 9 | Turkish translations of foreign academic books | Highest controlled-translation quality; copyright |
| 10 | Wikipedia Turkish (academic categories filtered) | Crowd-edited; lower register but free and clean |

### Sub-stage 1.5b — Sampling & spot-check *(2-3 days)*

For each candidate from 1.5a:

1. Pull 1K-5K random samples.
2. Spot-check 30 samples manually for register, grammar, domain fit.
3. Run an LLM-as-judge proxy ("Bu metin akademik Türkçe register'ında mı? 1-5") on the full sample.
4. Estimate **post-cleaning yield** — sources that look big on paper but lose 80% of content to header/footer/OCR noise.

Output: `data/audit_samples/<source>.parquet` (5K rows each), plus a
register-quality score per source.

### Sub-stage 1.5c — Pilot continued pre-training *(3-5 days, ~$50)*

For each source that scored ≥ 3 in 1.5b, run a *cheap* pilot
continued-pre-train of Trendyol-7B on ~100M tokens of that source alone.

| Parameter | Value |
|---|---|
| Base | `Trendyol-LLM-7B-base-v4.0` (frozen reference: vanilla base) |
| Pilot data | ~100M tokens from one candidate source |
| Method | Standard causal LM, bf16, LoRA rank=8 to save time/cost |
| Epochs | 1 |
| Wall time | ~2-3 hours per source on Colab Pro+ A100 |
| Cost | ~$8-10 per pilot run |

After each pilot, measure:

| Metric | Direction |
|---|---|
| Held-out perplexity on `thesis_test_5pct.parquet` (Turkish academic) | Lower = better academic fit |
| Held-out perplexity on `general_tr_test.jsonl` (Wiki/web mix) | Should not rise much — general ability retention |
| Citation-accuracy proxy: 30-Q eval with vanilla writer + this base | Higher = real downstream gain |

A source "wins" if it (i) lowers academic perplexity meaningfully (≥ 5%
relative) and (ii) does not regress general perplexity by more than 3%
relative.

### Sub-stage 1.5d — Decision matrix & final composition *(1 day)*

Aggregate 1.5b + 1.5c into one matrix:

| Source | Register score | Acad. PPL gain | General PPL cost | Volume | Cost to acquire | Decision |
|---|---|---|---|---|---|---|
| DergiPark abstracts | 4/5 | -8% | -1% | 300M | $0 (have it) | ✅ Include |
| DergiPark full-text | ? | ? | ? | 2-5B | PDF parse $200 | TBD by pilot |
| TÜBA Açık Ders | 5/5 | -3% | 0% | 50M | scraping | ✅ Include (small but premium) |
| TÜBİTAK Ulakbim | 3/5 | ~0% | 0% | 100M | OAI free | ⚠️ Maybe (marginal) |
| Wikipedia TR (acad filter) | 2/5 | -1% | +2% | 200M | dump free | ❌ Skip (dilutes) |
| Resmi Gazete | 2/5 | 0% | +1% | 100M | scraping | ❌ Skip (wrong register) |

Final Stage 2a corpus composition is then a weighted mix of the ✅ entries,
sized to 800M-1.5B tokens.

### Outputs

- `docs/data_audit.md` — full audit report, decision rationale per source
- `data/audit_samples/*.parquet` — 5K-row samples per candidate (reusable)
- `data/audit_perplexity/*.json` — pilot pre-train metrics per candidate
- `data/stage2a_corpus/` — final mixed corpus for Stage 2a continued pre-train
- (Optional) `hakansabunis/tr-academic-stage2a-mix` — HF dataset with the final composition

### Targets

| Metric | Target |
|---|---|
| Sources audited | ≥ 8 candidates |
| Pilot pre-trains run | ≥ 4 (top register-score sources) |
| Final Stage 2a corpus size | 800M-1.5B tokens |
| Academic PPL drop vs vanilla Trendyol-7B on `thesis_test_5pct` | ≥ 8% relative |
| General PPL retention on `general_tr_test` | ≤ 3% relative regression |

### Risk

Low-Medium. The risk is *over*-investing in audit and delaying Stage 2.
Mitigation: cap audit phase at 2 weeks; if a candidate needs >2 days of
engineering to even sample (e.g., bespoke OCR pipelines), it is dropped
to "future work" instead of blocking.

### Why this stage matters

- **Avoids repeating the Corpus Expansion Paradox.** Last time we paid
  for noisy data with a measurable accuracy drop.
- **The pilots are cheap (~$50 total) compared to a full Stage 2a run
  (~$30) — but they de-risk the Stage 2a investment by 10x.**
- **Documented audit = good story.** The decision matrix is itself a
  publishable artifact for the workshop paper section on Turkish academic
  data quality.

---

## Stage 2 — Turkish Academic Writer *(Weeks 3-6)*

### Goal

Build a domain-specialised Turkish academic writing model with two
deliberate use cases:

1. **Internal use** — replaces the rented DeepSeek API as the writer agent
   inside TürkResearcher's own RAG pipeline.
2. **External use** — exposed as an MCP server / HTTP API that foreign
   LLMs (Claude, GPT, Gemini) can call as a tool when they need to
   produce idiomatic Turkish academic prose.

The asymmetry being exploited: foreign LLMs reason superbly in English but
produce awkward Turkish output, because their pre-training data contains
very little high-quality Turkish academic text. Our 633K thesis corpus is
exactly that — native-speaker, edited, supervisor-reviewed academic prose
— and it doubles as a ~633K-pair parallel English↔Turkish corpus (YÖK
requires both abstracts on every thesis).

### Two hidden assets in the corpus

1. **Monolingual high-quality Turkish** — ~600M tokens of native, edited
   academic register prose. Cosmos / Trendyol / Hammer are pre-trained
   largely on web crawls (forum, blog, e-commerce); the quality of our
   corpus is materially higher for academic register.
2. **Parallel English↔Turkish** — ~633K abstract pairs. A parallel
   academic corpus of this scale and domain coverage does not exist for
   Turkish in any public dataset today.

### Sub-stage 2a — Continued pre-training *(Week 3)*

Domain-adapt a Turkish base model on the monolingual Turkish corpus.

| Parameter | Value |
|---|---|
| Base model | `Trendyol/Trendyol-LLM-7B-base-v4.0` (Apache 2.0) |
| Data | 633K Turkish abstracts (~600M tokens) |
| Method | Standard causal LM, bf16 mixed precision |
| Epochs | 1-2 |
| LR | 1e-5 (low to preserve general knowledge) |
| Effective batch | 32-64 |
| Hardware | Colab Pro+ A100 |
| Wall time | 12-20 hours |
| Cost | ~$30 (Colab Pro+) |
| Output | `hakansabunis/trakad-7b-base` (foundation, not instruction-tuned) |

Why low LR + few epochs: we want to *shift* the base model toward Turkish
academic register without erasing its general capabilities, the same
catastrophic-forgetting logic as Stage 1.

### Sub-stage 2b — Synthetic data preparation *(Week 4)*

The 633K parallel pairs feed three instruction templates. Mode B
("style refinement") needs synthetic rough Turkish as input — generated
by a back-translation trick.

| Mode | Input | Output | Source of `input` |
|---|---|---|---|
| A. Translator | English abstract | Turkish abstract | Direct (en_abstract → tr_abstract) |
| B. Refiner | Awkward Turkish | Polished Turkish | `tr → en → tr` round-trip through GPT-4o-mini |
| C. Writer | Topic + key points | Turkish paragraph | `(title + extracted keywords) → tr_abstract` |

For Mode B, we run each Turkish abstract through GPT-4o-mini twice
(tr → en, then en → tr). The result is grammatically valid but
unnatural Turkish — exactly the failure mode of foreign LLMs we want our
model to fix. Training pair: (round-tripped rough Turkish → original
high-quality Turkish abstract).

| Item | Value |
|---|---|
| Source pairs | 633K theses |
| Modes | 3 (Translator, Refiner, Writer) |
| Total candidate instructions | ~1.9M |
| Sub-sample for training | 300K-500K (cost-balanced) |
| Mode B back-translation API | GPT-4o-mini, ~$80 |
| Dedup | per-mode Jaccard < 0.7 |
| Output | `hakansabunis/trakad-writer-instruct-500k` (HF dataset, CC-BY-4.0) |

### Sub-stage 2c — QLoRA SFT *(Weeks 5-6)*

| Parameter | Value |
|---|---|
| Base | `hakansabunis/trakad-7b-base` (Stage 2a output) |
| Quantisation | 4-bit NF4 |
| LoRA rank | 16 |
| LoRA alpha | 32 |
| Target modules | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` |
| Data | 300K-500K instructions (3 modes mixed) |
| Epochs | 2 |
| LR | 2e-4 (cosine, 3% warmup) |
| Effective batch | 16 (per-device 4 × accum 4) |
| Optimizer | `paged_adamw_32bit` |
| Hardware | Colab Pro+ A100 |
| Wall time | 8-12 hours |
| Cost | ~$30 (Colab Pro+) |
| Output | `hakansabunis/trakad-writer-7b` (~70 MB adapter) |

### Why Trendyol-LLM-7B-base?

- Pre-trained on a large Turkish corpus by Trendyol (e-commerce + crawl) —
  sound Turkish grammar and vocabulary, the right base to specialise.
- Apache 2.0 license (commercially redistributable).
- 7B fits in 4 GB VRAM after 4-bit quantisation, so the final model runs
  on consumer hardware (RTX 3050 Ti at ~10-15 tokens/s).

Backup candidates: `Cosmos-LLaMa-Turkish-8B`, `Qwen2.5-7B-Instruct`,
`Llama-3.2-3B-Instruct` (lighter alternative).

### Deployment — three concurrent paths

**1) MCP server (primary)** — for Claude Desktop, Cursor, Cline users.

Exposed tools:

| Tool | Signature | Use case |
|---|---|---|
| `tr_translate` | `(en_text: str) -> tr_text: str` | Foreign LLM produced English; needs Turkish output |
| `tr_refine` | `(rough_tr: str) -> polished_tr: str` | Foreign LLM produced awkward Turkish; needs polish |
| `tr_write` | `(topic: str, keypoints: list[str]) -> tr_paragraph: str` | Direct Turkish generation from a brief |

Local 4-bit inference (~6 GB VRAM), $0/query, fully offline after model
download. Distributed as a single `pip install trakad-writer-mcp`
package wrapping the model + MCP server stub.

**2) HF Space REST API** — for tools that don't speak MCP (Custom GPT,
n8n, Zapier, web frontends).

Same three endpoints (`POST /translate`, `/refine`, `/write`). Paid GPU
tier (~$30/month for A10G) for production latency; free tier can fall
back to CPU for low-volume demo.

**3) Internal drop-in** — replaces DeepSeek API in TürkResearcher's RAG
writer.

Single config swap in `src/turk_researcher/llm.py`. Per-query cost
0.005 → $0. The Capstone demo now runs entirely offline after model
download.

### Evaluation

**Objective:**

| Metric | How | Target |
|---|---|---|
| BLEU / chrF | English → Turkish on held-out 5% pair split (~30K pairs) | BLEU ≥ 25, chrF ≥ 55 |
| Perplexity | On held-out Turkish abstracts vs base model | ≥ 10% relative drop |
| Native Turkish % | Output passed through a Turkish detection classifier | ≥ 99% |
| Citation accuracy (RAG) | 30-question eval with new writer | ≥ 0.75 |
| Holistic score (RAG) | LLM-as-judge | ≥ 3.5 / 5 |

**Subjective:**

- 5 native Turkish academics; blind A/B taste test:
  `trakad-writer-7b` vs `GPT-4o` vs `Cosmos-LLaMa-Turkish-8B`
  on the same prompt set (30 prompts across translation, refinement,
  native writing).
- Target: ≥ 60% prefer our output for *academic register* (not
  factual content).
- This small human eval is enough signal for a workshop paper section
  on Turkish academic generation quality.

### Targets

| Metric | DeepSeek API baseline | `trakad-writer-7b` target |
|---|---|---|
| Holistic score (1-5) | 2.4-2.6 | **≥ 3.5** |
| Citation accuracy (RAG) | 0.51-0.60 | **≥ 0.75** |
| Hallucination rate | unknown | < 10% |
| Per-query cost | $0.005 | **$0** |
| Local inference | n/a | **≥ 10 tokens/s on RTX 3050 Ti (4-bit)** |
| External tool surface | n/a | **MCP server + REST API live** |
| Foreign-LLM Turkish quality boost (human eval) | n/a | **≥ 60% preferred over GPT-4o for academic register** |

### Why this matters

- **Niche but undefended.** General-purpose Turkish LLMs exist (Cosmos,
  Trendyol, Hammer); none target academic register, and none expose
  themselves as a tool for foreign LLMs to call.
- **The parallel corpus is gold.** ~633K academic English↔Turkish pairs
  at this domain and scale is unpublished elsewhere.
- **Same training run, three deliverables.** Translator, refiner,
  writer — all addressable from one model with prompt prefixes.
- **Symmetric value to two audiences.** Turkish researchers writing their
  own papers; foreign LLM users who need Turkish output. Most projects
  target one audience.

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
| Base | `hakansabunis/trakad-writer-7b` |
| Method | Direct Preference Optimization (DPO) |
| β (regularisation) | 0.1 |
| Epochs | 1 |
| Hardware | Colab Pro+ A100, 4-6 hours |
| Output | `hakansabunis/trakad-writer-7b-dpo` |

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
├── trakad-7b-base                         (HF Hub model, Turkish academic foundation)
├── trakad-writer-instruct-500k            (HF Hub dataset, 3-mode instructions)
├── trakad-writer-7b                       (HF Hub model, SFT adapter)
├── trakad-writer-7b-dpo                   (HF Hub model, DPO model)
├── trakad-writer-mcp                      (PyPI / GitHub, MCP server wrapper)
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
| 1.5 | Audit over-invests, delays Stage 2 | Med | Hard 2-week cap; sources needing >2d engineering deferred to "future work" |
| 1.5 | Copyright on book / journal full-text unclear | Med | Stick to OAI-PMH, CC-licensed sources, or per-source explicit permission |
| 1.5 | Pilot perplexity gain doesn't translate downstream | Low | Also run lightweight 30-Q eval proxy on each pilot before final decision |
| 2a | Continued pre-training erases base general ability | Low | Low LR (1e-5), 1-2 epochs; small held-out general eval as guardrail |
| 2b | Back-translated rough Turkish is too clean (Mode B too easy) | Med | Use a weaker MT model (e.g. NLLB) instead of GPT-4o-mini for some pairs |
| 2c | Trendyol-7B Turkish academic register weak | Low | Switch base to Cosmos-LLaMa or Qwen2.5 |
| 2c | 4 GB VRAM insufficient at inference | Med | Drop to Llama-3.2-3B base if needed |
| 2c | Three modes interfere (negative transfer) | Med | Train mode-specific adapters; route by prompt prefix |
| 2 | MCP adoption is niche | Med | REST API fallback works for any client; HF Space demo broadens audience |
| 3 | DPO regresses metrics | Low | Lower β, more epochs, fall back to SFT v2 |

---

## Total budget

| Item | Cost |
|---|---|
| Embedder Colab A100 (Stage 1) | $0-5 |
| Data audit pilots, Colab Pro+ A100 (Stage 1.5) | ~$20-60 |
| Continued pre-train, Colab Pro+ A100 (Stage 2a) | ~$30 |
| GPT-4o-mini back-translation for Mode B (Stage 2b) | ~$80 |
| QLoRA SFT, Colab Pro+ A100 (Stage 2c) | ~$30 |
| DPO, Colab Pro+ A100 (Stage 3) | ~$10-30 |
| HF Space paid GPU (optional, for API hosting) | ~$30/month |
| Total cash, training only | **~$170-240** |
| Total cash with 6 months of paid Space | ~$350-420 |
| Active researcher time | ~90-110 hours over 9-10 weeks |
| GPU hours | ~35-50 (mostly Colab Pro+) |

---

## Why this matters

Two asymmetries this project leans on:

**1) Turkish academic corpus coverage.** Turkey produces tens of
thousands of theses and journal articles in Turkish each year, but the
LLM ecosystem barely indexes them. Tools like Elicit and Consensus.app
are English-only. A locally-runnable, domain-specialised Turkish
academic LLM is useful to:

- MSc / PhD students doing Turkish-language literature reviews
- TÜBİTAK researchers preparing project proposals
- University libraries building Turkish-aware search interfaces
- Any Turkish-language research workflow currently using English LLMs and
  losing source coverage

**2) Foreign LLMs cannot write Turkish academic prose well.** Claude,
GPT, Gemini are strong reasoners in English but produce awkward,
calque-heavy Turkish output, because high-quality Turkish academic text
is under-represented in their pre-training data. Stage 2's MCP / API
deliverable turns our corpus advantage into a *tool* those models can
call — they reason in English, our model produces idiomatic Turkish.
This pattern (a small specialist model serving as a "native voice" for
a large generalist) is itself a transferable idea: the same template
applies to any low-resource language with a high-quality domain corpus.

---

## Status

This roadmap is **planning**, not committed work. Stage 0 (Capstone
delivery) is the immediate priority. Stage 1 begins after delivery.

*Last updated: 2026-05-11 — Stage 2 evolved to dual-purpose (internal writer + MCP/API tool for foreign LLMs); Stage 1.5 added as data audit / pilot pre-train gate before Stage 2a.*
