# TürkResearcher 🔍

> **633.998 Türkçe yüksek lisans/doktora tezi** üzerinde çalışan, açık
> kaynak, çok-ajanlı Türkçe akademik araştırma asistanı. Sorduğunuz Türkçe
> soruyu kaynaklara dayandırarak, **IEEE atıflı** akademik bir yanıta
> dönüştürür.

[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-yellow.svg)](LICENSE)
[![Canlı demo](https://img.shields.io/badge/demo-HF%20Space-orange)](https://huggingface.co/spaces/hakansabunis/turkresearcher)
[![Embedder](https://img.shields.io/badge/model-trakad--embed--v2-blue)](https://huggingface.co/hakansabunis/trakad-embed-v2)
[![İndeks](https://img.shields.io/badge/veri-HF%20dataset-blue)](https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index)

Elicit / Consensus benzeri araçların Türkçe karşılığı yoktu — TürkResearcher
bu boşluğu **Türkçe tez korpusuna** dayanarak doldurur. Soru parçalanır,
çok-sorgulu erişim yapılır, kanıt sentezlenir, eksik kapsam denetlenir ve
gerçek `tez.yok.gov.tr` kayıtlarına atıflı Türkçe bir akademik metin yazılır.

---

## 🚀 Hızlı başlangıç

**Sadece denemek (kurulum yok):**
👉 [Canlı demo (HF Space)](https://huggingface.co/spaces/hakansabunis/turkresearcher) — kendi DeepSeek API anahtarınızla.

**Gerçek sistemi çalıştır (Docker — en kolay):**
```bash
git clone https://github.com/hakansabunis/tr-academic-research-agent
cd tr-academic-research-agent
cp .env.example .env          # .env içine DEEPSEEK_API_KEY=sk-... ekle
docker compose up --build     # ilk çalıştırma ~13-15 GB v2 indeksi bir kez indirir
# → http://localhost:7860
```

**Docker'sız tek komut:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1   # Windows
```
```bash
bash scripts/setup.sh                                          # Linux/macOS
```

Detaylı kullanım rehberi → **[`docs/KULLANIM.md`](docs/KULLANIM.md)**

## 🧠 Mimari

```
Soru (TR)
  → PLANNER       soruyu 3-5 alt soruya böler
  → RETRIEVER     trakad-embed-v2 ile ChromaDB (633K tez) çok-sorgulu erişim
  → RERANKER      cross-encoder ile yeniden sıralama (gürültü filtreler)
  → SYNTHESIZER   bulguları kümeler, çelişkileri işaretler
  → CRITIC        kapsam yeterli mi? değilse retriever'a döner (≤2 döngü)
  → WRITER        IEEE atıflı Türkçe akademik yanıt
```

**Yığın:** LangChain · LangGraph · ChromaDB · `trakad-embed-v2`
(fine-tuned Türkçe akademik embedder) · cross-encoder reranker
(`bge-reranker-base`) · Gradio · sağlayıcı-bağımsız LLM.

## 🔧 Kendi modelinle (sağlayıcı-bağımsız)

DeepSeek'e bağımlı **değildir**. `.env`'de `LLM_*` ile herhangi bir
OpenAI-uyumlu sağlayıcı (DEEPSEEK_* fallback; mevcut kurulum bozulmaz):

```bash
# Tamamen lokal, ücretsiz, offline — API anahtarı yok (Ollama/vLLM/LM Studio):
ollama pull qwen2.5:7b
#   .env:
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
# Veya cloud: OpenRouter / OpenAI / Groq … LLM_BASE_URL/LLM_API_KEY/LLM_MODEL
```
Embedder + reranker zaten lokaldi; LLM de lokal olunca **sıfır maliyet,
offline**. (Not: structured-output için tool-calling destekleyen model
gerekir — `qwen2.5`/`llama3.1` vb.)

## 📊 Bulgular (dürüst — pozitif + negatif)

Proje aşamalı ve kanıta dayalı geliştirildi; ne çalışmadığı da raporlanır:

| Bulgu | Sonuç |
|---|---|
| `trakad-embed-v2` özel embedder | citation accuracy **+%9.9**, CS kategorisi **+%42.6** ✅ |
| Corpus Expansion Paradox | korpus 633K→740K büyüyünce gürültü ↑ → atıf doğruluğu **düştü** |
| Base-model benchmark (adil BPC) | **Gemma-3-4b** > Türkçe-özel 7B/8B modeller |
| Naif continued pre-train (Trendyol-7b) | register mode-collapse → **başarısız** ❌ (dürüst negatif) |
| Writer distilasyon (Gemma'ya) | retrieval-bound; öğretmen zayıf → fine-tune **veriyle atlandı** ❌ |
| **Cross-encoder reranker** | citation **0.557→0.647 (+%16)**, faithfulness +0.04, $0 ✅ |

Anlatı: embedder erişimi iyileştirdi (1) ama korpus büyüyünce gürültü
arttı (2); writer'ı iyileştirmek işe yaramadı çünkü darboğaz writer
değildi (5); **reranker tam o gürültüyü filtreleyerek paradoksu kapattı (6)**.

## 📦 Bağlantılar

| | |
|---|---|
| Canlı demo | https://huggingface.co/spaces/hakansabunis/turkresearcher |
| Fine-tuned embedder | https://huggingface.co/hakansabunis/trakad-embed-v2 |
| Chroma indeksi + memstore | https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index |
| Kullanım rehberi | [`docs/KULLANIM.md`](docs/KULLANIM.md) |

## 🗂️ Depo yapısı

```
.
├── app.py                      # Lokal web arayüzü (gerçek sistem)
├── .claude/                    # Claude Code skill + /tr-arastir slash komutu
├── src/turk_researcher/        # Çekirdek paket (graph, agents, tools)
├── scripts/                    # Veri/indeks/değerlendirme/deploy betikleri
├── docs/                       # KULLANIM.md, bulgu raporları
├── space/                      # HF Space uygulaması
├── Dockerfile · docker-compose.yml
└── requirements.txt
```

## 🤝 Katkı & lisans

- **Kod:** MIT — bkz. [LICENSE](LICENSE).
- **Veri:** YÖK Ulusal Tez Merkezi tez özetleri, CC-BY-4.0.
- Hata/öneri için issue açabilirsiniz.

## 📄 Atıf

```bibtex
@misc{turkresearcher2026,
  title  = {TürkResearcher: 633K Türkçe tez üzerinde çok-ajanlı akademik RAG},
  author = {Sabuniş, Hakan},
  year   = {2026},
  howpublished = {\url{https://github.com/hakansabunis/tr-academic-research-agent}}
}
```

Geliştirici: **Hakan Sabuniş** · [hakansabunis.com](https://hakansabunis.com)
