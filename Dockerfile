# TürkResearcher — local product image (code + deps only).
# The ~13–15 GB v2 Chroma index is NOT baked in: it is pulled at first run
# into the mounted /data volume (see docker_entrypoint.sh). Keeps the image
# lean and lets users keep the index across container rebuilds.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # Product defaults (config.py also defaults to these; explicit here so the
    # container is correct even without a mounted .env).
    DATA_DIR=/data \
    EMBEDDING_MODEL=hakansabunis/trakad-embed-v2 \
    TRRESEARCHER_RERANK=1 \
    RERANK_MODEL=BAAI/bge-reranker-base \
    RERANK_TOP_N=10 \
    TRRESEARCHER_LIVE=0 \
    # Gradio reads these — bind to all interfaces so the port is reachable.
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860 \
    # Cache HF model downloads (embedder + reranker) on the volume too.
    HF_HOME=/data/.hf_cache

WORKDIR /app

# System deps kept minimal; slim + these cover chromadb/torch CPU wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && rm -rf /var/lib/apt/lists/*

# CPU-only torch first (avoids pulling multi-GB CUDA wheels), then the rest.
COPY requirements.txt .
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install -r requirements.txt

COPY . .

RUN chmod +x scripts/docker_entrypoint.sh
EXPOSE 7860
VOLUME ["/data"]

# Entrypoint pulls the v2 index on first run, then launches the web UI.
ENTRYPOINT ["scripts/docker_entrypoint.sh"]
