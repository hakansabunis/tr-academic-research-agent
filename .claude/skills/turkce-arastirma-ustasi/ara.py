"""turkce-arastirma-ustasi skill wrapper.

Guarantees the *best* retrieval config (trakad-embed-v2 + cross-encoder
reranker, live search off) regardless of the caller's shell, then runs the
TürkResearcher pipeline and emits the run.py --json object.

Env precedence: python-dotenv's load_dotenv (in config.py) does NOT override
already-set process env vars, so the defaults we set here win over .env
unless the user explicitly exported something else.

Usage:
    python .claude/skills/turkce-arastirma-ustasi/ara.py "Türkçe soru..."
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _data_dir() -> Path:
    """Resolve DATA_DIR (where chroma_db_v2 lives) from env or .env, with a
    sensible fallback. Only the DATA_DIR line is read — no secrets touched."""
    if d := os.getenv("DATA_DIR"):
        return Path(d)
    envf = ROOT / ".env"
    if envf.exists():
        for line in envf.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("DATA_DIR="):
                return Path(line.split("=", 1)[1].strip())
    return Path(r"C:\dev\turk-researcher-data")


def _python() -> str:
    venv = ROOT / ".venv" / "Scripts" / "python.exe"
    return str(venv) if venv.exists() else sys.executable


def main() -> int:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print("Kullanım: ara.py \"Türkçe akademik soru\"", file=sys.stderr)
        return 2

    chroma_v2 = _data_dir() / "chroma_db_v2"
    env = dict(os.environ)
    env.setdefault("CHROMA_PERSIST_DIR", str(chroma_v2))
    env.setdefault("EMBEDDING_MODEL", "hakansabunis/trakad-embed-v2")
    env.setdefault("TRRESEARCHER_RERANK", "1")
    env.setdefault("RERANK_MODEL", "BAAI/bge-reranker-base")
    env.setdefault("RERANK_TOP_N", "10")
    env.setdefault("TRRESEARCHER_LIVE", "0")

    if not chroma_v2.exists():
        print(f"[!] chroma_db_v2 bulunamadı: {chroma_v2}\n"
              f"    DATA_DIR'i ayarla veya v2 indeksini indir.", file=sys.stderr)
        return 1

    cmd = [_python(), str(ROOT / "scripts" / "run.py"), "--json", question]
    return subprocess.run(cmd, cwd=str(ROOT), env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
