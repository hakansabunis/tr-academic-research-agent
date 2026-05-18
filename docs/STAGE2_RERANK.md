# Stage 2 (Yol 2) — Cross-encoder Reranker

## Motivation (empirical, from the Stage 2b diagnostic)

Yol 1 (distilling the DeepSeek writer) was tested first. Two independent
diagnostics (5 medical + 30 CS/eng questions, scored with the *same*
`scripts/07_judge_eval.py` metric) showed:

| | citation | faithfulness | holistic |
|---|---|---|---|
| Medical smoke (n=5) | 0.51 | 0.45 | 2.20 |
| CS-bias (n=30) | 0.54 | 0.48 | 2.27 |
| System v2 eval baseline (n=29) | 0.56 | 0.53 | 2.31 |

Scores are uniform across domains and track the system's own weak baseline.
Rejection-sampling keep-rate at calibrated thresholds: **~13%**. Conclusion:
the bottleneck is **retrieval grounding, not the writer LM** — a clean,
honest negative that motivates Yol 2. (Yol 1 stays as the diagnostic +
a cheap "API-free baseline" ablation.)

## What changed

- `src/turk_researcher/tools/reranker.py` — cross-encoder rerank, lazy +
  cached, env-toggled, fail-safe (falls back to bi-encoder order).
- `src/turk_researcher/agents/retriever_node.py` — additive hook.
  **Product default ON** (measured-best). `TRRESEARCHER_RERANK=0` ⇒
  byte-identical to the v2 no-rerank baseline (used for the A/B below).
  ON ⇒ retrieve a wider candidate pool, cross-encoder re-score, keep top-N.

## A/B evaluation protocol (reuses existing harness)

Baseline already on disk: `data/eval/runs_v2` / `judgments_v2` /
`summary_v2.json` (faith 0.53, cite 0.56, holistic 2.31).

Rerank arm (PowerShell):
```powershell
$env:CHROMA_PERSIST_DIR = "C:\dev\turk-researcher-data\chroma_db_v2"
$env:EMBEDDING_MODEL    = "hakansabunis/trakad-embed-v2"
$env:TRRESEARCHER_RERANK = "1"
$env:RERANK_MODEL = "BAAI/bge-reranker-base"   # multilingual incl. Turkish
$env:RERANK_TOP_N = "10"
# $env:RERANK_DEVICE = "cuda"   # if torch sees the 3050 Ti — much faster

python scripts/06_run_eval.py --out-dir data/eval/runs_rerank
python scripts/07_judge_eval.py --runs data/eval/runs_rerank --out data/eval/judgments_rerank
python scripts/08_eval_summary.py   # point at the rerank dirs
```
Success = faithfulness / citation_accuracy rise vs `summary_v2` on the SAME
30-question holdout. Even a negative is publishable (honest).

## Results — paired A/B, 30-question holdout (n=29)

`BAAI/bge-reranker-base`, top-10, same questions, same `07_judge_eval` metric.

| Metric | v2 baseline | v2 + reranker | Δ | win/lose/tie |
|---|---|---|---|---|
| citation_accuracy | 0.557 | **0.647** | **+0.090** (~+16% rel.) | 17 / 4 / 8 |
| faithfulness | 0.528 | **0.566** | +0.038 | 16 / 10 / 3 |
| coverage | 0.450 | 0.434 | −0.016 | 8 / 8 / 13 |
| holistic | 2.310 | 2.414 | +0.103 | 8 / 5 / 16 |

Side effects: citations 28→~13 (fewer, better-grounded), latency 122s→83s.
Effect size (mean Δ / sd of paired diffs): citation 0.55 (medium),
faithfulness 0.29 (small–medium).

**Honest read:** a clean positive Stage 2 — the cross-encoder closes the
diagnostic-identified bottleneck (citation +9 pts, 17:4 wins) at $0 compute,
stacking on the embedder gain (+9.9%) and directly attacking the documented
Corpus Expansion Paradox.

**Threat to validity (record in paper):** the rerank arm ran with
`TRRESEARCHER_LIVE=0`; `runs_v2` baseline may have had live search on. Live
search adds sources, so disabling it would, if anything, *depress* the
rerank arm's coverage (consistent with Δcoverage −0.016) and cannot explain
the citation/faithfulness gains. A confirmatory baseline re-run with
`TRRESEARCHER_LIVE=0` is recommended future work for a strictly clean A/B.

## Cost
Reranker = local model, **$0 GPU/API**. The eval arm spends DeepSeek over
30 questions (same as prior `runs_v2`, ~a few $). CPU rerank adds latency;
`RERANK_DEVICE=cuda` recommended if available.

## Ablation triad (paper)
1. abandoned `build_writer_sft.py` (title→abstract) — documented failure
2. grounded-distill LoRA @ loose threshold — "API-free baseline"
3. **v2 + reranker** — the quality lever (this doc)
all vs DeepSeek, same `06→08` harness, same 30-question holdout.
