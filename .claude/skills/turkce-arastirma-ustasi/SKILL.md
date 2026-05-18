---
name: turkce-arastirma-ustasi
description: >-
  Türkçe akademik araştırma ustası. 633K+ YÖK tezi üzerinde kaynak-temelli,
  IEEE-atıflı Türkçe yanıt üretir (fine-tuned trakad-embed-v2 retriever +
  cross-encoder reranker + çok-ajanlı RAG). Türkçe bir akademik/literatür
  sorusu sorulduğunda; "tezlerde ne deniyor", "Türkçe kaynak bul/tara",
  "akademik özet/derleme" istendiğinde kullan.
---

# Türkçe Araştırma Ustası

Bu skill, TürkResearcher RAG sistemini (planner→retriever→synthesizer→
critic→writer) çağırır. Retrieval **trakad-embed-v2** (ölçülmüş +%9.9
citation) + **cross-encoder reranker** (ölçülmüş +0.09 citation accuracy)
ile yapılır. Sen kaynak uydurmazsın — sistem getirdiği tezlere dayanır.

## Ne zaman kullanılır
- Türkçe akademik/literatür sorusu ("... konusunda tezlerde hangi
  yöntemler kullanılmış?", "X ile Y'nin karşılaştırması").
- Türkçe kaynak/tez tarama, akademik derleme/özet isteği.
- Bir iddianın Türkçe tez literatüründe doğrulanması.

Genel bilgi sorularında veya kaynak gerektirmeyen sohbette **kullanma**.

## Nasıl çalıştırılır

Tek komut (env'i wrapper ayarlar — daima v2 + reranker):

```
python .claude/skills/turkce-arastirma-ustasi/ara.py "KULLANICININ TÜRKÇE SORUSU"
```

Çıktı tek bir JSON nesnesidir:
`{question, answer_md, citations_ieee[], n_sources, max_score,
sub_questions[], ok}`.

İlk çağrı reranker modelini indirebilir (~1 dk) ve sorgu ~60-120 sn sürer;
bu normaldir, bekle.

## Sonucu kullanıcıya sunma

1. `ok=false` ise: "Sistem yanıt üretemedi" de, uydurma.
2. `ok=true` ise `answer_md`'yi olduğu gibi (Markdown akademik özet) ver.
3. Ardından **Kaynaklar** başlığıyla `citations_ieee` listesini ekle.
4. `n_sources` ve `max_score`'u kısa bir güven notu olarak belirt
   (ör. "23 tez kaynağından, en yüksek benzerlik 0.89").
5. `answer_md` içindeki `[n]` atıfları `citations_ieee[n-1]` ile eşleşir —
   bu eşlemeyi bozma, atıf ekleme/çıkarma yapma.

## İlkeler (sıkı)
- **Kaynak-temellilik:** Yalnızca sistemin döndürdüğüne dayan. JSON dışı
  bilgi ekleme; eklersen "sistem dışı" diye açıkça işaretle.
- **Atıf bütünlüğü:** IEEE listesini ve `[n]` numaralarını aynen koru.
- **Dürüstlük:** Düşük `max_score` (< ~0.5) veya az `n_sources` ise
  kullanıcıyı "kanıt zayıf" diye uyar.
- **Kapsam:** Sistem kapalı-corpus'tur (YÖK tezleri + DergiPark); corpus
  dışı güncel çalışmaları kaçırabilir — gerektiğinde bunu söyle.

## Sınırlar
- Tam metin değil, tez özet düzeyinde çalışır.
- DeepSeek API anahtarı `.env`'de gerekli; yoksa wrapper anlaşılır hata verir.
