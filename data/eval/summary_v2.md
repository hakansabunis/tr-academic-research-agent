# TürkResearcher — Evaluation Summary

- **Questions:** 30 (ok: 29, failed: 1)


## Overall Metrics

| Metric | Mean | Median | Min | Max | n |
|---|---|---|---|---|---|
| citation_accuracy | 0.557 | 0.6 | 0.2 | 0.85 | 29 |
| faithfulness | 0.528 | 0.5 | 0.15 | 0.8 | 29 |
| coverage | 0.45 | 0.4 | 0.2 | 0.9 | 29 |
| holistic_score | 2.31 | 2 | 1 | 4 | 29 |
| n_citations | 28.31 | 27 | 16 | 41 | 29 |
| n_chunks | 28.31 | 27 | 16 | 41 | 29 |
| max_score | 0.896 | 0.894 | 0.849 | 0.949 | 29 |
| latency_seconds | 122.379 | 121.16 | 52.66 | 181.38 | 29 |

## By Category

| Category | n | Cite Acc | Faithfulness | Coverage | Holistic | Latency (s) |
|---|---|---|---|---|---|---|
| computer_science | 4 | 0.375 | 0.35 | 0.275 | 1.75 | 87.457 |
| education | 3 | 0.7 | 0.667 | 0.667 | 3.333 | 97.073 |
| health | 3 | 0.667 | 0.633 | 0.467 | 2.333 | 151.283 |
| engineering | 3 | 0.433 | 0.433 | 0.433 | 2 | 158.34 |
| social_sciences | 2 | 0.6 | 0.575 | 0.5 | 2.5 | 150.52 |
| business | 2 | 0.775 | 0.725 | 0.6 | 3 | 131.145 |
| agriculture | 1 | 0.6 | 0.5 | 0.25 | 2 | 119.15 |
| veterinary | 1 | 0.5 | 0.6 | 0.4 | 2 | 52.66 |
| linguistics | 1 | 0.6 | 0.5 | 0.6 | 3 | 113.2 |
| law | 2 | 0.6 | 0.5 | 0.6 | 3 | 161.51 |
| physics | 1 | 0.3 | 0.25 | 0.2 | 1 | 123.2 |
| chemistry | 1 | 0.6 | 0.5 | 0.4 | 2 | 139.19 |
| biology | 1 | 0.4 | 0.5 | 0.3 | 2 | 119.21 |
| tourism | 1 | 0.6 | 0.5 | 0.4 | 2 | 121.16 |
| sports | 1 | 0.6 | 0.65 | 0.5 | 3 | 137.11 |
| multi_domain | 2 | 0.7 | 0.675 | 0.6 | 2.5 | 114.215 |
| edge_case | 1 | 0.3 | 0.25 | 0.2 | 1 | 100.91 |

## Per-Question

| ID | Category | Type | Lat (s) | #Cite | CitAcc | Faith | Cov | Hol |
|---|---|---|---|---|---|---|---|---|
| q01 | computer_science | trend | 126.44 | 29 | 0.6 | 0.5 | 0.4 | 2 |
| q02 | computer_science | method | 105.8 | 27 | 0.4 | 0.35 | 0.3 | 2 |
| q03 | computer_science | application | 60.27 | 24 | 0.3 | 0.4 | 0.2 | 2 |
| q04 | computer_science | comparison | 57.32 | 24 | 0.2 | 0.15 | 0.2 | 1 |
| q05 | education | trend | 61.53 | 16 | 0.7 | 0.6 | 0.5 | 3 |
| q06 | education | method | 114.66 | 33 | 0.7 | 0.65 | 0.6 | 3 |
| q07 | education | limitation | 115.03 | 41 | 0.7 | 0.75 | 0.9 | 4 |
| q08 | health | method | 107.29 | 34 | 0.7 | 0.65 | 0.4 | 2 |
| q09 | health | comparison | 181.38 | 26 | 0.6 | 0.5 | 0.4 | 2 |
| q10 | health | application | 165.18 | 34 | 0.7 | 0.75 | 0.6 | 3 |
| q11 | engineering | application | 160.53 | 31 | 0.35 | 0.4 | 0.4 | 2 |
| q12 | engineering | method | 167.59 | 25 | 0.35 | 0.4 | 0.5 | 2 |
| q13 | engineering | trend | 146.9 | 33 | 0.6 | 0.5 | 0.4 | 2 |
| q14 | social_sciences | trend | 162.81 | 38 | 0.5 | 0.4 | 0.6 | 2 |
| q15 | social_sciences | method | 138.23 | 28 | 0.7 | 0.75 | 0.4 | 3 |
| q16 | business | method | 143.89 | 24 | 0.85 | 0.8 | 0.8 | 3 |
| q17 | business | application | 118.4 | 26 | 0.7 | 0.65 | 0.4 | 3 |
| q18 | agriculture | method | 119.15 | 29 | 0.6 | 0.5 | 0.25 | 2 |
| q19 | veterinary | method | 52.66 | 24 | 0.5 | 0.6 | 0.4 | 2 |
| q20 | linguistics | method | 113.2 | 27 | 0.6 | 0.5 | 0.6 | 3 |
| q21 | law | limitation | - | - | - | - | - | - |
| q22 | law | comparison | 161.51 | 36 | 0.6 | 0.5 | 0.6 | 3 |
| q23 | physics | method | 123.2 | 30 | 0.3 | 0.25 | 0.2 | 1 |
| q24 | chemistry | application | 139.19 | 25 | 0.6 | 0.5 | 0.4 | 2 |
| q25 | biology | method | 119.21 | 24 | 0.4 | 0.5 | 0.3 | 2 |
| q26 | tourism | trend | 121.16 | 25 | 0.6 | 0.5 | 0.4 | 2 |
| q27 | sports | method | 137.11 | 28 | 0.6 | 0.65 | 0.5 | 3 |
| q28 | multi_domain | cross | 135.08 | 36 | 0.7 | 0.75 | 0.8 | 3 |
| q29 | multi_domain | cross | 93.35 | 24 | 0.7 | 0.6 | 0.4 | 2 |
| q30 | edge_case | narrow | 100.91 | 20 | 0.3 | 0.25 | 0.2 | 1 |
