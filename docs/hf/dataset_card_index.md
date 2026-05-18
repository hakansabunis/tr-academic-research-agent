---
language: tr
license: cc-by-4.0
pretty_name: TürkResearcher Tez İndeksi (633K)
size_categories:
  - 100K<n<1M
task_categories:
  - sentence-similarity
  - question-answering
tags:
  - turkish
  - turkce
  - academic
  - thesis
  - rag
  - chromadb
---

# TürkResearcher — Türkçe Tez İndeksi

[**TürkResearcher**](https://github.com/hakansabunis/tr-academic-research-agent)
için önceden kurulmuş erişim artefaktları: **633.998 Türkçe yüksek lisans/
doktora tezi** özeti (YÖK Ulusal Tez Merkezi).

## İçerik

| Yol | Ne |
|---|---|
| `chroma_db_v2/` | ChromaDB indeksi — `trakad-embed-v2` ile kuruldu (**ürün**, ~13-15 GB) |
| `memstore/vectors_uint8.npy` | uint8 nicelenmiş vektörler (633K×768, ~464 MB) — harici DB'siz bellek-içi arama için |
| `memstore/payload.parquet` | minimal atıf meta verisi (tez_no, başlık, yazar, yıl…) |
| `memstore/abstracts_filtered_clean.parquet` | tez_no → tam Türkçe özet (~1.5 GB) |

uint8 ≈ float (top-10 örtüşme %97); tam abstract ayrı tutulur → kalite
kaybı olmadan ücretsiz host edilebilir.

## Kullanım

```bash
# Tüm sistemle (önerilen):
git clone https://github.com/hakansabunis/tr-academic-research-agent
python scripts/04_pull_index_from_hub.py --variant v2
python app.py
```
Bellek-içi (DB'siz) varyant ve canlı demo otomatik bu artefaktları kullanır.

## Bağlantılar

- Kod / sistem: https://github.com/hakansabunis/tr-academic-research-agent
- Embedder: [`trakad-embed-v2`](https://huggingface.co/hakansabunis/trakad-embed-v2)
- Canlı demo: [HF Space](https://huggingface.co/spaces/hakansabunis/turkresearcher)

## Lisans

Tez özetleri YÖK Ulusal Tez Merkezi kaynaklıdır — **CC-BY-4.0**.
Geliştirici: Hakan Sabuniş.
