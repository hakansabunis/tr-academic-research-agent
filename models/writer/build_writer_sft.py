"""Stage 2b — Build the Writer-mode instruction dataset.

Task taught: given a topic (+ optional key concepts), write a Turkish
academic abstract paragraph. Trained later via QLoRA SFT on Gemma-3-4b.

Source: cleaned corpus (garbled/English rows already removed by
clean_corpus.py). instruction = task-framed topic, response = the real
abstract. Multiple instruction templates rotate to prevent the model
overfitting to one phrasing.

Output: data/derived/writer_sft_{train,val}.jsonl
  {"instruction": "...", "response": "...", "source": "yok|dergipark"}

Usage:
    python models/writer/build_writer_sft.py
    python models/writer/build_writer_sft.py --limit 200000
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
YOK = ROOT / "data" / "derived" / "abstracts_filtered_clean.parquet"
DP = ROOT / "data" / "derived" / "dergipark_filtered_clean.parquet"
OUT_DIR = ROOT / "data" / "derived"

MIN_ABS = 200
MIN_TITLE = 5
SEED = 42
VAL_RATIO = 0.03
DEFAULT_LIMIT = 200_000  # enough for SFT; full 738K overfits + slow

# Rotating instruction templates. {topic} = thesis title, {kw} = subject
# concepts when available. Keeps the model from binding to one phrasing.
TEMPLATES_WITH_KW = [
    "Aşağıdaki konu ve anahtar kavramlar hakkında Türkçe akademik bir özet yaz:\nKonu: {topic}\nAnahtar kavramlar: {kw}",
    "Bir tez çalışması için şu konuda akademik bir özet (abstract) yaz.\nKonu: {topic}\nAnahtar kavramlar: {kw}",
    "{topic}\n\nYukarıdaki konu ve şu kavramlar ({kw}) çerçevesinde akademik üslupta bir özet paragrafı yaz.",
]
TEMPLATES_NO_KW = [
    "Aşağıdaki başlık için Türkçe akademik bir özet yaz:\n{topic}",
    "{topic} konusunda akademik üslupta bir tez özeti (abstract) yaz.",
    "Bir tez çalışması için şu konuda özet yaz: {topic}",
    "Konu: {topic}\nBu konuda akademik üslupta bir paragraf yaz.",
]


def _clean(s) -> str:
    return str(s or "").strip()


def _kw_from_subject(subject: str) -> str:
    """Subject field often looks like 'Engineering ; Mühendislik ; A,B,C'.
    Pull the comma/semicolon separated concept tokens, dedupe, cap at 5."""
    if not subject:
        return ""
    raw = subject.replace(";", ",").split(",")
    seen, out = set(), []
    for tok in raw:
        t = tok.strip()
        if 2 < len(t) < 40 and t.lower() not in seen and not t.startswith("."):
            seen.add(t.lower())
            out.append(t)
        if len(out) >= 5:
            break
    return ", ".join(out)


def load(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        print(f"[!] Missing {path} — run clean_corpus.py first", file=sys.stderr)
        return pd.DataFrame()
    cols = ["tez_no", "title_tr", "abstract_tr"]
    df = pd.read_parquet(path)
    if "subject" in df.columns:
        cols.append("subject")
    df = df[[c for c in cols if c in df.columns]].copy()
    df["title_tr"] = df["title_tr"].map(_clean)
    df["abstract_tr"] = df["abstract_tr"].map(_clean)
    df["subject"] = df["subject"].map(_clean) if "subject" in df.columns else ""
    df = df[(df["title_tr"].str.len() >= MIN_TITLE)
            & (df["abstract_tr"].str.len() >= MIN_ABS)].reset_index(drop=True)
    df["source"] = label
    print(f"[{label}] usable rows: {len(df):,}")
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    ap.add_argument("--val-ratio", type=float, default=VAL_RATIO)
    args = ap.parse_args()

    yok = load(YOK, "yok")
    dp = load(DP, "dergipark")
    df = pd.concat([yok, dp], ignore_index=True)
    if df.empty:
        return 1
    print(f"[+] Combined: {len(df):,}")

    rng = random.Random(SEED)
    if args.limit and args.limit < len(df):
        idx = rng.sample(range(len(df)), args.limit)
        df = df.iloc[idx].reset_index(drop=True)
        print(f"[+] Sampled to {len(df):,}")

    records = []
    for row in df.itertuples(index=False):
        topic = row.title_tr
        kw = _kw_from_subject(getattr(row, "subject", "") or "")
        if kw:
            tmpl = rng.choice(TEMPLATES_WITH_KW)
            instr = tmpl.format(topic=topic, kw=kw)
        else:
            tmpl = rng.choice(TEMPLATES_NO_KW)
            instr = tmpl.format(topic=topic)
        records.append({
            "instruction": instr,
            "response": row.abstract_tr,
            "source": row.source,
        })

    rng.shuffle(records)
    n_val = max(1, int(len(records) * args.val_ratio))
    val = records[:n_val]
    train = records[n_val:]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tr_path = OUT_DIR / "writer_sft_train.jsonl"
    va_path = OUT_DIR / "writer_sft_val.jsonl"
    with tr_path.open("w", encoding="utf-8") as f:
        for r in train:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with va_path.open("w", encoding="utf-8") as f:
        for r in val:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    avg_resp = sum(len(r["response"]) for r in records) / len(records)
    kw_share = sum(1 for r in records if "Anahtar kavramlar" in r["instruction"]) / len(records)
    print(f"\n[+] Wrote:")
    print(f"    {tr_path}  ({len(train):,} rows)")
    print(f"    {va_path}  ({len(val):,} rows)")
    print(f"    avg response chars: {avg_resp:.0f}")
    print(f"    with-keywords share: {kw_share*100:.0f}%")
    print(f"\nSample instruction:\n  {records[0]['instruction'][:200]}")
    print(f"Sample response:\n  {records[0]['response'][:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
