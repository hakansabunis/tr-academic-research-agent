"""Quick probes for non-DergiPark candidate sources.

Touches each source with 1-3 lightweight requests to gauge:
  - Is endpoint alive?
  - What format is the data in?
  - Rough estimate of volume
  - Initial register check (1-3 raw samples)

Writes findings to data/audit/other_sources_probe.md
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "audit" / "other_sources_probe.md"
HEADERS = {"User-Agent": "tr-academic-audit/0.1"}
TIMEOUT = 30


def probe_doaj() -> dict:
    """DOAJ — Directory of Open Access Journals. Filter by Turkish language."""
    print("\n=== DOAJ ===", file=sys.stderr)
    try:
        # Search journals in Turkish
        url = "https://doaj.org/api/search/journals/bibjson.language.exact:Turkish"
        r = requests.get(url, params={"pageSize": 10}, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return {"status": "fail", "reason": f"http {r.status_code}"}
        data = r.json()
        total = data.get("total", 0)
        results = data.get("results", [])
        sample = []
        for j in results[:5]:
            bib = j.get("bibjson", {})
            sample.append({
                "title": bib.get("title"),
                "publisher": (bib.get("publisher") or {}).get("name"),
                "url": (bib.get("link") or [{}])[0].get("url"),
                "lang": bib.get("language"),
                "subject_areas": [s.get("term") for s in (bib.get("subject") or [])][:3],
            })
        # Also count articles in DOAJ for Turkish journals
        url2 = "https://doaj.org/api/search/articles/bibjson.journal.language.exact:Turkish"
        r2 = requests.get(url2, params={"pageSize": 1}, headers=HEADERS, timeout=TIMEOUT)
        article_total = r2.json().get("total", 0) if r2.status_code == 200 else "?"
        return {
            "status": "ok",
            "journals_total": total,
            "articles_total": article_total,
            "sample_journals": sample,
        }
    except Exception as e:
        return {"status": "fail", "reason": str(e)}


def probe_anadolu_oai() -> dict:
    """Anadolu Üniversitesi Açık Erişim — OAI-PMH endpoint."""
    print("\n=== Anadolu Açık Erişim ===", file=sys.stderr)
    candidates = [
        "https://earsiv.anadolu.edu.tr/oai/request",
        "https://earsiv.anadolu.edu.tr/oai",
        "https://earsiv.anadolu.edu.tr/cgi-bin/oai-pmh",
        "https://acikerisim.anadolu.edu.tr/oai/request",
    ]
    for url in candidates:
        try:
            r = requests.get(url, params={"verb": "Identify"}, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 200 and b"OAI-PMH" in r.content:
                # Get record count via ListRecords first page
                r2 = requests.get(
                    url,
                    params={"verb": "ListRecords", "metadataPrefix": "oai_dc"},
                    headers=HEADERS, timeout=TIMEOUT,
                )
                # Try to find resumptionToken with completeListSize attr
                content = r2.content.decode("utf-8", errors="replace")
                m = re.search(r'completeListSize="(\d+)"', content)
                size = int(m.group(1)) if m else None
                return {
                    "status": "ok",
                    "endpoint": url,
                    "first_page_status": r2.status_code,
                    "complete_list_size": size,
                }
            else:
                print(f"  {url}: http {r.status_code}, has_OAI={'OAI-PMH' in r.content!r}", file=sys.stderr)
        except Exception as e:
            print(f"  {url}: {e}", file=sys.stderr)
    return {"status": "fail", "reason": "no OAI endpoint responded with OAI-PMH content"}


def probe_tuba_acikders() -> dict:
    """TÜBA Açık Ders — open courseware."""
    print("\n=== TÜBA Açık Ders ===", file=sys.stderr)
    candidates = [
        "https://tuba.gov.tr/tr/yayinlar/acik-ders-malzemeleri",
        "https://acikders.tuba.gov.tr/",
        "https://www.tuba.gov.tr/tr/yayinlar/acik-ders-malzemeleri",
    ]
    findings = []
    for url in candidates:
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            content_preview = r.text[:300] if r.status_code == 200 else ""
            findings.append({
                "url": url,
                "status": r.status_code,
                "final_url": r.url,
                "content_len": len(r.text) if r.status_code == 200 else 0,
                "preview": content_preview,
            })
        except Exception as e:
            findings.append({"url": url, "error": str(e)})
    return {"status": "probed", "candidates": findings}


def probe_tubitak_ulakbim() -> dict:
    """TÜBİTAK Ulakbim TR Dizin — academic journal index."""
    print("\n=== TÜBİTAK Ulakbim ===", file=sys.stderr)
    candidates = [
        "https://search.trdizin.gov.tr/oai/request",
        "https://trdizin.gov.tr/api/search/publication",
        "https://atif.trdizin.gov.tr/oai",
    ]
    findings = []
    for url in candidates:
        try:
            r = requests.get(url, params={"verb": "Identify"}, headers=HEADERS, timeout=TIMEOUT)
            findings.append({
                "url": url,
                "status": r.status_code,
                "looks_oai": b"OAI-PMH" in r.content if r.status_code == 200 else False,
                "preview": r.text[:200] if r.status_code == 200 else "",
            })
        except Exception as e:
            findings.append({"url": url, "error": str(e)})
    return {"status": "probed", "candidates": findings}


def probe_universities_oai() -> dict:
    """Major Turkish universities' open access OAI endpoints."""
    print("\n=== University OAI endpoints ===", file=sys.stderr)
    universities = [
        ("METU (ODTÜ)", "https://open.metu.edu.tr/oai/request"),
        ("ITÜ", "https://polen.itu.edu.tr/oai/request"),
        ("Boğaziçi", "https://acikerisim.boun.edu.tr/oai/request"),
        ("Bilkent", "https://repository.bilkent.edu.tr/oai/request"),
        ("Sabancı", "https://research.sabanciuniv.edu/oai/request"),
        ("Hacettepe", "https://repository.hacettepe.edu.tr/oai/request"),
        ("İstanbul Ü.", "https://acikerisim.istanbul.edu.tr/oai/request"),
        ("Ankara Ü.", "https://acikerisim.ankara.edu.tr/oai/request"),
    ]
    findings = []
    for name, url in universities:
        try:
            r = requests.get(url, params={"verb": "Identify"}, headers=HEADERS, timeout=15)
            is_oai = r.status_code == 200 and b"OAI-PMH" in r.content
            findings.append({
                "name": name, "url": url, "status": r.status_code, "is_oai": is_oai,
            })
            if is_oai:
                # Try to count records
                r2 = requests.get(
                    url,
                    params={"verb": "ListRecords", "metadataPrefix": "oai_dc"},
                    headers=HEADERS, timeout=15,
                )
                content = r2.content.decode("utf-8", errors="replace")
                m = re.search(r'completeListSize="(\d+)"', content)
                size = int(m.group(1)) if m else None
                findings[-1]["complete_list_size"] = size
            time.sleep(0.5)
        except Exception as e:
            findings.append({"name": name, "url": url, "error": str(e)[:100]})
    return {"status": "probed", "universities": findings}


def render_md(results: dict) -> str:
    lines = ["# Stage 1.5b — Other Sources Probe", ""]
    lines.append(f"*Probed: 2026-05-11. Each entry shows endpoint accessibility, "
                 "volume estimate (where available), and recommendation.*")
    lines.append("")

    # DOAJ
    lines.append("## 1. DOAJ (Directory of Open Access Journals) — Turkish")
    doaj = results["doaj"]
    if doaj["status"] == "ok":
        lines.append(f"- **Status:** ✅ live")
        lines.append(f"- **Turkish journals indexed:** {doaj['journals_total']:,}")
        lines.append(f"- **Turkish-language articles:** {doaj['articles_total']:,}")
        lines.append(f"- **Sample journals:**")
        for s in doaj["sample_journals"]:
            lines.append(f"  - *{s['title']}* — {s.get('publisher','?')}")
        lines.append("")
        lines.append("**Verdict:** Likely overlaps heavily with DergiPark (most Turkish OA "
                     "journals are on DergiPark). Worth a dedup check before harvesting.")
    else:
        lines.append(f"- **Status:** ❌ {doaj.get('reason','fail')}")
    lines.append("")

    # Anadolu
    lines.append("## 2. Anadolu Üniversitesi Açık Erişim")
    a = results["anadolu"]
    if a["status"] == "ok":
        lines.append(f"- **Status:** ✅ OAI endpoint live at `{a['endpoint']}`")
        lines.append(f"- **Total records:** {a.get('complete_list_size','?')}")
        lines.append("")
        lines.append("**Verdict:** Likely overlaps with YÖK Tez (theses are also indexed there). "
                     "Worth dedup probe before harvesting.")
    else:
        lines.append(f"- **Status:** ❌ {a.get('reason','endpoint not found')}")
    lines.append("")

    # TÜBA
    lines.append("## 3. TÜBA Açık Ders")
    t = results["tuba"]
    lines.append("- **Status:** probed")
    for c in t["candidates"]:
        if "error" in c:
            lines.append(f"  - `{c['url']}` — error: {c['error']}")
        else:
            lines.append(f"  - `{c['url']}` → final `{c['final_url']}` "
                         f"(http {c['status']}, {c['content_len']:,} bytes)")
    lines.append("")
    lines.append("**Verdict:** TÜBA's site is mostly an institutional homepage; open "
                 "courseware (if it exists) is not at a predictable URL. Likely requires "
                 "manual landing-page exploration. Defer to manual investigation.")
    lines.append("")

    # TÜBİTAK Ulakbim
    lines.append("## 4. TÜBİTAK Ulakbim TR Dizin")
    u = results["tubitak"]
    lines.append("- **Status:** probed")
    for c in u["candidates"]:
        if "error" in c:
            lines.append(f"  - `{c['url']}` — error: {c['error']}")
        else:
            tag = "✅ OAI" if c.get("looks_oai") else "—"
            lines.append(f"  - `{c['url']}` (http {c['status']}, {tag})")
    lines.append("")
    lines.append("**Verdict:** TR Dizin is an *index* (metadata aggregator); content typically "
                 "links back to DergiPark. Even if OAI is accessible, expected overlap with "
                 "DergiPark is near-100%.")
    lines.append("")

    # Universities
    lines.append("## 5. Major Turkish University OAI endpoints")
    lines.append("")
    lines.append("| University | Endpoint | Status | Records (est) |")
    lines.append("|---|---|---|---|")
    u2 = results["universities"]
    for r in u2["universities"]:
        if "error" in r:
            lines.append(f"| {r['name']} | `{r['url']}` | ❌ {r['error'][:50]} | — |")
        else:
            tag = "✅ OAI live" if r.get("is_oai") else f"http {r['status']}"
            size = r.get("complete_list_size", "?")
            size_str = f"{size:,}" if isinstance(size, int) else "?"
            lines.append(f"| {r['name']} | `{r['url']}` | {tag} | {size_str} |")
    lines.append("")
    lines.append("**Verdict:** Universities with live OAI endpoints overlap with YÖK Tez "
                 "(theses) and with each other (cross-author publications). Net new content "
                 "needs explicit measurement via dedup against existing corpus.")
    lines.append("")

    # Overall takeaway
    lines.append("## Overall takeaway")
    lines.append("")
    lines.append("Most candidate Turkish academic sources funnel through two aggregators:")
    lines.append("- **YÖK Tez** — theses (already harvested, 633K abstracts)")
    lines.append("- **DergiPark** — journal articles (already harvested abstracts, full-text PDFs in 1.5b)")
    lines.append("")
    lines.append("Additional sources will mostly *duplicate* what we already have. Real net-new "
                 "content requires:")
    lines.append("1. DergiPark **full-text** (vs abstracts only) — biggest potential gain")
    lines.append("2. Institutional repositories with **non-thesis/non-journal** content (lecture "
                 "notes, technical reports) — TÜBA Açık Ders is the cleanest candidate but "
                 "endpoint discovery is manual")
    lines.append("3. University OAI endpoints — useful only if they expose content beyond YÖK Tez "
                 "(e.g., faculty book chapters, working papers); needs dedup verification")
    return "\n".join(lines)


def main():
    results = {
        "doaj": probe_doaj(),
        "anadolu": probe_anadolu_oai(),
        "tuba": probe_tuba_acikders(),
        "tubitak": probe_tubitak_ulakbim(),
        "universities": probe_universities_oai(),
    }
    md = render_md(results)
    OUT.write_text(md, encoding="utf-8")
    print(f"\n[+] Wrote {OUT}")
    # Also save raw json
    (OUT.parent / "other_sources_probe.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
