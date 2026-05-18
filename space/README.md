---
title: TürkResearcher
emoji: 🔍
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "5.6.0"
app_file: app.py
pinned: false
license: mit
short_description: Turkish academic RAG over 633K theses (embedder + reranker)
---

# TürkResearcher — Türkçe Akademik Araştırma Ajanı

[![GitHub](https://img.shields.io/badge/code-GitHub-181717?logo=github)](https://github.com/hakansabunis/tr-academic-research-agent)
[![HF Index](https://img.shields.io/badge/index-Hugging%20Face-yellow)](https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index)

**Gerçek sistem** — 633K+ YÖK tezi üzerinde, fine-tuned `trakad-embed-v2`
retriever + cross-encoder reranker + çok-ajanlı RAG. Kaynak-temelli,
IEEE atıflı Türkçe akademik yanıt.

## Mimari

```
Soru (TR) → Planner → Retriever (trakad-embed-v2, in-memory uint8 search)
          → Reranker (bge-reranker-base) → Synthesizer → Critic → Writer
          → IEEE atıflı Türkçe yanıt
```

Harici vektör DB yok: bellek-içi arama. Açılışta `memstore/` artefaktları
(uint8 vektörler + abstract parquet) HF index dataset'inden çekilir.
uint8 ≈ float (top-10 parite %97); reranker geri kalan hassasiyeti toparlar
→ **kalite kaybı yok**, ölçülen sistemle aynı.

## Kullanım

1. Kendi **DeepSeek API key**'inizi girin (Space saklamaz · ~$0.005-0.01/sorgu).
2. Türkçe akademik sorunuzu yazın → **Sor**.

⏱️ **Ücretsiz tier dürüst notu:** Space uyuduktan sonra ilk istek
**birkaç dakika** sürer (~2 GB indeks indirilir + RAM'e yüklenir).
Sonraki sorgular ~2-4 dk (çok-ajanlı LLM aşaması).

## Tam yerel kurulum (daha hızlı, kalıcı)

```bash
git clone https://github.com/hakansabunis/tr-academic-research-agent
cd tr-academic-research-agent
docker compose up --build      # veya: scripts/setup.ps1 / setup.sh
```
Detay: repo'daki `docs/KULLANIM.md`.

## Lisans
MIT (kod) · CC-BY-4.0 (veri). Geliştirici: [Hakan Sabuniş](https://hakansabunis.com).
