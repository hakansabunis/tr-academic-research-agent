# Turkish Academic Base-LM Benchmark

*Which base language model best models Turkish academic-abstract register?
Fair bits-per-character (BPC) comparison + the Stage 2a continued-pretrain
negative result.*

## TL;DR

On 2,000 held-out, cleaned Turkish academic abstracts (raw text, each model
tokenized with its own tokenizer — no packing/decode artefact, ~0.34%
garbled rows removed):

| Model | Params | BPC (↓ better) | Note |
|---|---|---|---|
| **google/gemma-3-4b-pt** | **4B** | **0.7259** | 🏆 best, smallest |
| Trendyol-LLM-7b-base-v1.0 | 7B | 0.7455 | Turkish-specialized base |
| Trendyol-LLM-7b-chat-v1.0 | 7B | 0.7751 | chat-tuned |
| Cosmos-Turkish-Llama-8B-DPO | 8B | 0.8348 | Turkish Llama |
| **trakad-7b-base (ours, Stage 2a CPT)** | 7B | **1.0181** | worst — see below |

Two findings:

1. **A modern multilingual 4B model (Gemma-3-4b) beats Turkish-specialized
   7B/8B models on Turkish academic text.** Smaller and not Turkish-specific,
   yet lower perplexity and better-formed thesis-style generations.
2. **Naive continued pre-training on a narrow academic-abstract corpus
   degraded the base model** (Trendyol-7b 0.7455 → ours 1.0181, +36.6%
   worse BPC). This is a documented negative result, not a win.

## Methodology

- **Eval set:** `pretrain_corpus/clean_eval.parquet` — 2,000 abstracts
  (`{title}\n\n{abstract}`), sampled SEED=1234 (disjoint from the SEED=42
  training sample), garbled/non-Turkish rows filtered (`clean_corpus.py`:
  avg-word-length, Turkish-marker-ratio, non-Turkish-char-ratio heuristics).
- **Metric:** bits-per-character. Each model uses its own tokenizer; total
  NLL normalized by character count → tokenizer-independent, cross-model
  fair. Lower = the model assigns higher probability to real Turkish
  academic text.
- **No format artefact:** raw text, natural tokenization. (Earlier
  packed-chunk PPL tests were biased — see "Why the earlier numbers were
  misleading".)
- Greedy decoding (`do_sample=False`) for the qualitative generations.

## Why the earlier numbers were misleading

An earlier benchmark reported "trakad-7b-base PPL 4.99 vs vanilla Trendyol
28.22 (5.65× better)". That was a **train–test format artefact**:

- Our model trained on packed 2048-token chunks with EOS document
  separators. The packed-val PPL test fed back exactly that structure →
  our model saw its training distribution and scored low; vanilla never
  saw this packing and scored artificially high.
- Decoding those chunks to raw text and re-tokenizing flipped it the
  other way (EOS stripped, BOS added → out-of-distribution for our model).

Neither was fair. This BPC test on raw clean text with per-model
tokenization removes the artefact. The honest result: our continued
pre-train **hurt** raw-text modeling.

## Interpreting the negative result (Stage 2a)

`trakad-7b-base` = `Trendyol-LLM-7b-base-v1.0` + 1 epoch continued
pre-training on 387M tokens of Turkish academic abstracts.

Qualitatively the model **did** acquire a strong thesis-introduction
register prior ("Bu çalışmada … amaçlanmıştır", auto-generated
"Bir … modeli" subtitles). But BPC got worse. Reconciliation:

> The model collapsed toward a narrow stylistic template. It is fluent
> and confident in one register, but that over-confidence raises loss on
> the diverse phrasings real held-out abstracts use. A "thesis-template
> parrot": stylistically plausible, predictively weaker.

Likely root causes:

- Corpus too narrow (abstracts only, ~387M tokens, no general Turkish
  mixed in → catastrophic forgetting of general fluency).
- Aggressive packing format mismatched real single-document usage.
- Optimizer switch mid-run (paged_adamw_8bit → Adafactor with fresh
  state, forced by Colab bitsandbytes/triton breakage) may have
  destabilized training.
- One epoch over a narrow distribution = many effective passes →
  template overfit.

This is scientifically useful: *naive domain continued-pretraining on a
narrow register, without general-data replay, can reduce a base model's
predictive quality even while imparting a visible stylistic prior.*

## Strategic consequence

- **Drop the Trendyol/trakad-base path for the writer model.** Stage 2c
  (instruction tuning) will be done on **Gemma-3-4b** instead — smaller,
  cheaper (QLoRA fits a T4), and already the strongest Turkish-academic
  base measured here.
- **Keep Stage 2a as a documented ablation** ("what didn't work + why"),
  not a headline result.
- The project's solid quantitative win remains **Stage 1**
  (`trakad-embed-v2`: +9.9% citation accuracy, +42.6% on the CS category
  vs the mpnet baseline — see `comparison_v1_vs_v2.md`).

## Sample generations (greedy)

**Gemma-3-4b** — "Üniversite öğrencilerinin akademik başarısını etkileyen faktörler":
> … Bu çalışmanın amacı, üniversite öğrencilerinin motivasyon düzeylerini
> ve akademik başarılarını değerlendirmek ve bu iki değişken arasındaki
> ilişkiyi incelemektir. Araştırma, 2019-2020 eğitim öğretim yılında
> İstanbul'da bulunan bir devlet üniversitesinde öğrenim gören 300 öğrenci
> üzerinde gerçekleştirilmiştir. …

Coherent thesis methodology framing with specific, plausible detail —
strongest of all models tested.

## Reproducibility

- Eval set: `hakansabunis/tr-academic-research-agent-index` →
  `pretrain_corpus/clean_eval.parquet` (also in repo at
  `data/derived/clean_eval.parquet`)
- Cleaner: `models/writer/clean_corpus.py`
- Eval-set builder: `models/writer/_make_clean_eval.py`
- Benchmark notebook: `colab/fair_benchmark.ipynb`
- Garbled rows removed: YOK 535/633,998 (0.1%), DergiPark 1,986/106,641
  (1.9%); also catches mislabeled English `abstract_tr` entries.

*Generated: 2026-05-15 — Stage 2 base-model selection.*
