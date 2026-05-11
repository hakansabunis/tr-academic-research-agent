# Stage 1.5 — Data Audit (Sourcing & Quality)

*Goal: before committing Stage 2a's continued pre-training corpus, systematically inventory and audit candidate Turkish academic data sources. Avoid the Corpus Expansion Paradox (Stage 0 finding: more data ≠ better when register distribution shifts).*

---

## Current state — what we already have

| Source | Volume | Status | Notes |
|---|---|---|---|
| **YÖK Tez (thesis abstracts)** | 633,998 abstracts ≈ 200M tokens | ✅ Used in Stage 1 | Native, supervisor-reviewed, broad domain |
| **DergiPark (journal abstracts)** | 207,700 raw / 106,641 filtered ≈ 34M tokens | ✅ Harvested + filtered | Initially appeared corrupted; **false alarm** — Windows PowerShell console rendering issue, raw bytes are clean UTF-8 |

**Minimum baseline for Stage 2a:** YÖK Tez + DergiPark abstracts = ~234M tokens monolingual Turkish academic prose. Already enough to run continued pre-training. The audit answers: *should we add more?*

---

## Inventory — candidate additional sources

Sources are scored a priori on register fit, acquisition feasibility, and license clarity. Final go/no-go depends on Stage 1.5b (sampling) + 1.5c (pilot pre-train).

### Priority 1 — High yield, accessible

| # | Source | Est. volume | License | Acquisition | A priori register | Risks |
|---|---|---|---|---|---|---|
| 1 | **DergiPark full-text PDFs** | 200K-700K articles → 2-5B tokens after parse | Mixed (per-journal); most CC-BY or open | OAI-PMH (have IDs); HTTP PDF download + parse | High (peer-reviewed) | OCR/layout noise, ~1-2 MB × 200K = ~300 GB disk, parsing time |
| 2 | **TÜBA Açık Ders** | ~50-100M tokens | TÜBA open educational; CC-BY-NC likely | Scraping (tuba.gov.tr/acikders) | Very high (editor-supervised teaching prose) | Volume modest; scraping engineering ~1 day |
| 3 | **Anadolu Üniversitesi Açık Erişim** | ~50K theses + papers | Open access | OAI-PMH endpoint exists | High | Overlap with YÖK Tez likely; check dedup |

### Priority 2 — Probe to see if worth it

| # | Source | Est. volume | License | Acquisition | A priori register | Risks |
|---|---|---|---|---|---|---|
| 4 | **METU / ITÜ / Boğaziçi Open Courseware** | ~10-30M tokens | Mixed (mostly CC-BY-NC) | Scraping per-university | Mixed: some are Turkish, many English | Volume small, language coverage unclear |
| 5 | **DOAJ Turkish journals (non-DergiPark)** | ~20-50M tokens | Open access (DOAJ-curated) | DOAJ API + per-journal scraping | High (peer-reviewed) | Most Turkish journals are already on DergiPark — overlap risk |
| 6 | **TÜBİTAK Ulakbim TR Dizin** | ~50-100M tokens | Open metadata | API / OAI | High | Likely heavy overlap with DergiPark + YÖK Tez |
| 7 | **Wikipedia Turkish (academic categories only)** | ~100-200M tokens (filtered) | CC-BY-SA | Wikipedia dumps | Medium (encyclopedic ≠ academic) | Dilutes academic register if not filtered carefully |

### Priority 3 — Likely skip (wrong register or legal risk)

| # | Source | Why skip |
|---|---|---|
| 8 | TÜBA Yayınlar (academic books) | Mostly copyrighted; per-title permission needed; not scalable |
| 9 | Resmi Gazete teknik tebliğler | Bureaucratic register, not academic |
| 10 | TBMM komite raporları | Mostly political/legal register, not academic |
| 11 | Turkish translations of foreign academic books | Copyright-restricted; cannot redistribute training corpus |
| 12 | Twitter / Reddit / forum Turkish | Strongly negative register fit; would worsen the model |
| 13 | Common Crawl Turkish | Web-quality, mostly off-domain |

---

## Decision criteria (Stage 1.5c pilot pre-train)

For each Priority 1-2 source that gets to 1.5c, we run a small (~100M token, 1 epoch, LoRA rank=8) continued pre-train of Trendyol-7B and measure:

| Metric | Direction | Threshold to "include" |
|---|---|---|
| Held-out academic perplexity (on YÖK Tez 5% slice) | Lower is better | ≥ 5% relative drop |
| Held-out general perplexity (Wiki/web mix) | Should not rise much | ≤ 3% relative regression |
| 30-Q proxy eval (1-2 questions, citation accuracy) | Higher | Directional, not gated |

A source "wins" if both PPL conditions are met. A source "marginal" if academic PPL drops <5% but general PPL doesn't regress. A source "loses" if general PPL regresses >3%.

---

## Concrete next steps (1.5b — sampling)

Order of operations (fastest feedback first):

1. **DergiPark full-text PDF sampling.** Pull 100 random PDFs from existing DergiPark article IDs, parse with pdfplumber or PyMuPDF, check yield/quality. **~1 day.**
2. **TÜBA Açık Ders scraping.** Build crawler for tuba.gov.tr/acikders, pull 5K text fragments. **~1 day.**
3. **Anadolu Açık Erişim OAI probe.** Quick OAI-PMH list request; if endpoint live, harvest 5K samples for quality check. **~half day.**
4. **DOAJ Turkish journals API.** Quick API call to list TR-language OA journals not on DergiPark. **~half day.**
5. **METU/ITÜ/Boğaziçi OCW.** Crawl each, sample 1-2K Turkish text fragments. **~1-2 days.**

If any of (1-4) yields a clearly high-quality source, skip lower-priority items and move to 1.5c pilot pre-train.

---

## Hypothesis to test in 1.5c (revised after per-question re-analysis)

Original Stage 1 framing: STEM categories regressed in v2, audit should target STEM augmentation.

**Updated framing (2026-05-11):** Per-question STEM analysis (see `data/eval/stem_regression_analysis.md`) shows the category-level "STEM regression" was largely an artifact of n=1 per category. Across all 17 STEM-tagged questions, v2's net citation accuracy delta is **+0.65 (avg +0.04/question)** — i.e. STEM cohort is positive, just unevenly. There is no evidence of a systematic STEM deficiency in the embedding model.

**What this means for 1.5c.** The pilot continued pre-training does not need to compare STEM-only vs general data. Instead it should compare:
- Trendyol-7B vanilla (reference)
- Trendyol-7B + 100M tokens of DergiPark mixed-domain full-text (diverse, the natural Stage 2a candidate)

The success metric is overall academic register PPL drop, not a STEM-specific gain. STEM remains a useful test slice but is no longer the central hypothesis.

---

## Budget for this stage

| Item | Cost | Time |
|---|---|---|
| Sampling + spot-check scripts (1.5b) | $0 | 3-5 days dev time |
| Pilot pre-trains (1.5c), 4-5 sources × ~$10 | ~$50 | 3-5 days A100 |
| Decision write-up (1.5d) | $0 | 1 day |
| **Total** | **~$50** | **~2 weeks** |

Stage 2a depends on this audit's go/no-go output. Cap audit at 2 weeks; sources needing >2 days of bespoke engineering to even sample get deferred to "future work" instead of blocking.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Audit over-invests and delays Stage 2 | Medium | Hard 2-week cap; defer expensive sources |
| Copyright on full-text PDFs unclear per-journal | Medium | Restrict to CC-BY / explicit OA journals; per-publisher check |
| PDF parsing yields low after cleaning (headers/footers/refs noise) | High | Estimate post-cleaning yield from 100-sample test before scaling |
| Pilot PPL gain doesn't translate to downstream Stage 2 wins | Low | Also run lightweight 30-Q proxy eval for any source that passes PPL |
| Stage 1.5b/1.5c require domain-specific engineering (e.g., Açık Ders scraping is hard) | Medium | Drop hard-to-acquire sources; document as "future work" |

---

## Status

| Sub-stage | Status |
|---|---|
| 1.5a Inventory | ✅ Done (this document) |
| 1.5b Sampling & spot-check | ⬜ Next |
| 1.5c Pilot pre-train | ⬜ Pending |
| 1.5d Decision matrix | ⬜ Pending |

---

*Started: 2026-05-11*
