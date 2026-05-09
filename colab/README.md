# Colab Index Build

Bu klasör, ana Chroma indeksinin **Google Colab T4 GPU**'da kurulup Hugging Face Hub'a yüklenmesi için gereken notebook'u içerir.

## Neden Colab?

| | Lokal RTX 3050 Ti (4GB) | Colab T4 (16GB) |
|---|---|---|
| Embedding süresi (~600K abstract) | 8-14 saat | **1-2 saat** |
| Bilgisayar açık kalmalı mı | Evet | Hayır |
| Disk kullanımı | Lokal | Drive + HF Hub |

## Akış

```
Colab GPU                                        Lokal
─────────                                        ─────
1. Bu notebook'u çalıştır                        4. python scripts/04_pull_index_from_hub.py
   ├── HF dataset fetch                              (~5-8 GB inecek)
   ├── Filter (~600K kalır)                      5. python scripts/run.py "soru"
   ├── Chroma build (T4, 1-2 saat)                  (DeepSeek API üzerinden)
   ├── Smoke retrieval test
   └── HF Hub'a upload
        ↓
   hakansabunis/tr-academic-research-agent-index
```

## Kullanım

1. **Notebook'u Colab'a yükle:**
   - https://colab.research.google.com → File → Upload notebook → `build_index_colab.ipynb`
2. **GPU'yu aç:** Runtime → Change runtime type → T4 GPU → Save
3. **Hücreleri sırayla çalıştır.** Her hücre yorumlu, ne yaptığı açık.
4. **Smoke testi için:** Hücre 4'te `LIMIT = 1000` yapıp tüm hücreleri çalıştır (~3 dk). Sonuçları doğrula. Sonra `LIMIT = None` yapıp tekrar.
5. **Drive mount şart:** Colab kesintilerinde index Drive'da kalır, kaldığı yerden devam eder.

## HF token

İlk hücrelerde `HF write token` istenecek. Oluşturmak için:
1. https://huggingface.co/settings/tokens
2. "New token" → Type: **Write**
3. Token'ı kopyala, Colab'a yapıştır

## Beklenen çıktı

HF Hub'da yeni bir dataset repo oluşur:
```
hakansabunis/tr-academic-research-agent-index/
├── chroma_db/                          # ~5-8 GB
│   ├── chroma.sqlite3
│   └── ...
├── abstracts_filtered.parquet          # ~300 MB
└── filter_report.json                  # küçük
```

Lokal pull script (`scripts/04_pull_index_from_hub.py`) bunları indirir ve `data/` altına yerleştirir, böylece agent doğrudan kullanılabilir hale gelir.

## Sorun giderme

- **Colab disconnect:** Drive'a kaydettiğimiz için sorun yok; hücre 7'yi tekrar çalıştır, kaldığı yerden devam eder (`upsert` resumable).
- **OOM:** `BATCH_SIZE`'ı 256'dan 128'e düşür.
- **HF upload zaman aşımı:** Büyük dosyalar otomatik LFS'e gider; yeniden çalıştır, atlanan dosyalar atlanır.
- **`transformers/sentence_transformers` versiyon çatışması:** İlk hücredeki pip install'ı `--upgrade` ile yenile.
