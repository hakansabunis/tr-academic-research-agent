"""DergiPark OAI-PMH harvester.

Streams all DergiPark journal article metadata via OAI-PMH (Dublin Core
records) and writes them as JSONL. Resumable on crash / network drop.

Endpoint: https://dergipark.org.tr/api/public/oai/
Spec: http://www.openarchives.org/OAI/openarchivesprotocol.html

Output:
  data/raw/dergipark.jsonl              — one record per line
  data/raw/dergipark.state.json         — resumption token + checkpoint

Design:
- Persists every page to disk. On crash, re-run; resumes from resumption_token.
- Polite delay between requests (default 0.5s) to avoid hammering the API.
- Single-pass: one record per OAI identifier (no duplicates within a single run).

Schema (unified with theses where possible — see scripts/06_unify_corpora.py):
  {
    "oai_id":      "oai:dergipark.org.tr:article/1704902",
    "article_id":  "1704902",
    "title_tr":    "...",
    "title_en":    "...",            # may be empty
    "authors":     "Özaydın, H.; Gümüş, N.; ...",
    "subjects":    ["Tourism Geography", ...],
    "abstract_tr": "...",
    "abstract_en": "...",            # may be empty
    "publisher":   "Ordu Üniversitesi",
    "journal":     "Ünye İİBF Dergisi, Vol. 7 No. 2",
    "year":        2025,
    "date":        "2025-05-23",
    "language":    "tr",
    "type":        "article",
    "url":         "https://dergipark.org.tr/.../article/1704902",
    "datestamp":   "2026-02-02",     # OAI datestamp
    "set_spec":    "54"
  }
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode

import requests

_RESUMPTION_TOKEN_RE = re.compile(
    r"<resumptionToken[^>]*>([^<]+)</resumptionToken>",
    re.IGNORECASE,
)


def _extract_resumption_token(content_bytes: bytes) -> str | None:
    """Regex-based fallback when the page is malformed XML but the
    resumptionToken element itself is intact."""
    try:
        text = content_bytes.decode("utf-8", errors="replace")
    except Exception:
        return None
    m = _RESUMPTION_TOKEN_RE.search(text)
    if m:
        return m.group(1).strip()
    return None

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
JSONL_PATH = RAW_DIR / "dergipark.jsonl"
STATE_PATH = RAW_DIR / "dergipark.state.json"

ENDPOINT = "https://dergipark.org.tr/api/public/oai/"
NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "xml": "http://www.w3.org/XML/1998/namespace",
}

USER_AGENT = "tr-academic-research-agent/0.1 (academic project; +https://huggingface.co/hakansabunis)"


def _text_with_lang(elements, prefer_lang: str | None = None) -> str:
    """Return text from one of the elements, preferring xml:lang match."""
    if not elements:
        return ""
    if prefer_lang:
        for el in elements:
            lang = el.attrib.get(f"{{{NS['xml']}}}lang", "")
            if lang.startswith(prefer_lang):
                return (el.text or "").strip()
    # fallback: first non-empty
    for el in elements:
        if el.text and el.text.strip():
            return el.text.strip()
    return ""


def _all_texts(elements) -> list[str]:
    return [el.text.strip() for el in elements if el.text and el.text.strip()]


def parse_record(record_el: ET.Element) -> dict | None:
    header = record_el.find("oai:header", NS)
    if header is None:
        return None

    # Skip deleted records (OAI-PMH spec)
    if header.attrib.get("status") == "deleted":
        return None

    oai_id_el = header.find("oai:identifier", NS)
    datestamp_el = header.find("oai:datestamp", NS)
    set_specs = [el.text for el in header.findall("oai:setSpec", NS) if el.text]

    metadata = record_el.find("oai:metadata", NS)
    if metadata is None:
        return None
    dc = metadata.find("oai_dc:dc", NS)
    if dc is None:
        return None

    titles = dc.findall("dc:title", NS)
    creators = dc.findall("dc:creator", NS)
    subjects = dc.findall("dc:subject", NS)
    descriptions = dc.findall("dc:description", NS)
    publishers = dc.findall("dc:publisher", NS)
    dates = dc.findall("dc:date", NS)
    types = dc.findall("dc:type", NS)
    identifiers = dc.findall("dc:identifier", NS)
    sources = dc.findall("dc:source", NS)
    languages = dc.findall("dc:language", NS)

    oai_id = oai_id_el.text if oai_id_el is not None else ""
    article_id = oai_id.rsplit("/", 1)[-1] if oai_id else ""

    title_tr = _text_with_lang(titles, "tr")
    title_en = _text_with_lang(titles, "en")
    abstract_tr = _text_with_lang(descriptions, "tr")
    abstract_en = _text_with_lang(descriptions, "en")

    # Pick canonical URL = first dc:identifier that looks like a dergipark URL
    canonical_url = ""
    for ident in identifiers:
        if ident.text and "dergipark.org.tr" in ident.text:
            canonical_url = ident.text.strip()
            break
    if not canonical_url and identifiers:
        first = identifiers[0].text
        canonical_url = first.strip() if first else ""

    date_str = (dates[0].text or "").strip() if dates else ""
    year = 0
    if date_str and len(date_str) >= 4 and date_str[:4].isdigit():
        year = int(date_str[:4])

    return {
        "oai_id": oai_id,
        "article_id": article_id,
        "title_tr": title_tr,
        "title_en": title_en,
        "authors": "; ".join(_all_texts(creators)),
        "subjects": _all_texts(subjects),
        "abstract_tr": abstract_tr,
        "abstract_en": abstract_en,
        "publisher": (publishers[0].text or "").strip() if publishers else "",
        "journal": (sources[0].text or "").strip() if sources else "",
        "year": year,
        "date": date_str,
        "language": (languages[0].text or "").strip() if languages else "",
        "type": (types[0].text or "").strip() if types else "",
        "url": canonical_url,
        "datestamp": (datestamp_el.text or "").strip() if datestamp_el is not None else "",
        "set_spec": ",".join(set_specs),
    }


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"resumption_token": None, "harvested": 0, "pages": 0, "completed": False}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_page(params: dict, *, max_retries: int = 5, timeout: int = 60) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    backoff = 2
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(ENDPOINT, params=params, headers=headers, timeout=timeout)
            if r.status_code == 200:
                return r.content
            if r.status_code in (429, 502, 503, 504):
                wait = backoff * attempt
                print(f"  [warn] {r.status_code}; backing off {wait}s (attempt {attempt}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
                continue
            r.raise_for_status()
        except requests.RequestException as e:
            wait = backoff * attempt
            print(f"  [warn] network error: {e}; retry in {wait}s ({attempt}/{max_retries})", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch after {max_retries} attempts: {params}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-date", default=None,
                        help="Lower bound on OAI datestamp (YYYY-MM-DD). Default: from beginning.")
    parser.add_argument("--until-date", default=None,
                        help="Upper bound on OAI datestamp (YYYY-MM-DD). Default: until now.")
    parser.add_argument("--set", dest="set_spec", default=None, help="Optional OAI set restriction")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Polite delay between page requests (seconds)")
    parser.add_argument("--max-pages", type=int, default=None,
                        help="Stop after N pages (debug). Default: harvest everything.")
    parser.add_argument("--reset", action="store_true", help="Discard prior state and start fresh")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if args.reset:
        if STATE_PATH.exists():
            STATE_PATH.unlink()
        if JSONL_PATH.exists():
            JSONL_PATH.unlink()

    state = load_state()
    if state["completed"]:
        print(f"[=] Harvest already completed: {state['harvested']:,} records in {JSONL_PATH}")
        print(f"    Use --reset to re-harvest from scratch.")
        return 0

    print(f"[+] DergiPark OAI-PMH harvest -> {JSONL_PATH}")
    print(f"    Already harvested: {state['harvested']:,} records, {state['pages']} pages")

    out_fp = JSONL_PATH.open("a", encoding="utf-8", buffering=1)
    pages_this_run = 0
    records_this_run = 0
    parse_retry_count = 0
    MAX_PARSE_RETRIES = 5
    t0 = time.time()

    try:
        while True:
            if args.max_pages is not None and pages_this_run >= args.max_pages:
                print(f"[=] Stopped: --max-pages={args.max_pages}")
                break

            if state["resumption_token"]:
                params = {"verb": "ListRecords", "resumptionToken": state["resumption_token"]}
            else:
                params = {"verb": "ListRecords", "metadataPrefix": "oai_dc"}
                if args.from_date:
                    params["from"] = args.from_date
                if args.until_date:
                    params["until"] = args.until_date
                if args.set_spec:
                    params["set"] = args.set_spec

            content = fetch_page(params)
            try:
                root = ET.fromstring(content)
                parse_retry_count = 0  # reset on success
            except ET.ParseError as e:
                parse_retry_count += 1
                debug_path = RAW_DIR / f"dergipark.error_page_{state['pages']}_attempt{parse_retry_count}.xml"
                debug_path.write_bytes(content)
                print(
                    f"[!] XML parse error (attempt {parse_retry_count}/{MAX_PARSE_RETRIES}): {e}",
                    file=sys.stderr,
                )
                print(f"    Wrote {debug_path}", file=sys.stderr)
                if parse_retry_count >= MAX_PARSE_RETRIES:
                    # Last-resort bypass: extract resumptionToken via regex from
                    # the malformed response and jump to the next page. We lose
                    # this page's ~100 records but the harvest can continue.
                    bypass_token = _extract_resumption_token(content)
                    if bypass_token:
                        print(
                            f"[!] {MAX_PARSE_RETRIES} parse errors at this cursor; "
                            f"regex-extracted resumptionToken to skip page "
                            f"{state['pages'] + 1} (~100 records lost).",
                            file=sys.stderr,
                        )
                        state["resumption_token"] = bypass_token
                        state["pages"] += 1
                        save_state(state)
                        pages_this_run += 1
                        parse_retry_count = 0
                        time.sleep(args.delay)
                        continue
                    print(
                        f"[!] Aborting: {MAX_PARSE_RETRIES} consecutive parse errors "
                        "and no resumptionToken extractable from malformed response. "
                        f"Harvested so far: {state['harvested']:,} records in {state['pages']} pages.",
                        file=sys.stderr,
                    )
                    return 2
                # Exponential-ish backoff: 5, 10, 15, 20, 25 seconds
                wait = 5 * parse_retry_count
                print(f"    Backing off {wait}s and retrying same resumption_token...", file=sys.stderr)
                time.sleep(wait)
                continue

            # Detect OAI-level errors (e.g., badResumptionToken)
            err = root.find("oai:error", NS)
            if err is not None:
                code = err.attrib.get("code", "?")
                msg = err.text or ""
                print(f"[!] OAI error code={code}: {msg}", file=sys.stderr)
                if code == "badResumptionToken":
                    print("    Token expired; clearing state and restarting from beginning.", file=sys.stderr)
                    state["resumption_token"] = None
                    save_state(state)
                    continue
                return 3

            list_records = root.find("oai:ListRecords", NS)
            if list_records is None:
                print("[!] No ListRecords in response", file=sys.stderr)
                return 4

            page_records = 0
            for rec_el in list_records.findall("oai:record", NS):
                rec = parse_record(rec_el)
                if rec is None:
                    continue
                out_fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
                page_records += 1

            records_this_run += page_records
            state["harvested"] += page_records
            state["pages"] += 1
            pages_this_run += 1

            # Progress log
            elapsed = time.time() - t0
            rate = records_this_run / elapsed if elapsed > 0 else 0
            print(
                f"  page {state['pages']:>5} | +{page_records:>4} rec | "
                f"total {state['harvested']:>7,} | {rate:>5.1f} rec/s",
                flush=True,
            )

            # Resumption token
            token_el = list_records.find("oai:resumptionToken", NS)
            if token_el is None or not (token_el.text or "").strip():
                state["resumption_token"] = None
                state["completed"] = True
                save_state(state)
                print(f"[+] Done. {state['harvested']:,} total records.")
                break

            state["resumption_token"] = token_el.text.strip()
            save_state(state)
            time.sleep(args.delay)

    finally:
        out_fp.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
