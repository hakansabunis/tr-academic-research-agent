# TürkResearcher — Kullanım Rehberi

633K+ YÖK tezi üzerinde, kaynak-temelli, IEEE atıflı Türkçe akademik
araştırma asistanı. Bu doküman **kim, nasıl kullanır** sorusunun tek
durağıdır.

## Artefaktlar (hepsi açık)

| Ne | Nerede |
|---|---|
| Kod (MIT) | https://github.com/hakansabunis/tr-academic-research-agent |
| Canlı lite demo | https://huggingface.co/spaces/hakansabunis/turkresearcher |
| Fine-tuned embedder | https://huggingface.co/hakansabunis/trakad-embed-v2 |
| Chroma indeksi (v1+v2) | https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index |

## Hangi kullanıcı, hangi yol?

### 1) Sadece denemek istiyorum (kurulum yok)
→ **HF Space**: https://huggingface.co/spaces/hakansabunis/turkresearcher
Kendi DeepSeek API key'inle çalışır. ⚠️ Bu **lite demo**: canlı
OpenAlex/Semantic Scholar kullanır — 633K tez korpusu, trakad-embed-v2 ve
reranker **yoktur**. Ölçülen/gerçek sistem değildir.

### 2) Gerçek sistemi çalıştırmak istiyorum — Docker (en kolay)
```bash
git clone https://github.com/hakansabunis/tr-academic-research-agent
cd tr-academic-research-agent
cp .env.example .env          # icine DEEPSEEK_API_KEY=sk-... ekle
docker compose up --build     # ilk calistirma ~13-15 GB v2 indeksi ceker (bir kez)
# → http://localhost:7860
```
İndeks + model cache `tr_data` volume'unda kalıcı (rebuild'de yeniden inmez).

### 3) Gerçek sistem — Docker'sız tek komut
```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1   # Windows
```
```bash
bash scripts/setup.sh                                          # Linux/macOS
```
Sonra `.env`'e key'i ekle → `python app.py` → http://127.0.0.1:7860

### 4) Claude Code kullanıcısıyım
Repo lokalde kuruluyken Claude Code'da:
- Slash: `/tr-arastir Türkçe doğal dil işlemede ana yaklaşımlar nelerdir?`
- Ya da doğal dille "şu konuyu Türkçe tezlerde araştır" — skill otomatik tetiklenir.

## Ön koşullar

- **DeepSeek API key** (zorunlu) — https://platform.deepseek.com · ~$0.005-0.01/sorgu.
- Gerçek sistem için: ~25-30 GB disk (13-15 GB indeks dahil), makul RAM.
- İlk sorgu reranker+embedder modellerini indirir (~1 dk, sonra cache'li).
- Sorgu süresi: ~2-4 dk (planner→retriever+reranker→synth→critic→writer).

## Ne alırsın

Markdown akademik özet + **Kaynaklar** (IEEE, gerçek `tez.yok.gov.tr`
linkleri) + güven notu (kaç tez kaynağı, en yüksek benzerlik skoru).

## Sınırlar (dürüst)

- **Kapalı corpus**: YÖK tezleri (+DergiPark). Corpus dışı / çok güncel
  çalışmaları kaçırabilir.
- Tam metin değil, **tez özeti** düzeyinde çalışır.
- Lite demo (HF Space) ≠ ölçülen sistem (korpus/embedder/reranker yok).
- Yanıt kalitesi getirilen kaynaklara bağlıdır; düşük skorda "kanıt zayıf"
  uyarısı verir — sistem kaynak uydurmaz.

## Sık sorun

- **Web UI'de yanıt gelmiyor / takılıyor**: sorgu 2-4 dk sürer; `app.py`
  `queue()` ile çalışır, sabırlı ol. Hard refresh (Ctrl+F5) dene.
- **401 / invalid api key**: `.env` içindeki `DEEPSEEK_API_KEY` geçersiz/eski.
- **chroma_db_v2 bulunamadı**: indeks çekilmemiş →
  `python scripts/04_pull_index_from_hub.py --variant v2`.

## Yapılandırma

Ürün varsayılanı = ölçülen en iyi sistem (trakad-embed-v2 + chroma_db_v2 +
reranker ON + live OFF). `.env.example` bunları hazır getirir. v1/baseline'a
dönmek için `.env.example` içindeki yorumlu bloğa bak.

## Kendi modelinle / sağlayıcı-bağımsız (DeepSeek zorunlu değil)

Sistem **herhangi bir OpenAI-uyumlu sağlayıcı** ile çalışır. Varsayılan
DeepSeek; değiştirmek için `.env`'e `LLM_*` ekle (DEEPSEEK_*'ı override eder):

| Sağlayıcı | `.env` |
|---|---|
| OpenRouter | `LLM_BASE_URL=https://openrouter.ai/api/v1` · `LLM_API_KEY=sk-or-...` · `LLM_MODEL=meta-llama/llama-3.1-70b-instruct` |
| OpenAI | `LLM_BASE_URL=https://api.openai.com/v1` · `LLM_API_KEY=sk-...` · `LLM_MODEL=gpt-4o-mini` |
| **Lokal (ücretsiz, offline, key yok)** | `ollama pull qwen2.5:7b` → `LLM_BASE_URL=http://localhost:11434/v1` · `LLM_MODEL=qwen2.5:7b` |

Lokal seçenekle **hiçbir API anahtarı/ücret yok** — embedder + reranker
zaten lokaldi, artık LLM de. ⚠️ Pipeline structured-output için
tool/function-calling kullanır → tool-calling destekleyen model seç
(cloud modellerin çoğu; Ollama'da `qwen2.5` / `llama3.1`). Zayıf model
JSON üretemeyip kaliteyi düşürebilir; sistem yine de sağlayıcıdan bağımsızdır.

(Public HF Space tasarım gereği DeepSeek-BYO kalır; bağımsızlık
self-host / Docker / lokal kullanıcılar içindir.)

---

### Ek: HF kartlarına eklenecek çapraz-link (manuel, bir kez)

Aşağıdaki bloğu `trakad-embed-v2` model kartına ve indeks dataset kartına
ekle (HF Hub'a erişim sende; bu repodan push edilemez):

```markdown
**Part of [TürkResearcher](https://github.com/hakansabunis/tr-academic-research-agent)**
— Turkish academic RAG over 633K theses.
Embedder: [trakad-embed-v2](https://huggingface.co/hakansabunis/trakad-embed-v2) ·
Index: [tr-academic-research-agent-index](https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index) ·
Demo: [Space](https://huggingface.co/spaces/hakansabunis/turkresearcher)
```
