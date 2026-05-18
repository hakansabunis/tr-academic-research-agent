"""Abstract store — tez_no → full abstract lookup (D5b.2).

The hosted-free design keeps abstracts OUT of the vector DB (Qdrant free
tier can't hold ~1.3 GB of abstract text). Qdrant returns only minimal
payload (tez_no, title, …); this module rehydrates the *full* abstract by
tez_no so the reranker + writer see complete text — i.e. **no quality
compromise**.

Source parquet (tez_no, abstract_tr) is the existing cleaned corpus, also
published on the HF index dataset. Loaded once, lazily, into a dict
(~633K × ~2 KB ≈ ~1.3 GB RAM — fine on a 16 GB free HF Space).

Env:
    ABSTRACT_PARQUET   path to the abstracts parquet
                       (default: data/derived/abstracts_filtered_clean.parquet)
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PARQUET = ROOT / "data" / "derived" / "abstracts_filtered_clean.parquet"


def _parquet_path() -> Path:
    return Path(os.getenv("ABSTRACT_PARQUET", str(DEFAULT_PARQUET)))


@lru_cache(maxsize=1)
def _store() -> dict[str, str]:
    import pandas as pd

    p = _parquet_path()
    if not p.exists():
        raise RuntimeError(
            f"Abstract parquet not found: {p}. Set ABSTRACT_PARQUET or pull "
            f"it from the HF index dataset.")
    df = pd.read_parquet(p, columns=["tez_no", "abstract_tr"])
    df["tez_no"] = df["tez_no"].astype(str)
    # dict comprehension keeps last on dup tez_no (corpus is deduped anyway)
    return dict(zip(df["tez_no"], df["abstract_tr"].fillna("").astype(str)))


def get_abstract(tez_no: str) -> str:
    """Full abstract for a tez_no, or '' if unknown."""
    return _store().get(str(tez_no), "")


def get_many(tez_nos) -> dict[str, str]:
    s = _store()
    return {str(t): s.get(str(t), "") for t in tez_nos}


def warm() -> int:
    """Force-load the store (call at app startup). Returns row count."""
    return len(_store())
