"""Live academic search tools — used when local Chroma corpus is insufficient.

Each function returns a list of `RetrievedChunk` objects, compatible with the
local retriever, so the synthesiser/writer agents can use them
indistinguishably.

Sources:
    - OpenAlex     — broad scholarly graph (~250M works), Turkish content too
    - Semantic Scholar — citation graph + abstracts, free API
    - DergiPark    — Turkish journals via OAI-PMH (recent date range)

Polite usage: 1-2s timeouts, single retry, descriptive User-Agent.
"""
from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlencode

import requests

from ..schemas import RetrievedChunk

USER_AGENT = "tr-academic-research-agent/0.1 (academic project; +https://huggingface.co/hakansabunis)"
DEFAULT_TIMEOUT = 12

# ─────────────────────── OpenAlex ───────────────────────


def _openalex_reconstruct_abstract(inverted_idx: dict[str, list[int]] | None) -> str:
    if not inverted_idx:
        return ""
    pairs: list[tuple[int, str]] = []
    for word, positions in inverted_idx.items():
        for p in positions:
            pairs.append((p, word))
    pairs.sort()
    return " ".join(w for _, w in pairs)


def search_openalex(query: str, *, k: int = 8, language: str | None = None) -> list[RetrievedChunk]:
    """Search OpenAlex via REST. No auth required. Optional language filter (e.g. 'tr')."""
    # NB: `host_venue` was deprecated by OpenAlex; use `primary_location` only.
    params = {
        "search": query,
        "per-page": k,
        "select": "id,doi,display_name,publication_year,authorships,abstract_inverted_index,language,primary_location",
    }
    if language:
        params["filter"] = f"language:{language}"
    url = f"https://api.openalex.org/works?{urlencode(params)}"

    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:
            return []
        data = r.json()
    except (requests.RequestException, ValueError):
        return []

    out: list[RetrievedChunk] = []
    for w in data.get("results", []):
        title = w.get("display_name") or ""
        abstract = _openalex_reconstruct_abstract(w.get("abstract_inverted_index"))
        if not title and not abstract:
            continue

        authors = ", ".join(
            (a.get("author", {}) or {}).get("display_name", "")
            for a in (w.get("authorships") or [])
            if a
        )
        venue = ""
        primary = w.get("primary_location") or {}
        source = (primary.get("source") or {}) if primary else {}
        venue = source.get("display_name") or ""

        oa_id = w.get("id", "")
        doi = w.get("doi") or ""
        url_link = doi if doi else oa_id

        out.append(RetrievedChunk(
            tez_no=oa_id.rsplit("/", 1)[-1] if oa_id else "",
            title_tr=title,
            author=authors,
            advisor=None,
            location=venue or None,
            year=w.get("publication_year") or None,
            abstract_tr=abstract,
            score=0.5,  # live results don't have local-Chroma scores
            pdf_url=url_link or None,
        ))
    return out


# ──────────────────── Semantic Scholar ────────────────────


def search_semantic_scholar(query: str, *, k: int = 8) -> list[RetrievedChunk]:
    """Free public API. Rate-limited; 1 retry on 429."""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": k,
        "fields": "paperId,title,abstract,authors,year,url,venue,externalIds",
    }
    try:
        r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=DEFAULT_TIMEOUT)
        if r.status_code == 429:
            time.sleep(2.0)
            r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:
            return []
        data = r.json()
    except (requests.RequestException, ValueError):
        return []

    out: list[RetrievedChunk] = []
    for p in data.get("data", []):
        title = p.get("title") or ""
        abstract = p.get("abstract") or ""
        if not title and not abstract:
            continue
        authors = ", ".join((a or {}).get("name", "") for a in (p.get("authors") or []))
        out.append(RetrievedChunk(
            tez_no=p.get("paperId", ""),
            title_tr=title,
            author=authors,
            advisor=None,
            location=p.get("venue") or None,
            year=p.get("year") or None,
            abstract_tr=abstract,
            score=0.5,
            pdf_url=p.get("url") or None,
        ))
    return out


# ──────────────────── DergiPark (OAI-PMH live) ────────────────────


_DERGIPARK_NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "xml": "http://www.w3.org/XML/1998/namespace",
}


def _dp_text_lang(elements, prefer: str = "tr") -> str:
    if not elements:
        return ""
    for el in elements:
        lang = el.attrib.get(f"{{{_DERGIPARK_NS['xml']}}}lang", "")
        if lang.startswith(prefer):
            return (el.text or "").strip()
    for el in elements:
        if el.text and el.text.strip():
            return el.text.strip()
    return ""


def search_dergipark(query: str, *, k: int = 8, days_back: int = 365) -> list[RetrievedChunk]:
    """Approximate DergiPark search by harvesting the most recent OAI-PMH page
    (last `days_back` days) and filtering locally by query term presence in
    title or abstract. Crude but works without a documented search endpoint."""
    from datetime import datetime, timedelta

    until = datetime.utcnow().date()
    since = until - timedelta(days=days_back)

    params = {
        "verb": "ListRecords",
        "metadataPrefix": "oai_dc",
        "from": since.isoformat(),
        "until": until.isoformat(),
    }

    try:
        r = requests.get(
            "https://dergipark.org.tr/api/public/oai/",
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
    except (requests.RequestException, ET.ParseError):
        return []

    list_records = root.find("oai:ListRecords", _DERGIPARK_NS)
    if list_records is None:
        return []

    q_lower = query.lower()
    out: list[RetrievedChunk] = []
    for rec in list_records.findall("oai:record", _DERGIPARK_NS):
        meta = rec.find("oai:metadata", _DERGIPARK_NS)
        if meta is None:
            continue
        dc = meta.find("oai_dc:dc", _DERGIPARK_NS)
        if dc is None:
            continue

        title = _dp_text_lang(dc.findall("dc:title", _DERGIPARK_NS), "tr")
        abstract = _dp_text_lang(dc.findall("dc:description", _DERGIPARK_NS), "tr")
        if not (q_lower in title.lower() or q_lower in abstract.lower()):
            continue

        creators = [el.text.strip() for el in dc.findall("dc:creator", _DERGIPARK_NS) if el.text]
        sources = [el.text.strip() for el in dc.findall("dc:source", _DERGIPARK_NS) if el.text]
        identifiers = [el.text.strip() for el in dc.findall("dc:identifier", _DERGIPARK_NS) if el.text]
        dates = [el.text.strip() for el in dc.findall("dc:date", _DERGIPARK_NS) if el.text]

        canonical_url = next((u for u in identifiers if "dergipark.org.tr" in u), identifiers[0] if identifiers else "")
        year = int(dates[0][:4]) if dates and dates[0][:4].isdigit() else None

        header = rec.find("oai:header", _DERGIPARK_NS)
        oai_id_el = header.find("oai:identifier", _DERGIPARK_NS) if header is not None else None
        oai_id = oai_id_el.text if oai_id_el is not None else ""
        article_id = oai_id.rsplit("/", 1)[-1] if oai_id else ""

        out.append(RetrievedChunk(
            tez_no=article_id,
            title_tr=title,
            author="; ".join(creators),
            advisor=None,
            location=sources[0] if sources else None,
            year=year,
            abstract_tr=abstract,
            score=0.5,
            pdf_url=canonical_url or None,
        ))
        if len(out) >= k:
            break

    return out


# ──────────────────── Aggregator ────────────────────


def search_live(query: str, *, k_each: int = 6, sources: list[str] | None = None) -> dict[str, list[RetrievedChunk]]:
    """Run the requested live sources and return per-source results."""
    sources = sources or ["openalex", "semantic_scholar", "dergipark"]
    out: dict[str, list[RetrievedChunk]] = {}
    if "openalex" in sources:
        out["openalex"] = search_openalex(query, k=k_each)
    if "semantic_scholar" in sources:
        out["semantic_scholar"] = search_semantic_scholar(query, k=k_each)
    if "dergipark" in sources:
        out["dergipark"] = search_dergipark(query, k=k_each)
    return out
