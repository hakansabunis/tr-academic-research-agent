---
title: TürkResearcher Demo
emoji: 🔍
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
license: mit
short_description: Multi-agent LLM research assistant for Turkish academic literature
---

# TürkResearcher — Hugging Face Spaces Demo

[![GitHub](https://img.shields.io/badge/code-GitHub-181717?logo=github)](https://github.com/hakansabunis/tr-academic-research-agent)
[![HF Index](https://img.shields.io/badge/index-Hugging%20Face-yellow)](https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/hakansabunis/tr-academic-research-agent/blob/main/LICENSE)

This is the public demo of **TürkResearcher**, a multi-agent LLM
research assistant for Turkish academic literature.

## What it does

Given a Turkish academic question, the agent decomposes it into 3–5
sub-questions, retrieves evidence from public scholarly APIs
(OpenAlex + Semantic Scholar), and produces a Turkish academic answer
with IEEE-style citations linking to real DOIs.

## Why this is the demo (not the full system)

The full TürkResearcher pipeline indexes 740K Turkish thesis and
journal-article abstracts in a 15 GB Chroma vector store, which is too
large for the Hugging Face Spaces free tier. This demo therefore runs
in **live-API mode**: retrieval is delegated to OpenAlex and Semantic
Scholar at query time. The architecture, agents, prompts, and
citation subsystem are otherwise identical.

For the **full local-corpus pipeline** (with 740K embedded abstracts):

```bash
git clone https://github.com/hakansabunis/tr-academic-research-agent
cd tr-academic-research-agent
pip install -r requirements.txt
python scripts/04_pull_index_from_hub.py
python scripts/run.py "Türkçe doğal dil işleme metodları nelerdir?"
```

## Configuration

This Space requires a single secret:

| Secret | Description |
|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek API key (https://platform.deepseek.com) |

Optional (for tuning):

| Secret | Default |
|---|---|
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | `deepseek-chat` |

## Pipeline

```
Question (TR)
   ↓
Planner       — DeepSeek decomposes into 3–5 sub-questions
   ↓
LiveSearch    — OpenAlex + Semantic Scholar (deduped, top-24)
   ↓
Writer        — DeepSeek emits Turkish academic answer + [n] markers
   ↓
Citation      — IEEE references built deterministically from chunk metadata
   ↓
Output (TR)
```

## Author

Hakan Sabuniş — Computer Engineering student at Istanbul Medipol University.
Built as the final project for the Large Language Models course (Spring 2026).

- Personal site: https://hakansabunis.com
- GitHub: https://github.com/hakansabunis
