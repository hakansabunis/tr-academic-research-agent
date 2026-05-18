---
description: Türkçe akademik soruyu 633K YÖK tezi üzerinde araştır (trakad-embed-v2 + reranker, IEEE atıflı)
argument-hint: <Türkçe akademik soru>
allowed-tools: Bash(*/python.exe:*), Bash(python:*)
---

Kullanıcı şu Türkçe akademik soruyu araştırmak istiyor:

> $ARGUMENTS

Adımlar:

1. Şu komutu çalıştır (env'i wrapper ayarlar — daima trakad-embed-v2 +
   cross-encoder reranker; sorgu ~2-4 dk sürer, sabırlı ol):

   ```
   python .claude/skills/turkce-arastirma-ustasi/ara.py "$ARGUMENTS"
   ```

2. Çıktı tek bir JSON: `{question, answer_md, citations_ieee[], n_sources,
   max_score, sub_questions[], ok}`.

3. Sonucu kullanıcıya sun (`.claude/skills/turkce-arastirma-ustasi/SKILL.md`
   ilkelerine uy):
   - `ok=false` → "Sistem yanıt üretemedi" de, **uydurma**.
   - `ok=true` → `answer_md`'yi Markdown akademik özet olarak ver, ardından
     **Kaynaklar** başlığıyla `citations_ieee` listesini ekle.
   - `[n]` atıfları `citations_ieee[n-1]` ile eşleşir — eşlemeyi bozma,
     atıf ekleme/çıkarma.
   - Sonuna kısa güven notu: `n_sources` tez kaynağı, en yüksek skor
     `max_score`. `max_score < 0.5` ise "kanıt zayıf" diye uyar.

Argüman boşsa kullanıcıdan Türkçe bir soru iste.
