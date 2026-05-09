from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str

    embedding_model: str
    chroma_persist_dir: Path
    chroma_collection: str

    data_dir: Path
    parquet_path: Path
    eval_dir: Path

    hf_index_repo: str

    langsmith_tracing: bool
    langsmith_project: str


def _env(name: str, default: str | None = None, *, required: bool = False) -> str:
    val = os.getenv(name, default)
    if required and not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val or ""


def load_settings() -> Settings:
    data_dir_raw = _env("DATA_DIR", "")
    data_dir = Path(data_dir_raw) if data_dir_raw else ROOT / "data"

    return Settings(
        # Not required at load time so utility scripts (pull, harvest) work
        # without an API key. build_llm() checks lazily.
        deepseek_api_key=_env("DEEPSEEK_API_KEY", ""),
        deepseek_base_url=_env("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        deepseek_model=_env("DEEPSEEK_MODEL", "deepseek-chat"),
        embedding_model=_env(
            "EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        ),
        chroma_persist_dir=data_dir / "chroma_db",
        chroma_collection=_env("CHROMA_COLLECTION", "turkish_theses"),
        data_dir=data_dir,
        parquet_path=data_dir / "abstracts_filtered.parquet",
        eval_dir=data_dir / "eval",
        hf_index_repo=_env("HF_INDEX_REPO", "hakansabunis/tr-academic-research-agent-index"),
        langsmith_tracing=_env("LANGSMITH_TRACING", "false").lower() == "true",
        langsmith_project=_env("LANGSMITH_PROJECT", "turk-researcher"),
    )
