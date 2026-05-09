"""Health-check the prebuilt 48K Chroma index before we commit to reusing it.

Usage:
    python scripts/00_validate_index.py [--path PATH]

By default, points at the sibling tr-academic-nlp Chroma directory so we can
validate WITHOUT copying first. After validation passes, run 01_copy_data.py.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

DEFAULT_PATH = r"C:\Users\SABUNIS\OneDrive\Desktop\tr-academic-nlp\data\chroma_db"
COLLECTION = "turkish_theses"
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EXPECTED_RECORDS = 48_376
EXPECTED_DIM = 768

REQUIRED_META_KEYS = {"tez_no", "title_tr", "author", "year", "abstract_tr"}

SMOKE_QUERIES = [
    "derin öğrenme ile sel tahmini",
    "Türkçe doğal dil işleme metodları",
    "kalp damar hastalıkları teşhis yöntemleri",
    "yenilenebilir enerji rüzgar türbin",
    "üniversite öğrencilerinin akademik başarısı",
]

OK = "[ OK ]"
WARN = "[WARN]"
FAIL = "[FAIL]"


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.fails = 0
        self.warns = 0

    def ok(self, msg: str) -> None:
        self.lines.append(f"{OK} {msg}")

    def warn(self, msg: str) -> None:
        self.lines.append(f"{WARN} {msg}")
        self.warns += 1

    def fail(self, msg: str) -> None:
        self.lines.append(f"{FAIL} {msg}")
        self.fails += 1

    def section(self, title: str) -> None:
        self.lines.append("")
        self.lines.append(f"=== {title} ===")

    def dump(self) -> None:
        print("\n".join(self.lines))
        print()
        print(f"Summary: {self.fails} fail, {self.warns} warn")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=DEFAULT_PATH, help="Chroma persist directory")
    parser.add_argument("--collection", default=COLLECTION)
    parser.add_argument("--no-smoke", action="store_true", help="Skip retrieval smoke test")
    args = parser.parse_args()

    path = Path(args.path)
    rep = Report()
    rep.section(f"Validating Chroma at {path}")

    if not path.exists():
        rep.fail(f"Path does not exist: {path}")
        rep.dump()
        return 1
    if not (path / "chroma.sqlite3").exists():
        rep.fail("chroma.sqlite3 not found — not a Chroma persist dir")
        rep.dump()
        return 1
    rep.ok(f"Persist dir exists ({sum(f.stat().st_size for f in path.rglob('*') if f.is_file()) / 1024 / 1024:.1f} MB total)")

    rep.section("Opening collection")
    client = chromadb.PersistentClient(path=str(path))
    try:
        collections = [c.name for c in client.list_collections()]
        rep.ok(f"Collections present: {collections}")
        if args.collection not in collections:
            rep.fail(f"Expected collection '{args.collection}' not found")
            rep.dump()
            return 1
    except Exception as e:
        rep.fail(f"Failed to list collections: {e}")
        rep.dump()
        return 1

    coll = client.get_collection(args.collection)
    count = coll.count()
    rep.ok(f"Record count: {count:,}")
    if abs(count - EXPECTED_RECORDS) > 50:
        rep.warn(f"Record count drifts from expected {EXPECTED_RECORDS:,} (diff {count - EXPECTED_RECORDS:+,})")

    rep.section("Sampling records")
    sample = coll.get(limit=200, include=["documents", "metadatas", "embeddings"])
    docs = sample["documents"] or []
    metas = sample["metadatas"] or []
    embs = sample["embeddings"]
    if embs is not None and len(embs) > 0:
        dim = len(embs[0])
        rep.ok(f"Embedding dimension: {dim}")
        if dim != EXPECTED_DIM:
            rep.fail(f"Embedding dim {dim} != expected {EXPECTED_DIM} (mpnet-base-v2)")
    else:
        rep.warn("Could not retrieve embeddings sample")

    if metas:
        keys_seen: Counter[str] = Counter()
        missing_per_record = 0
        for m in metas:
            keys_seen.update(m.keys())
            if not REQUIRED_META_KEYS.issubset(m.keys()):
                missing_per_record += 1
        rep.ok(f"Metadata keys (top): {keys_seen.most_common(15)}")
        if missing_per_record:
            rep.warn(f"{missing_per_record}/{len(metas)} sample records missing required keys "
                     f"({REQUIRED_META_KEYS})")
        else:
            rep.ok(f"All {len(metas)} sample records have required keys: {REQUIRED_META_KEYS}")

    if docs:
        lengths = [len(d) for d in docs if isinstance(d, str)]
        if lengths:
            rep.ok(
                f"Document char length — min {min(lengths)} / "
                f"median {int(statistics.median(lengths))} / "
                f"p95 {sorted(lengths)[int(len(lengths) * 0.95)]} / "
                f"max {max(lengths)}"
            )
            short = sum(1 for l in lengths if l < 200)
            if short > len(lengths) * 0.05:
                rep.warn(f"{short}/{len(lengths)} docs shorter than 200 chars (>5% threshold)")

    rep.section("Year distribution (sample)")
    if metas:
        years = Counter()
        for m in metas:
            y = m.get("year")
            if y:
                years[int(y) if not isinstance(y, str) or y.isdigit() else 0] += 1
        top_years = sorted(years.items(), reverse=True)[:8]
        rep.ok(f"Sample year coverage: {top_years}")

    rep.section("Subject diversity (sample)")
    if metas:
        subjects = Counter(m.get("subject") or "(none)" for m in metas)
        rep.ok(f"Distinct subjects in sample: {len(subjects)}")
        for s, n in subjects.most_common(5):
            rep.ok(f"  {s[:80]}: {n}")

    rep.section("Duplicate tez_no check (sample)")
    if metas:
        tez_nos = [m.get("tez_no") for m in metas if m.get("tez_no")]
        dups = [k for k, v in Counter(tez_nos).items() if v > 1]
        if dups:
            rep.warn(f"Duplicates in sample: {dups[:5]} (total {len(dups)})")
        else:
            rep.ok("No duplicate tez_no in sample")

    if args.no_smoke:
        rep.section("Smoke retrieval test")
        rep.ok("Skipped (--no-smoke)")
    else:
        rep.section("Smoke retrieval test")
        try:
            embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
            coll_q = client.get_collection(args.collection, embedding_function=embed_fn)
        except Exception as e:
            rep.fail(f"Failed to attach embed_fn for queries: {e}")
            rep.dump()
            return 1

        for q in SMOKE_QUERIES:
            t0 = time.time()
            try:
                res = coll_q.query(query_texts=[q], n_results=3, include=["documents", "metadatas", "distances"])
                dt = time.time() - t0
                top_meta = (res["metadatas"][0] or [{}])[0]
                top_doc = (res["documents"][0] or [""])[0]
                top_dist = (res["distances"][0] or [None])[0]
                rep.ok(
                    f"q={q!r} -> {dt:.2f}s | "
                    f"top: {top_meta.get('author','?')} ({top_meta.get('year','?')}) "
                    f"\"{(top_meta.get('title_tr') or top_doc[:80])[:80]}\" | dist={top_dist:.4f}"
                )
            except Exception as e:
                rep.fail(f"Query failed for {q!r}: {e}")

    rep.section("Verdict")
    if rep.fails:
        rep.fail("Index NOT healthy — fix before reuse")
    elif rep.warns > 3:
        rep.warn("Index has warnings — review before reuse")
    else:
        rep.ok("Index looks healthy. Safe to copy via scripts/01_copy_data.py")

    rep.dump()

    out_dir = Path(__file__).resolve().parents[1] / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "path": str(path),
        "count": count,
        "fails": rep.fails,
        "warns": rep.warns,
        "lines": rep.lines,
    }
    (out_dir / "index_validation_report.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nReport saved -> {out_dir / 'index_validation_report.json'}")

    return 0 if rep.fails == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
