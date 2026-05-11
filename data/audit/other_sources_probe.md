# Stage 1.5b — Other Sources Probe

*Probed: 2026-05-11. Each entry shows endpoint accessibility, volume estimate (where available), and recommendation.*

## 1. DOAJ (Directory of Open Access Journals) — Turkish
- **Status:** ✅ live
- **Turkish journals indexed:** 0
- **Turkish-language articles:** 0
- **Sample journals:**

**Verdict:** Likely overlaps heavily with DergiPark (most Turkish OA journals are on DergiPark). Worth a dedup check before harvesting.

## 2. Anadolu Üniversitesi Açık Erişim
- **Status:** ❌ no OAI endpoint responded with OAI-PMH content

## 3. TÜBA Açık Ders
- **Status:** probed
  - `https://tuba.gov.tr/tr/yayinlar/acik-ders-malzemeleri` → final `https://tuba.gov.tr/tr/yayinlar/acik-ders-malzemeleri` (http 404, 0 bytes)
  - `https://acikders.tuba.gov.tr/` — error: HTTPSConnectionPool(host='acikders.tuba.gov.tr', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1028)')))
  - `https://www.tuba.gov.tr/tr/yayinlar/acik-ders-malzemeleri` → final `https://www.tuba.gov.tr/tr/yayinlar/acik-ders-malzemeleri` (http 404, 0 bytes)

**Verdict:** TÜBA's site is mostly an institutional homepage; open courseware (if it exists) is not at a predictable URL. Likely requires manual landing-page exploration. Defer to manual investigation.

## 4. TÜBİTAK Ulakbim TR Dizin
- **Status:** probed
  - `https://search.trdizin.gov.tr/oai/request` (http 200, —)
  - `https://trdizin.gov.tr/api/search/publication` (http 404, —)
  - `https://atif.trdizin.gov.tr/oai` — error: HTTPSConnectionPool(host='atif.trdizin.gov.tr', port=443): Max retries exceeded with url: /oai?verb=Identify (Caused by NameResolutionError("HTTPSConnection(host='atif.trdizin.gov.tr', port=443): Failed to resolve 'atif.trdizin.gov.tr' ([Errno 11001] getaddrinfo failed)"))

**Verdict:** TR Dizin is an *index* (metadata aggregator); content typically links back to DergiPark. Even if OAI is accessible, expected overlap with DergiPark is near-100%.

## 5. Major Turkish University OAI endpoints

| University | Endpoint | Status | Records (est) |
|---|---|---|---|
| METU (ODTÜ) | `https://open.metu.edu.tr/oai/request` | ❌ HTTPSConnectionPool(host='open.metu.edu.tr', port= | — |
| ITÜ | `https://polen.itu.edu.tr/oai/request` | ✅ OAI live | 67,765 |
| Boğaziçi | `https://acikerisim.boun.edu.tr/oai/request` | ❌ HTTPSConnectionPool(host='acikerisim.boun.edu.tr', | — |
| Bilkent | `https://repository.bilkent.edu.tr/oai/request` | http 404 | ? |
| Sabancı | `https://research.sabanciuniv.edu/oai/request` | http 404 | ? |
| Hacettepe | `https://repository.hacettepe.edu.tr/oai/request` | ❌ ('Connection aborted.', ConnectionResetError(10054 | — |
| İstanbul Ü. | `https://acikerisim.istanbul.edu.tr/oai/request` | ❌ HTTPSConnectionPool(host='acikerisim.istanbul.edu. | — |
| Ankara Ü. | `https://acikerisim.ankara.edu.tr/oai/request` | ❌ HTTPSConnectionPool(host='acikerisim.ankara.edu.tr | — |

**Verdict:** Universities with live OAI endpoints overlap with YÖK Tez (theses) and with each other (cross-author publications). Net new content needs explicit measurement via dedup against existing corpus.

## Overall takeaway

Most candidate Turkish academic sources funnel through two aggregators:
- **YÖK Tez** — theses (already harvested, 633K abstracts)
- **DergiPark** — journal articles (already harvested abstracts, full-text PDFs in 1.5b)

Additional sources will mostly *duplicate* what we already have. Real net-new content requires:
1. DergiPark **full-text** (vs abstracts only) — biggest potential gain
2. Institutional repositories with **non-thesis/non-journal** content (lecture notes, technical reports) — TÜBA Açık Ders is the cleanest candidate but endpoint discovery is manual
3. University OAI endpoints — useful only if they expose content beyond YÖK Tez (e.g., faculty book chapters, working papers); needs dedup verification