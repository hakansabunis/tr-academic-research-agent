#!/usr/bin/env bash
# TürkResearcher — one-command local setup (Linux / macOS).
#   bash scripts/setup.sh
# Creates venv, installs deps, prepares .env, pulls the v2 index.
# Idempotent: re-running skips steps already done.
set -e
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  echo "[setup] creating .venv"
  python3 -m venv .venv
fi
PY=".venv/bin/python"

echo "[setup] installing dependencies"
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "[setup] .env created from .env.example — EDIT IT: add DEEPSEEK_API_KEY"
else
  echo "[setup] .env already exists — leaving it"
fi

echo "[setup] pulling v2 Chroma index (~13-15 GB, one time)"
"$PY" scripts/04_pull_index_from_hub.py --variant v2

echo
echo "[setup] DONE. Next:"
echo "  1) put DEEPSEEK_API_KEY=sk-... in .env (if not already)"
echo "  2) $PY app.py   ->  http://127.0.0.1:7860"
