from __future__ import annotations

from langchain_huggingface import HuggingFaceEmbeddings

from .config import Settings, load_settings


def build_embedder(settings: Settings | None = None) -> HuggingFaceEmbeddings:
    """Multilingual mpnet-base-v2 — 768-dim, the same model the existing 48K
    Chroma index was built with, so we can reuse that index without re-embedding.
    Stronger Turkish quality than MiniLM at the cost of ~2x latency."""
    s = settings or load_settings()
    return HuggingFaceEmbeddings(
        model_name=s.embedding_model,
        encode_kwargs={"normalize_embeddings": True},
    )
