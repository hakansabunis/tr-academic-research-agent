from __future__ import annotations

from functools import lru_cache

import chromadb
from chromadb.api.models.Collection import Collection

from .config import Settings, load_settings


@lru_cache(maxsize=1)
def _collection_for(persist_dir: str, collection_name: str) -> Collection:
    """Open a Chroma collection without attaching an embedding function.

    Why no embedding_function: chroma_db_v2 was indexed with `embeddings=`
    passed explicitly (no ef registered → persisted name='default'), and
    Chroma 0.5+ raises on get_collection if the supplied ef name doesn't
    match the persisted one. We sidestep the conflict by encoding queries
    ourselves via get_encoder() and passing query_embeddings= at query time.
    Works uniformly for v1 (mpnet-built) and v2 (trakad-embed-v2-built).
    """
    client = chromadb.PersistentClient(path=persist_dir)
    return client.get_collection(name=collection_name)


@lru_cache(maxsize=2)
def _encoder_for(model_name: str):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name, device="cpu")


def get_collection(settings: Settings | None = None) -> Collection:
    s = settings or load_settings()
    return _collection_for(
        persist_dir=str(s.chroma_persist_dir),
        collection_name=s.chroma_collection,
    )


def get_encoder(settings: Settings | None = None):
    s = settings or load_settings()
    return _encoder_for(s.embedding_model)
