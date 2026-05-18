"""D2.2 — Create the Qdrant collection and upsert the uint8 export.

Run scripts/31_export_qdrant.py first. Needs a (free) Qdrant Cloud cluster:
put creds in .env (NEVER paste in chat):

    QDRANT_URL=https://xxxx.cloud.qdrant.io:6333
    QDRANT_API_KEY=...
    QDRANT_COLLECTION=turkish_theses_v2     # optional

Collection is created with vector datatype=UINT8 + cosine → only uint8 is
stored (no float32 originals), so 633K×768 fits the ~1 GB free tier.

Usage:
    python scripts/32_upsert_qdrant.py
    python scripts/32_upsert_qdrant.py --batch 1000 --limit 5000   # smoke
    python scripts/32_upsert_qdrant.py --recreate                  # drop+rebuild
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

EXPORT = ROOT / "data" / "derived" / "qdrant_export"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=2000)
    ap.add_argument("--limit", type=int, default=None, help="smoke cap")
    ap.add_argument("--recreate", action="store_true",
                    help="Drop the collection and rebuild from scratch")
    args = ap.parse_args()

    from qdrant_client import QdrantClient
    from qdrant_client.models import (Datatype, Distance, PointStruct,
                                      VectorParams)

    from turk_researcher.tools.qdrant_store import COLLECTION, PAYLOAD_KEYS

    import os
    url = os.getenv("QDRANT_URL")
    if not url:
        print("[!] QDRANT_URL not set — add it to .env (see script header).",
              file=sys.stderr)
        return 2

    vpath = EXPORT / "vectors_uint8.npy"
    ppath = EXPORT / "payload.parquet"
    if not vpath.exists() or not ppath.exists():
        print(f"[!] Export missing in {EXPORT} — run 31_export_qdrant.py first",
              file=sys.stderr)
        return 1

    vecs = np.load(vpath, mmap_mode="r")
    pay = pd.read_parquet(ppath)
    n = len(vecs)
    if args.limit:
        n = min(n, args.limit)
    dim = int(vecs.shape[1])
    print(f"[i] {n:,} points · dim={dim} · collection='{COLLECTION}'")

    client = QdrantClient(url=url, api_key=os.getenv("QDRANT_API_KEY"),
                          timeout=60)

    exists = client.collection_exists(COLLECTION)
    if args.recreate and exists:
        client.delete_collection(COLLECTION)
        exists = False
    if not exists:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=dim, distance=Distance.COSINE,
                datatype=Datatype.UINT8,   # only uint8 stored → free-tier fit
            ),
        )
        print(f"[+] created collection '{COLLECTION}' (uint8, cosine)")

    sent = 0
    for start in range(0, n, args.batch):
        end = min(start + args.batch, n)
        pts = []
        for i in range(start, end):
            row = pay.iloc[i]
            payload = {k: (None if pd.isna(row[k]) else row[k])
                       for k in PAYLOAD_KEYS if k in pay.columns}
            pts.append(PointStruct(
                id=i,
                vector=np.asarray(vecs[i]).astype(int).tolist(),
                payload=payload,
            ))
        client.upsert(collection_name=COLLECTION, points=pts, wait=False)
        sent += len(pts)
        if (start // args.batch) % 10 == 0:
            print(f"    upserted {sent:,}/{n:,}")

    print(f"[+] done — {sent:,} points in '{COLLECTION}'")
    print("    sanity:", client.count(COLLECTION, exact=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
