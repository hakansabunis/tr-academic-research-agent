# TürkResearcher — Evaluation Summary

- **Questions:** 30 (ok: 30, failed: 0)


## Overall Metrics

| Metric | Mean | Median | Min | Max | n |
|---|---|---|---|---|---|
| citation_accuracy | 0.507 | 0.55 | 0.1 | 0.85 | 30 |
| faithfulness | 0.49 | 0.5 | 0.1 | 0.9 | 30 |
| coverage | 0.465 | 0.45 | 0.2 | 0.8 | 30 |
| holistic_score | 2.4 | 2.0 | 1 | 4 | 30 |
| n_citations | 32.8 | 31.0 | 22 | 47 | 30 |
| n_chunks | 32.8 | 31.0 | 22 | 47 | 30 |
| max_score | 0.929 | 0.931 | 0.898 | 0.953 | 30 |
| latency_seconds | 111.411 | 119.98 | 50.91 | 152.59 | 30 |

## By Category

| Category | n | Cite Acc | Faithfulness | Coverage | Holistic | Latency (s) |
|---|---|---|---|---|---|---|
| computer_science | 4 | 0.263 | 0.25 | 0.3 | 1.5 | 114.968 |
| education | 3 | 0.633 | 0.6 | 0.6 | 3 | 97.863 |
| health | 3 | 0.533 | 0.55 | 0.567 | 2.333 | 115.31 |
| engineering | 3 | 0.533 | 0.583 | 0.533 | 2.667 | 138.033 |
| social_sciences | 2 | 0.7 | 0.7 | 0.5 | 3 | 116.785 |
| business | 2 | 0.675 | 0.6 | 0.6 | 2.5 | 113.68 |
| agriculture | 1 | 0.6 | 0.5 | 0.4 | 2 | 114.16 |
| veterinary | 1 | 0.1 | 0.1 | 0.2 | 1 | 60.31 |
| linguistics | 1 | 0.3 | 0.25 | 0.4 | 2 | 83.1 |
| law | 2 | 0.4 | 0.325 | 0.275 | 2 | 103.32 |
| physics | 1 | 0.3 | 0.4 | 0.3 | 2 | 135.19 |
| chemistry | 1 | 0.7 | 0.65 | 0.6 | 3 | 111.73 |
| biology | 1 | 0.6 | 0.5 | 0.4 | 2 | 121.38 |
| tourism | 1 | 0.6 | 0.5 | 0.5 | 3 | 124.64 |
| sports | 1 | 0.6 | 0.7 | 0.4 | 3 | 119.36 |
| multi_domain | 2 | 0.7 | 0.7 | 0.7 | 3.5 | 120.25 |
| edge_case | 1 | 0.3 | 0.25 | 0.3 | 2 | 50.91 |

## Per-Question

| ID | Category | Type | Lat (s) | #Cite | CitAcc | Faith | Cov | Hol |
|---|---|---|---|---|---|---|---|---|
| q01 | computer_science | trend | 123.39 | 47 | 0.15 | 0.1 | 0.2 | 1 |
| q02 | computer_science | method | 126.27 | 41 | 0.3 | 0.25 | 0.2 | 1 |
| q03 | computer_science | application | 79.48 | 24 | 0.3 | 0.4 | 0.4 | 2 |
| q04 | computer_science | comparison | 130.73 | 40 | 0.3 | 0.25 | 0.4 | 2 |
| q05 | education | trend | 76.44 | 24 | 0.85 | 0.9 | 0.8 | 4 |
| q06 | education | method | 69.47 | 24 | 0.7 | 0.6 | 0.4 | 3 |
| q07 | education | limitation | 147.68 | 42 | 0.35 | 0.3 | 0.6 | 2 |
| q08 | health | method | 100.75 | 28 | 0.7 | 0.75 | 0.6 | 3 |
| q09 | health | comparison | 125.03 | 33 | 0.4 | 0.5 | 0.5 | 2 |
| q10 | health | application | 120.15 | 43 | 0.5 | 0.4 | 0.6 | 2 |
| q11 | engineering | application | 152.59 | 34 | 0.6 | 0.65 | 0.5 | 3 |
| q12 | engineering | method | 141.7 | 34 | 0.35 | 0.4 | 0.5 | 2 |
| q13 | engineering | trend | 119.81 | 44 | 0.65 | 0.7 | 0.6 | 3 |
| q14 | social_sciences | trend | 131.33 | 34 | 0.7 | 0.65 | 0.6 | 3 |
| q15 | social_sciences | method | 102.24 | 30 | 0.7 | 0.75 | 0.4 | 3 |
| q16 | business | method | 103.0 | 34 | 0.5 | 0.4 | 0.6 | 2 |
| q17 | business | application | 124.36 | 26 | 0.85 | 0.8 | 0.6 | 3 |
| q18 | agriculture | method | 114.16 | 30 | 0.6 | 0.5 | 0.4 | 2 |
| q19 | veterinary | method | 60.31 | 24 | 0.1 | 0.1 | 0.2 | 1 |
| q20 | linguistics | method | 83.1 | 39 | 0.3 | 0.25 | 0.4 | 2 |
| q21 | law | limitation | 63.42 | 24 | 0.5 | 0.4 | 0.3 | 2 |
| q22 | law | comparison | 143.22 | 39 | 0.3 | 0.25 | 0.25 | 2 |
| q23 | physics | method | 135.19 | 30 | 0.3 | 0.4 | 0.3 | 2 |
| q24 | chemistry | application | 111.73 | 26 | 0.7 | 0.65 | 0.6 | 3 |
| q25 | biology | method | 121.38 | 31 | 0.6 | 0.5 | 0.4 | 2 |
| q26 | tourism | trend | 124.64 | 30 | 0.6 | 0.5 | 0.5 | 3 |
| q27 | sports | method | 119.36 | 31 | 0.6 | 0.7 | 0.4 | 3 |
| q28 | multi_domain | cross | 124.73 | 45 | 0.7 | 0.8 | 0.8 | 4 |
| q29 | multi_domain | cross | 115.77 | 31 | 0.7 | 0.6 | 0.6 | 3 |
| q30 | edge_case | narrow | 50.91 | 22 | 0.3 | 0.25 | 0.3 | 2 |
