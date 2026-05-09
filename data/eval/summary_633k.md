# TürkResearcher — Evaluation Summary

- **Questions:** 30 (ok: 30, failed: 0)


## Overall Metrics

| Metric | Mean | Median | Min | Max | n |
|---|---|---|---|---|---|
| citation_accuracy | 0.603 | 0.7 | 0.1 | 0.85 | 30 |
| faithfulness | 0.585 | 0.625 | 0.15 | 0.9 | 30 |
| coverage | 0.492 | 0.6 | 0.2 | 0.9 | 30 |
| holistic_score | 2.633 | 3.0 | 1 | 4 | 30 |
| n_citations | 30.067 | 30.0 | 24 | 40 | 30 |
| n_chunks | 30.067 | 30.0 | 24 | 40 | 30 |
| max_score | 0.929 | 0.933 | 0.878 | 0.962 | 30 |
| latency_seconds | 105.822 | 111.59 | 46.01 | 146.53 | 30 |

## By Category

| Category | n | Cite Acc | Faithfulness | Coverage | Holistic | Latency (s) |
|---|---|---|---|---|---|---|
| computer_science | 4 | 0.212 | 0.288 | 0.25 | 1.5 | 67.922 |
| education | 3 | 0.75 | 0.7 | 0.6 | 3 | 96.113 |
| health | 3 | 0.8 | 0.767 | 0.633 | 3.333 | 96.73 |
| engineering | 3 | 0.733 | 0.783 | 0.7 | 3.333 | 125.787 |
| social_sciences | 2 | 0.775 | 0.725 | 0.55 | 3.5 | 121.135 |
| business | 2 | 0.475 | 0.45 | 0.45 | 2.5 | 90.81 |
| agriculture | 1 | 0.7 | 0.6 | 0.6 | 3 | 114.96 |
| veterinary | 1 | 0.3 | 0.4 | 0.25 | 2 | 82.1 |
| linguistics | 1 | 0.5 | 0.4 | 0.4 | 2 | 120.43 |
| law | 2 | 0.625 | 0.6 | 0.5 | 2.5 | 119.08 |
| physics | 1 | 0.3 | 0.2 | 0.2 | 1 | 133.27 |
| chemistry | 1 | 0.85 | 0.8 | 0.6 | 3 | 146.53 |
| biology | 1 | 0.6 | 0.5 | 0.3 | 2 | 121.12 |
| tourism | 1 | 0.7 | 0.6 | 0.4 | 3 | 119.46 |
| sports | 1 | 0.7 | 0.65 | 0.6 | 3 | 103.45 |
| multi_domain | 2 | 0.85 | 0.85 | 0.7 | 3.5 | 117.505 |
| edge_case | 1 | 0.3 | 0.25 | 0.2 | 1 | 108.69 |

## Per-Question

| ID | Category | Type | Lat (s) | #Cite | CitAcc | Faith | Cov | Hol |
|---|---|---|---|---|---|---|---|---|
| q01 | computer_science | trend | 89.92 | 38 | 0.3 | 0.4 | 0.3 | 2 |
| q02 | computer_science | method | 56.86 | 39 | 0.15 | 0.2 | 0.3 | 1 |
| q03 | computer_science | application | 46.01 | 24 | 0.1 | 0.15 | 0.2 | 1 |
| q04 | computer_science | comparison | 78.9 | 35 | 0.3 | 0.4 | 0.2 | 2 |
| q05 | education | trend | 81.51 | 26 | 0.85 | 0.8 | 0.6 | 3 |
| q06 | education | method | 103.49 | 24 | 0.7 | 0.65 | 0.6 | 3 |
| q07 | education | limitation | 103.34 | 32 | 0.7 | 0.65 | 0.6 | 3 |
| q08 | health | method | 106.95 | 29 | 0.85 | 0.8 | 0.6 | 3 |
| q09 | health | comparison | 99.59 | 31 | 0.7 | 0.6 | 0.6 | 3 |
| q10 | health | application | 83.65 | 32 | 0.85 | 0.9 | 0.7 | 4 |
| q11 | engineering | application | 130.12 | 31 | 0.85 | 0.9 | 0.9 | 4 |
| q12 | engineering | method | 120.98 | 30 | 0.65 | 0.7 | 0.6 | 3 |
| q13 | engineering | trend | 126.26 | 35 | 0.7 | 0.75 | 0.6 | 3 |
| q14 | social_sciences | trend | 127.05 | 28 | 0.85 | 0.8 | 0.7 | 4 |
| q15 | social_sciences | method | 115.22 | 24 | 0.7 | 0.65 | 0.4 | 3 |
| q16 | business | method | 66.47 | 24 | 0.6 | 0.5 | 0.6 | 3 |
| q17 | business | application | 115.15 | 26 | 0.35 | 0.4 | 0.3 | 2 |
| q18 | agriculture | method | 114.96 | 25 | 0.7 | 0.6 | 0.6 | 3 |
| q19 | veterinary | method | 82.1 | 35 | 0.3 | 0.4 | 0.25 | 2 |
| q20 | linguistics | method | 120.43 | 37 | 0.5 | 0.4 | 0.4 | 2 |
| q21 | law | limitation | 111.85 | 30 | 0.65 | 0.7 | 0.6 | 3 |
| q22 | law | comparison | 126.31 | 31 | 0.6 | 0.5 | 0.4 | 2 |
| q23 | physics | method | 133.27 | 34 | 0.3 | 0.2 | 0.2 | 1 |
| q24 | chemistry | application | 146.53 | 28 | 0.85 | 0.8 | 0.6 | 3 |
| q25 | biology | method | 121.12 | 30 | 0.6 | 0.5 | 0.3 | 2 |
| q26 | tourism | trend | 119.46 | 26 | 0.7 | 0.6 | 0.4 | 3 |
| q27 | sports | method | 103.45 | 24 | 0.7 | 0.65 | 0.6 | 3 |
| q28 | multi_domain | cross | 111.33 | 30 | 0.85 | 0.9 | 0.8 | 4 |
| q29 | multi_domain | cross | 123.68 | 24 | 0.85 | 0.8 | 0.6 | 3 |
| q30 | edge_case | narrow | 108.69 | 40 | 0.3 | 0.25 | 0.2 | 1 |
