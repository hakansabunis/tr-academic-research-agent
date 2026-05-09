# tr-academic-research-agent

> **TürkResearcher** — the first open multi-agent academic research assistant for Turkish, grounded in 633K Turkish thesis abstracts.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Live demo on HF Spaces](https://img.shields.io/badge/demo-HF%20Space-orange)](https://huggingface.co/spaces/hakansabunis/turkresearcher)
[![Index on HF](https://img.shields.io/badge/index-HuggingFace-blue)](https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index)
[![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-green)](https://github.com/langchain-ai/langgraph)

> 🚀 **Try it live:** [hakansabunis/turkresearcher](https://huggingface.co/spaces/hakansabunis/turkresearcher) (bring your own DeepSeek API key)

Inspired by Elicit / Consensus.app — but Turkish-first, since no equivalent exists. Given a Turkish research question, the agent decomposes it, retrieves multi-query evidence from a 633.998-record corpus, runs a critic loop for coverage, then writes a Turkish academic answer with IEEE-style citations grounded in real `tez.yok.gov.tr` PDFs.

## Demo

```bash
python scripts/run.py "Türkçe doğal dil işlemede son yıllardaki ana yaklaşımlar nelerdir?"
```

Produces a 9-section Turkish academic article with 30+ IEEE citations in ~60-90 s.

## Architecture

```
                   Question (TR)
                        │
                        ▼
              ┌─────────────────────┐
              │      PLANNER        │  3-5 sub-questions (DeepSeek)
              └─────────────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │     RETRIEVER       │  multi-query Chroma over 633K theses
              └─────────────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │    SYNTHESISER      │  cluster + flag contradictions
              └─────────────────────┘
                        │
                        ▼
              ┌─────────────────────┐  coverage_ok=False
              │       CRITIC        │ ──────────────► RETRIEVER (loop ≤2)
              └─────────────────────┘                  or
                        │                              LIVE_SEARCH
                        │                              (OpenAlex + Semantic Scholar
                        ▼                               + DergiPark live)
              ┌─────────────────────┐
              │       WRITER        │  IEEE-cited Turkish answer
              └─────────────────────┘
                        │
                        ▼
                     Answer
```

**Stack:** LangChain · LangGraph · ChromaDB · DeepSeek API · `paraphrase-multilingual-mpnet-base-v2` (768-dim, cosine).

## Quick start

### 1. Install

```bash
git clone https://github.com/hakansabunis/tr-academic-research-agent.git
cd tr-academic-research-agent
python -m venv .venv
.venv\Scripts\activate                      # Windows PowerShell
# source .venv/bin/activate                 # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure

```bash
copy .env.example .env                       # Windows
# cp .env.example .env                       # macOS/Linux
```

Edit `.env`:
```
DEEPSEEK_API_KEY=sk-...                      # required
DATA_DIR=C:\dev\turk-researcher-data         # outside OneDrive recommended
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
CHROMA_COLLECTION=turkish_theses
HF_INDEX_REPO=hakansabunis/tr-academic-research-agent-index
```

### 3. Pull the prebuilt 14.8 GB Chroma index

```bash
python scripts/04_pull_index_from_hub.py
```

(Takes ~3–5 minutes on a fast connection. The index is rebuilt from scratch
on Colab GPU; see `colab/build_index_colab.ipynb` for details.)

### 4. Ask a question

```bash
python scripts/run.py "Türkiye'de derin öğrenme ile sel tahmini çalışmaları nelerdir?" --show-trace
```

## Project layout

```
.
├── colab/                      # Colab notebook to rebuild the index from scratch
│   └── build_index_colab.ipynb
├── data/
│   └── eval/questions.json     # 30-question Turkish benchmark
├── docs/
│   ├── report/                 # IEEE LaTeX academic report
│   └── presentation/           # Marp slides
├── src/turk_researcher/
│   ├── config.py               # env-driven settings (DATA_DIR, DeepSeek, embedder)
│   ├── llm.py                  # DeepSeek chat (langchain_openai with base_url)
│   ├── embeddings.py           # mpnet-base-v2 wrapper
│   ├── vectorstore.py          # chromadb-direct, CPU-forced
│   ├── schemas.py              # Pydantic models + GraphState
│   ├── tools/
│   │   ├── retriever.py        # multi-query RAG over Chroma
│   │   └── live_search.py      # OpenAlex + Semantic Scholar + DergiPark
│   ├── agents/
│   │   ├── planner.py          # decompose into sub-questions
│   │   ├── retriever_node.py   # retrieval node
│   │   ├── synthesizer.py      # cluster findings
│   │   ├── critic.py           # coverage check
│   │   ├── live_search_node.py # external API augmentation
│   │   └── writer.py           # IEEE-cited Turkish output
│   └── graph.py                # LangGraph state machine
└── scripts/
    ├── 04_pull_index_from_hub.py    # download prebuilt index
    ├── 05_harvest_dergipark.py      # OAI-PMH harvest of journal articles
    ├── 06_run_eval.py               # run agent on 30-question benchmark
    ├── 07_judge_eval.py             # LLM-as-judge metrics
    ├── 08_eval_summary.py           # aggregate report
    └── run.py                       # CLI agent runner
```

## Data

| Source | Records | License | Pipeline |
|---|---|---|---|
| YÖK Ulusal Tez Merkezi (via [umutertugrul/turkish-academic-theses-dataset](https://huggingface.co/datasets/umutertugrul/turkish-academic-theses-dataset)) | 633,998 (filtered from 650K) | CC-BY-4.0 | `colab/build_index_colab.ipynb` |
| DergiPark journal articles | 100K+ harvested, indexing pending | OAI-PMH/public | `scripts/05_harvest_dergipark.py` |
| OpenAlex (live) | 250M+ works | CC0 | `tools/live_search.py` |
| Semantic Scholar (live) | 220M+ papers | terms of use | `tools/live_search.py` |

The prebuilt 14.8 GB Chroma index is published as
**[`hakansabunis/tr-academic-research-agent-index`](https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index)**
on Hugging Face Hub.

## Evaluation

```bash
python scripts/06_run_eval.py        # ~30-40 min on 30 questions
python scripts/07_judge_eval.py      # ~10 min LLM-as-judge
python scripts/08_eval_summary.py    # aggregate report
```

Metrics (DeepSeek as judge):
- **Citation accuracy** — does each `[n]` citation actually support the claim?
- **Faithfulness** — is the answer grounded in retrieved chunks?
- **Coverage** — fraction of sub-questions addressed?
- **Holistic** — overall academic quality (1-5)
- **Latency** — end-to-end seconds

See `data/eval/summary.md` after running for full results.

## Reproducibility

- **All code** is MIT-licensed and pinned to specific dependency versions in `requirements.txt`.
- **Source data** is fetched directly from Hugging Face Hub (no scraping required).
- **Prebuilt index** is published openly — no need to re-run the 6-hour Colab build.
- **Eval set** is checked in (`data/eval/questions.json`); re-running `scripts/06_run_eval.py` is deterministic up to LLM nondeterminism.

## Course

Final project for *Large Language Models* — Track 1 (Novel Idea), Istanbul Medipol University.

## Citation

If you use this project, please cite the underlying corpus:

```bibtex
@misc{umut2024theses,
  title={Turkish academic theses dataset},
  author={Erturul, Umut},
  year={2024},
  howpublished={\url{https://huggingface.co/datasets/umutertugrul/turkish-academic-theses-dataset}},
  note={CC-BY-4.0}
}
```

## License

MIT (see [LICENSE](LICENSE)). The corpus retains its CC-BY-4.0 license.
