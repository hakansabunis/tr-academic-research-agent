#!/usr/bin/env bash
# First run: pull the v2 Chroma index into the /data volume if absent,
# then launch the local web UI. Idempotent — subsequent runs skip the pull.
set -e

INDEX_DIR="${DATA_DIR:-/data}/chroma_db_v2"

if [ ! -d "$INDEX_DIR" ] || [ -z "$(ls -A "$INDEX_DIR" 2>/dev/null)" ]; then
  echo "[entrypoint] v2 index not found at $INDEX_DIR — pulling from HF Hub"
  echo "[entrypoint] (~13-15 GB, one time; stored in the mounted volume)"
  python scripts/04_pull_index_from_hub.py --variant v2
else
  echo "[entrypoint] v2 index present at $INDEX_DIR — skipping pull"
fi

if [ -z "$DEEPSEEK_API_KEY" ]; then
  echo "[entrypoint] WARNING: DEEPSEEK_API_KEY not set — queries will fail."
  echo "[entrypoint] Pass it: docker run -e DEEPSEEK_API_KEY=sk-... ..."
fi

echo "[entrypoint] launching web UI on :${GRADIO_SERVER_PORT:-7860}"
exec python app.py
