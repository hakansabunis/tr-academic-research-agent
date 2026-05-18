# TürkResearcher — Evaluation Summary

- **Questions:** 30 (ok: 30, failed: 0)


## Overall Metrics

| Metric | Mean | Median | Min | Max | n |
|---|---|---|---|---|---|
| citation_accuracy | 0.653 | 0.7 | 0.3 | 0.95 | 30 |
| faithfulness | 0.573 | 0.6 | 0.2 | 0.9 | 30 |
| coverage | 0.443 | 0.4 | 0.2 | 0.9 | 30 |
| holistic_score | 2.433 | 2.0 | 2 | 4 | 30 |
| n_citations | 12.733 | 13.0 | 10 | 16 | 30 |
| n_chunks | 12.733 | 13.0 | 10 | 16 | 30 |
| max_score | 0.801 | 0.909 | 0.043 | 0.998 | 30 |
| latency_seconds | 82.835 | 83.68 | 46.8 | 114.05 | 30 |

## By Category

| Category | n | Cite Acc | Faithfulness | Coverage | Holistic | Latency (s) |
|---|---|---|---|---|---|---|
| computer_science | 4 | 0.4 | 0.362 | 0.275 | 2 | 89.455 |
| education | 3 | 0.883 | 0.833 | 0.667 | 3 | 86.447 |
| health | 3 | 0.733 | 0.65 | 0.467 | 2.333 | 81.837 |
| engineering | 3 | 0.633 | 0.533 | 0.4 | 2.333 | 87.017 |
| social_sciences | 2 | 0.775 | 0.7 | 0.45 | 2.5 | 76.685 |
| business | 2 | 0.7 | 0.6 | 0.4 | 2.5 | 72.625 |
| agriculture | 1 | 0.6 | 0.5 | 0.4 | 2 | 73.95 |
| veterinary | 1 | 0.85 | 0.7 | 0.6 | 3 | 81.52 |
| linguistics | 1 | 0.3 | 0.4 | 0.4 | 2 | 76.88 |
| law | 2 | 0.725 | 0.6 | 0.6 | 2.5 | 89.635 |
| physics | 1 | 0.6 | 0.5 | 0.3 | 2 | 88.2 |
| chemistry | 1 | 0.7 | 0.6 | 0.4 | 2 | 49.98 |
| biology | 1 | 0.5 | 0.4 | 0.3 | 2 | 87.82 |
| tourism | 1 | 0.85 | 0.7 | 0.4 | 3 | 67.95 |
| sports | 1 | 0.6 | 0.5 | 0.4 | 2 | 98.84 |
| multi_domain | 2 | 0.775 | 0.7 | 0.65 | 3.5 | 90.26 |
| edge_case | 1 | 0.3 | 0.2 | 0.2 | 2 | 77.79 |

## Per-Question

| ID | Category | Type | Lat (s) | #Cite | CitAcc | Faith | Cov | Hol |
|---|---|---|---|---|---|---|---|---|
| q01 | computer_science | trend | 114.05 | 13 | 0.3 | 0.4 | 0.2 | 2 |
| q02 | computer_science | method | 76.41 | 15 | 0.6 | 0.5 | 0.4 | 2 |
| q03 | computer_science | application | 82.87 | 16 | 0.3 | 0.25 | 0.2 | 2 |
| q04 | computer_science | comparison | 84.49 | 13 | 0.4 | 0.3 | 0.3 | 2 |
| q05 | education | trend | 80.58 | 12 | 0.95 | 0.9 | 0.6 | 3 |
| q06 | education | method | 85.8 | 12 | 0.85 | 0.8 | 0.6 | 3 |
| q07 | education | limitation | 92.96 | 13 | 0.85 | 0.8 | 0.8 | 3 |
| q08 | health | method | 90.36 | 15 | 0.6 | 0.5 | 0.4 | 2 |
| q09 | health | comparison | 108.35 | 13 | 0.7 | 0.6 | 0.4 | 2 |
| q10 | health | application | 46.8 | 10 | 0.9 | 0.85 | 0.6 | 3 |
| q11 | engineering | application | 85.86 | 14 | 0.6 | 0.5 | 0.3 | 2 |
| q12 | engineering | method | 89.85 | 10 | 0.7 | 0.6 | 0.5 | 3 |
| q13 | engineering | trend | 85.34 | 16 | 0.6 | 0.5 | 0.4 | 2 |
| q14 | social_sciences | trend | 75.88 | 11 | 0.7 | 0.6 | 0.4 | 2 |
| q15 | social_sciences | method | 77.49 | 11 | 0.85 | 0.8 | 0.5 | 3 |
| q16 | business | method | 73.37 | 12 | 0.7 | 0.6 | 0.4 | 2 |
| q17 | business | application | 71.88 | 14 | 0.7 | 0.6 | 0.4 | 3 |
| q18 | agriculture | method | 73.95 | 14 | 0.6 | 0.5 | 0.4 | 2 |
| q19 | veterinary | method | 81.52 | 13 | 0.85 | 0.7 | 0.6 | 3 |
| q20 | linguistics | method | 76.88 | 12 | 0.3 | 0.4 | 0.4 | 2 |
| q21 | law | limitation | 87.67 | 12 | 0.85 | 0.8 | 0.7 | 3 |
| q22 | law | comparison | 91.6 | 14 | 0.6 | 0.4 | 0.5 | 2 |
| q23 | physics | method | 88.2 | 13 | 0.6 | 0.5 | 0.3 | 2 |
| q24 | chemistry | application | 49.98 | 10 | 0.7 | 0.6 | 0.4 | 2 |
| q25 | biology | method | 87.82 | 12 | 0.5 | 0.4 | 0.3 | 2 |
| q26 | tourism | trend | 67.95 | 11 | 0.85 | 0.7 | 0.4 | 3 |
| q27 | sports | method | 98.84 | 14 | 0.6 | 0.5 | 0.4 | 2 |
| q28 | multi_domain | cross | 100.04 | 13 | 0.85 | 0.8 | 0.9 | 4 |
| q29 | multi_domain | cross | 80.48 | 10 | 0.7 | 0.6 | 0.4 | 3 |
| q30 | edge_case | narrow | 77.79 | 14 | 0.3 | 0.2 | 0.2 | 2 |
