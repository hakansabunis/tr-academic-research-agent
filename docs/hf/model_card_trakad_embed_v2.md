---
language: tr
license: apache-2.0
library_name: sentence-transformers
pipeline_tag: sentence-similarity
base_model: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
tags:
  - sentence-transformers
  - turkish
  - turkce
  - academic
  - retrieval
  - feature-extraction
---

# trakad-embed-v2 — Türkçe Akademik Embedder

`paraphrase-multilingual-mpnet-base-v2`'nin **633K Türkçe tez** başlık↔özet
çifti üzerinde, konu-duyarlı hard-negative madenciliği + contrastive loss
ile fine-tune edilmiş hali. 768 boyut, kosinüs.

[**TürkResearcher**](https://github.com/hakansabunis/tr-academic-research-agent)
projesinin retriever'ı — Türkçe akademik literatür erişimi için.

## Ölçülen kazanım

Genel mpnet baseline'a göre TürkResearcher RAG hattında:

- **citation accuracy +%9.9** (0.507 → 0.557)
- **faithfulness +%7.8**
- Bilgisayar (CS) kategorisi **+%42.6** (orijinal başarısızlık modu kapandı)

## Kullanım

```python
from sentence_transformers import SentenceTransformer

m = SentenceTransformer("hakansabunis/trakad-embed-v2")
emb = m.encode(["Türkçe doğal dil işleme yöntemleri"],
               normalize_embeddings=True)
```

## Bağlantılar

- Kod / sistem: https://github.com/hakansabunis/tr-academic-research-agent
- Hazır Chroma indeksi: [`tr-academic-research-agent-index`](https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index)
- Canlı demo: [HF Space](https://huggingface.co/spaces/hakansabunis/turkresearcher)

## Lisans & atıf

Apache-2.0 (taban model lisansı). Eğitim verisi: YÖK tez özetleri (CC-BY-4.0).
Geliştirici: Hakan Sabuniş.
