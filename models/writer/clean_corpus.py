"""Detect + filter PDF font-encoding garbled abstracts from the corpus.

Problem: a chunk of YOK Tez / DergiPark abstracts were extracted from PDFs
with broken (non-Unicode CMap) fonts, producing a deterministic substitution
cipher where e.g. "Bu çalışmada" -> "%XoDOÕúPDGD". These rows poison both
training and evaluation.

Detection heuristics (a row is GARBLED if any fires):
  1. Avg word length > 15  (cipher often collapses spaces -> runaway words)
  2. Turkish-stopword ratio < 1%  (clean academic TR is dense with
     ve/bir/bu/ile/için/olarak/...)
  3. Non-Turkish-letter ratio > 35%  (cipher injects Õ ú ÷ | \ % etc.)

Usage:
    python models/writer/clean_corpus.py --report-only      # just stats
    python models/writer/clean_corpus.py                     # write clean parquets
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def _resolve_yok() -> Path:
    import os
    if env := os.getenv("DATA_DIR"):
        p = Path(env) / "abstracts_filtered.parquet"
        if p.exists():
            return p
    return ROOT / "data" / "derived" / "abstracts_filtered.parquet"


DEFAULT_YOK = _resolve_yok()
DEFAULT_DERGIPARK = ROOT / "data" / "derived" / "dergipark_filtered.parquet"
OUT_DIR = ROOT / "data" / "derived"

# High-frequency Turkish function/academic words. Clean abstracts are dense
# with these; cipher text has almost none.
TR_MARKERS = {
    "ve", "bir", "bu", "ile", "için", "olarak", "da", "de", "ki", "daha",
    "gibi", "olan", "veya", "ya", "çok", "en", "ancak", "ise", "göre",
    "çalışma", "çalışmada", "çalışmanın", "araştırma", "araştırmanın",
    "amaç", "amacı", "amacıyla", "yöntem", "yöntemi", "sonuç", "sonuçlar",
    "analiz", "elde", "edilen", "edilmiştir", "yapılmıştır", "olduğu",
    "üzerine", "üzerinde", "arasında", "tarafından", "kullanılarak",
}

TR_LETTERS = set("abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ ")

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def classify(text: str) -> tuple[bool, str]:
    """Returns (is_garbled, reason)."""
    t = (text or "").strip()
    if len(t) < 50:
        return True, "too_short"

    words = _WORD_RE.findall(t)
    if not words:
        return True, "no_words"

    avg_wlen = sum(len(w) for w in words) / len(words)
    if avg_wlen > 15:
        return True, f"avg_word_len={avg_wlen:.0f}"

    lower_words = [w.lower() for w in words]
    marker_hits = sum(1 for w in lower_words if w in TR_MARKERS)
    marker_ratio = marker_hits / len(words)
    if marker_ratio < 0.01:
        return True, f"tr_marker_ratio={marker_ratio:.3f}"

    non_tr = sum(1 for c in t if c not in TR_LETTERS and not c.isdigit()
                 and c not in ".,;:()[]{}\"'-/%&+=*\n\t")
    non_tr_ratio = non_tr / len(t)
    if non_tr_ratio > 0.35:
        return True, f"non_tr_ratio={non_tr_ratio:.2f}"

    return False, "clean"


def process(path: Path, label: str, report_only: bool) -> pd.DataFrame | None:
    if not path.exists():
        print(f"[!] Missing {path}", file=sys.stderr)
        return None

    df = pd.read_parquet(path)
    n0 = len(df)
    print(f"\n[{label}] {n0:,} rows")

    abs_col = "abstract_tr"
    flags = df[abs_col].fillna("").astype(str).map(classify)
    df["_garbled"] = flags.map(lambda x: x[0])
    df["_reason"] = flags.map(lambda x: x[1])

    n_garbled = int(df["_garbled"].sum())
    pct = n_garbled / n0 * 100
    print(f"  garbled: {n_garbled:,} ({pct:.1f}%)")
    print(f"  reason breakdown:")
    for reason, cnt in df[df["_garbled"]]["_reason"].apply(
        lambda r: r.split("=")[0]
    ).value_counts().items():
        print(f"    {reason:24s} {cnt:,}")

    if report_only:
        # Show 3 garbled samples (ascii-safe — Windows console is cp1254)
        garbled = df[df["_garbled"]].head(3)
        for _, row in garbled.iterrows():
            sample = str(row[abs_col])[:120].encode("ascii", "replace").decode("ascii")
            print(f"    SAMPLE [{row['_reason']}]: {sample}")
        return None

    clean = df[~df["_garbled"]].drop(columns=["_garbled", "_reason"]).reset_index(drop=True)
    print(f"  -> kept {len(clean):,} clean rows")
    return clean


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yok", type=Path, default=DEFAULT_YOK)
    ap.add_argument("--dergipark", type=Path, default=DEFAULT_DERGIPARK)
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    yok_clean = process(args.yok, "YOK Tez", args.report_only)
    dp_clean = process(args.dergipark, "DergiPark", args.report_only)

    if args.report_only:
        print("\n[report-only] No files written.")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if yok_clean is not None:
        out = OUT_DIR / "abstracts_filtered_clean.parquet"
        yok_clean.to_parquet(out, index=False)
        print(f"\n[+] Wrote {out} ({len(yok_clean):,} rows)")
    if dp_clean is not None:
        out = OUT_DIR / "dergipark_filtered_clean.parquet"
        dp_clean.to_parquet(out, index=False)
        print(f"[+] Wrote {out} ({len(dp_clean):,} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
