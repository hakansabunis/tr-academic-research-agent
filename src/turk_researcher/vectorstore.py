from __future__ import annotations

from functools import lru_cache

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions

from .config import Settings, load_settings


@lru_cache(maxsize=1)
def _collection_for(persist_dir: str, collection_name: str, model_name: str) -> Collection:
    """Open a Chroma collection with our own embedding function (CPU-forced).

    We bypass langchain_chroma to avoid a known issue where the collection's
    persisted embedding-function config (device='cuda', set during Colab
    build) conflicts with the local CPU-only torch install. By attaching our
    own SentenceTransformerEmbeddingFunction at query time, we get the same
    embeddings without touching the persisted config.
    """
    client = chromadb.PersistentClient(path=persist_dir)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=model_name,
        device="cpu",
    )
    return client.get_collection(name=collection_name, embedding_function=embed_fn)


def get_collection(settings: Settings | None = None) -> Collection:
    s = settings or load_settings()
    return _collection_for(
        persist_dir=str(s.chroma_persist_dir),
        collection_name=s.chroma_collection,
        model_name=s.embedding_model,
    )
