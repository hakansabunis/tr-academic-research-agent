# 633K vs 740K Corpus Comparison

Pre: 633.998 thesis abstracts (mpnet-base-v2, cosine).
Post: + 106.641 DergiPark journal articles → 740.639 total.

## Overall metrics
| Metric | 633K | 740K | Δ |
|---|---|---|---|
| citation_accuracy | 0.603 | 0.507 | -0.096 ↓ |
| faithfulness | 0.585 | 0.490 | -0.095 ↓ |
| coverage | 0.492 | 0.465 | -0.027 ↓ |
| holistic_score | 2.63 | 2.40 | -0.23 ↓ |
| n_citations | 30.1 | 32.8 | +2.7 ↑ |
| latency_seconds | 105.8 | 111.4 | +5.6 ↑ |

## Per-category citation accuracy
| Category | n | 633K | 740K | Δ |
|---|---|---|---|---|
| business | 2 | 0.47 | 0.68 | +0.20 ↑ |
| computer_science | 4 | 0.21 | 0.26 | +0.05 ↑ |
| social_sciences | 2 | 0.78 | 0.70 | -0.08 ↓ |
| education | 3 | 0.75 | 0.63 | -0.12 ↓ |
| multi_domain | 2 | 0.85 | 0.70 | -0.15 ↓ |
| engineering | 3 | 0.73 | 0.53 | -0.20 ↓ |
| law | 2 | 0.62 | 0.40 | -0.22 ↓ |
| health | 3 | 0.80 | 0.53 | -0.27 ↓ |

## Interpretation

- Mean citation accuracy DROPPED at the corpus level (0.60 → 0.51) despite the broader corpus.
- Computer-science (the original failure mode) improved by +0.05, suggesting article inclusion does help domains where Turkish theses are sparse.
- Mean citation count increased (30.1 → 32.8), so the writer agent produces *more* but not necessarily *better-grounded* citations.
- DergiPark journal abstracts are typically shorter than thesis abstracts; mixed-source contexts reduce the writer's ability to ground every claim.
- Take-away: corpus expansion is **not** a free improvement; the system needs a smarter source-aware retrieval / writer policy (future work).