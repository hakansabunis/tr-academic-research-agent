# STEM Regression Analysis — v1 vs v2 Side-by-Side

*17 STEM questions analyzed. For each, top-5 retrieved thesis titles compared between v1 (mpnet) and v2 (trakad-embed-v2), plus judge scores.*

## q01 — `computer_science`

**Question:** Türkçe doğal dil işlemede son yıllardaki ana yaklaşımlar nelerdir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.15 | 0.60 | +0.45 |
| faithfulness | 0.10 | 0.50 | +0.40 |
| coverage | 0.20 | 0.40 | +0.20 |
| holistic | 1 | 2 | +1 |

**Retrieval overlap (top-5):** 0/5 same chunks. 5 only in v1, 5 only in v2.

**v1 top-5 retrieved:**
-   `770005` [0.941] Çağdaş Türk lehçelerinde ünsüzler
-   `754010` [0.932] Erken Cumhuriyet Dönemi basınında Harf İnkılabı: Sosyolojik bir analiz
-   `art-22326` [0.932] BİTLİS MERKEZ AĞZINDAN DERLEME SÖZLÜĞÜNE KATKILAR
-   `art-90237` [0.931] TÜRKÇE DİL YAPILARININ ANA DİLİ EĞİTİMİNDEKİ İŞLEVLERİYLE İLGİLİ BAZI TESPİTLER
-   `929088` [0.931] Abdurrahman Cahit Zarifoğlu'nun "Ağaçkakanlar" adlı eserinin kelime grupları ve Türkçe eğitimi açısı

**v2 top-5 retrieved:**
-   `565656` [0.897] İstatistiksel doğal dil işlemede derin öğrenme yöntemleri kullanılarak çevrimiçi Türkçe akademik der
-   `621585` [0.887] Türkçe morfolojik analiz için yeni bir yöntem
-   `256758` [0.883] Türkçe için tümleşik bir biçimbirim çözümleme ve sözcük türü tespit yöntemi
-   `580794` [0.881] Üretim sürecinin doğal dil işleme ile düzenlenmesi
-   `630095` [0.879] Üretim süreçlerinde doğal dil işleme kullanılarak makine öğrenimi

---

## q02 — `computer_science`

**Question:** Türkçe metin sınıflandırmada Transformer tabanlı modellerin (BERT vb.) avantajları ve sınırlılıkları nelerdir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.30 | 0.40 | +0.10 |
| faithfulness | 0.25 | 0.35 | +0.10 |
| coverage | 0.20 | 0.30 | +0.10 |
| holistic | 1 | 2 | +1 |

**Retrieval overlap (top-5):** 0/5 same chunks. 5 only in v1, 5 only in v2.

**v1 top-5 retrieved:**
-   `265360` [0.906] Türkçede belirteç tümcecikleri: Sözbilimsel yapı çözümlemesi çerçevesinde bir sınıflandırma önerisi
-   `art-467774` [0.890] Türkiye Türkçesinde Kapalı Gövde Örnekleri
-   `597036` [0.883] Başkurt Türkçesinde fiil-tamlayıcı ilişkisi
-   `art-108889` [0.882] Hâfız Sâmi Gazellerinde Terennüm Kelimeleri ve Kullanımı
-   `234320` [0.876] Sümer dili'nin biçimbilimsel ve sözdizimsel yapısı

**v2 top-5 retrieved:**
-   `343705` [0.888] Bilimsel makalelerin metin işleme yöntemleri ile sınıflandırılması
-   `735613` [0.880] Çift yönlü enkoder transformatör tabanlı Türkçe metin sınıflandırma derin öğrenme modeli geliştirilm
-   `606859` [0.875] Derin öğrenme yöntemleri ile Türkçe metinlerde benzerlik tespiti
-   `859818` [0.867] Geleneksel makine öğrenimi ve derin öğrenme modelleri ile Türkçe metin sınıflandırmada kelime temsil
-   `222323` [0.867] Türkçe metinler için konu belirleme sistemi

---

## q03 — `computer_science`

**Question:** Derin öğrenme yöntemleri Türkiye'deki sel ve taşkın tahmininde nasıl uygulanmıştır?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.30 | 0.30 | +0.00 |
| faithfulness | 0.40 | 0.40 | +0.00 |
| coverage | 0.40 | 0.20 | -0.20 |
| holistic | 2 | 2 | +0 |

**Retrieval overlap (top-5):** 0/5 same chunks. 5 only in v1, 5 only in v2.

**v1 top-5 retrieved:**
-   `415386` [0.900] Batı Karadeniz ve pontidlerin yapısının jeofizik verilerle irdelenmesi
-   `art-1060944` [0.894] KAFKAS ARAZİLERİ VE HALKLARININ TASVİRİNE DAİR MATERYALLER TOPLUSU İZAHLI BİBLİYOGRAFYASI
-   `619059` [0.892] Karadeniz'de çevresel güvenlik
-   `249617` [0.892] Tekir Havzası'nın fiziki coğrafyası
-   `550460` [0.892] Anadolu Feneri-Ağva arası kıyı bölgesinin jeomorfolojisi, değişimi ve gelişimi

**v2 top-5 retrieved:**
-   `300941` [0.909] Web servislerine dayalı bir afet ve acil durum yönetim sisteminin tasarlanması: Taşkın tahmin erken 
-   `565593` [0.898] Yapay sinir ağları ile ortalama debi ve maksimum yağış tahmini İstanbul Göksu dere örneği
-   `743690` [0.886] Makine öğrenmesi kullanılarak hidrolojik modelleme: fırtına deresi örneği
-   `334737` [0.881] Taşkın tehlikesinin belirlenmesi amacı ile otomatik yağış miktarı ölçüm sisteminin geliştirilmesi.
-   `439608` [0.879] Taşkın debilerinin tahmini için olasılık modeli yaklaşımı

---

## q04 — `computer_science`

**Question:** Türkçe görüntü tanımada konvolüsyonel sinir ağları ile geleneksel makine öğrenmesi yöntemlerinin karşılaştırması nasıldır?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.30 | 0.20 | -0.10 |
| faithfulness | 0.25 | 0.15 | -0.10 |
| coverage | 0.40 | 0.20 | -0.20 |
| holistic | 2 | 1 | -1 |

**Retrieval overlap (top-5):** 0/5 same chunks. 5 only in v1, 5 only in v2.

**v1 top-5 retrieved:**
-   `art-1165291` [0.898] Konvolüsyonel Sinir Ağları Tabanlı Türkçe Metin Sınıflandırma
-   `art-1082379` [0.894] Türkçe Metin Madenciliği için Dikkat Mekanizması Tabanlı Derin Öğrenme Mimarilerinin Değerlendirilme
-   `477899` [0.883] Derin öğrenme tabanlı yüz ayırt etme ve tanıma
-   `761081` [0.883] Derin öğrenme tabanlı görüntü işleme ile nesne tanıma yöntemlerinde başarım oranı artırma
-   `724182` [0.883] Konvolüsyonel sinir ağlarında ağ eğitiminin iyileştirilmesi

**v2 top-5 retrieved:**
-   `884709` [0.854] Kısa metinlerde makine öğrenmesi yöntemleriyle yüksek performanslı dil tanıma
-   `551894` [0.843] İşaret dili ile akıllı kontrol sistemi
-   `517724` [0.842] Derin öğrenme yöntemi kullanılarak görüntü-tabanlı türk işaret dili tanıma
-   `592014` [0.832] El yazısı karakter tanıma ve resim sınıflandırmada derin öğrenme yaklaşımları
-   `905471` [0.832] Makine öğrenimi yöntemleri ile sağkalım analizi

---

## q08 — `health`

**Question:** Diyabet hastalarında beslenme alışkanlıklarının glisemik kontrol üzerindeki etkisi nasıl değerlendirilmiştir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.70 | 0.70 | +0.00 |
| faithfulness | 0.75 | 0.65 | -0.10 |
| coverage | 0.60 | 0.40 | -0.20 |
| holistic | 3 | 2 | -1 |

**Retrieval overlap (top-5):** 0/5 same chunks. 5 only in v1, 5 only in v2.

**v1 top-5 retrieved:**
-   `art-1085617` [0.927] Adölesanlarda diyabete özgü yeme bozukluğu:‘Diabulimia’ riskinin ve metabolik etkilerinin araştırılm
-   `art-1167421` [0.921] Tip 2 diabetes mellitus hastalarında sezgisel yemenin yeme tutumu ve glisemik kontrol ile ilişkisi
-   `741134` [0.920] Tip 2 diyabetli bireylerde beslenme eğitiminin serum ileri glikasyon son ürünleri, glukoz ve lipid m
-   `501295` [0.919] Bireylerin besin tüketiminin saptanmasında kullanılan yöntemlerin karşılaştırılması
-   `674977` [0.918] Tip 2 diyabetli bireylerde sezgisel yemenin yeme tutumu ve glisemik kontrol ile ilişkisi

**v2 top-5 retrieved:**
-   `681951` [0.893] Tip 1 diyabetli bireylerde diyetin karbonhidrat miktarı ve glisemik indeksinin kan glukoz değişkenli
-   `225630` [0.873] Tip 2 diyabetli hastaların diyetlerinin içerdiği glisemik indeks ve glisemik yükün değerlendirilmesi
-   `817583` [0.861] Irak'ta diyabetli hastalarda beslenme durumunun değerlendirilmesi
-   `340663` [0.861] Tip 1 diyabeti olan ve olmayan bireylerin diyet glisemik indeks ve yükünün hesaplanması ve değerlend
-   `617776` [0.861] Özel bir hastanenin beslenme ve diyet polikliniğine başvuran Tip 2 diyabetli bireylerin beslenme alı

---

## q09 — `health`

**Question:** Kalp damar hastalıklarının teşhisinde ekokardiyografi ve manyetik rezonans görüntülemenin karşılaştırmalı performansı nedir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.40 | 0.60 | +0.20 |
| faithfulness | 0.50 | 0.50 | +0.00 |
| coverage | 0.50 | 0.40 | -0.10 |
| holistic | 2 | 2 | +0 |

**Retrieval overlap (top-5):** 0/5 same chunks. 5 only in v1, 5 only in v2.

**v1 top-5 retrieved:**
-   `243087` [0.937] Fonksiyonel kardiyak manyetik rezonans görüntüleme: Ekokardiyografi bulguları ile karşılaştırmalı de
-   `272414` [0.910] Yavaş koroner akımı olan hastalarda sol ventrikül fonksiyonlarının ve miyokard performans indeksinin
-   `310069` [0.910] Sol ventrikül volüm ve fonksiyonlarının değerlendirilmesinde kardiyak MRG ve ekokardiyografi bulgula
-   `566322` [0.906] Kardiyopulmoner resüsitasyon esnasında monitör ritmi ile ekokardiografi ve nabız değerlendirme bulgu
-   `443737` [0.906] Dekompanse kalp yetersizliği tanısı ile hastaneye yatırılan mitral kapak yetersizlikli hastalarda ha

**v2 top-5 retrieved:**
-   `774731` [0.882] Ejeksiyon fraksiyonu düşük ve korunmuş kalp yetersizliği vakaları için tek sinyal kullanarak makine 
-   `387056` [0.875] Kardiyak MRG
-   `203683` [0.872] Kalp kapak hastalığı ile NT-proBNP ilişkisi
-   `384292` [0.867] Ekokardiyografide görsel olarak değerlendirilen ejeksiyon fraksiyonunun diğer kantitatif yöntemlerle
-   `784428` [0.863] Sol ventrikül sistolik fonksiyonunun anterior mitral annulus hareketi aracılığıyla tahmini

---

## q10 — `health`

**Question:** Türkiye'de hemşirelik öğrencilerinin klinik karar verme becerilerinin geliştirilmesi için kullanılan yöntemler nelerdir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.50 | 0.70 | +0.20 |
| faithfulness | 0.40 | 0.75 | +0.35 |
| coverage | 0.60 | 0.60 | +0.00 |
| holistic | 2 | 3 | +1 |

**Retrieval overlap (top-5):** 1/5 same chunks. 4 only in v1, 4 only in v2.

**v1 top-5 retrieved:**
-   `412496` [0.930] Hemşirelik eğitiminde farklı simülasyon yöntemlerinin öğrencilerin eleştirel düşünme eğilimleri ve ö
-   `589546` [0.926] Simülasyona dayalı eğitimde farklı çözümleme yöntemlerinin hemşirelik öğrencilerinin bilgi ve perfor
-   `629201` [0.922] Hemşirelik öğrencilerinin mesleki hazır oluşluk algılarının güçlendirilmesinde simülasyon stratejisi
- ✓ `468810` [0.921] Yüksek gerçeklikli simülasyon yönteminin hemşirelik öğrencilerinin bilgi ve klinik karar verme düzey
-   `art-1170788` [0.920] Hemşirelik Lisans Öğrencileri İçin Fiziksel Muayenede  Algılanan Öz Yeterlik Ölçeği’nin Türkçe Geçer

**v2 top-5 retrieved:**
- ✓ `468810` [0.893] Yüksek gerçeklikli simülasyon yönteminin hemşirelik öğrencilerinin bilgi ve klinik karar verme düzey
-   `827772` [0.877] Hemşirelik eğitiminde venöz kan örneği alma becerisinin kazandırılmasında sanal oyun simülasyon yönt
-   `896126` [0.872] Öğrencilerin hemşirelik süreci geliştirmesinde simülasyon ve vaka tartışması yöntemlerinin etkinliği
-   `308291` [0.867] Hemşirelik öğrencilerinin ameliyat öncesi ve sonrası hasta bakım yönetimini öğrenmesinde bilgisayar 
-   `625858` [0.858] Hemşirelik eğitiminde simülasyon yönteminin etkinliğinin incelenmesi

---

## q11 — `engineering`

**Question:** Yenilenebilir enerji kaynaklarından rüzgar türbinlerinin Türkiye'deki potansiyeli ve verimliliği üzerine yapılan çalışmalar nelerdir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.60 | 0.35 | -0.25 |
| faithfulness | 0.65 | 0.40 | -0.25 |
| coverage | 0.50 | 0.40 | -0.10 |
| holistic | 3 | 2 | -1 |

**Retrieval overlap (top-5):** 1/5 same chunks. 4 only in v1, 4 only in v2.

**v1 top-5 retrieved:**
- ✓ `523795` [0.953] Türkiye'nin rüzgâr enerji potansiyelinin belirlenmesi
-   `246548` [0.950] Rüzgar türbininde rotor tasarımı ve analizi
-   `245033` [0.950] Rüzgâr enerjisi potansiyeli ölçümü
-   `521748` [0.948] Türkiye'de rüzgar enerji potansiyelinin belirlenmesine yönelik çalışmaların incelenmesi
-   `art-432590` [0.947] Türkiye’de bulunan farklı illerin rüzgâr enerjisi potansiyelinin incelenmesi ve sonuçların destek ve

**v2 top-5 retrieved:**
-   `486752` [0.947] Osmaniye ili sınırları içerisindeki bir bölgenin rüzgar enerjisi potansiyelinin analiz edilmesi
-   `354580` [0.945] Başlangıcından günümüze Türkiye'de rüzgâr enerjisi mevzuatı lisanslı ve lisanssız üretim
-   `814078` [0.938] Türkiye rüzgâr enerjisi potansiyelinin olasılık dağılım parametreleri kullanılarak bölgelere göre an
-   `638341` [0.936] Rüzgâr enerji potansiyelinin istatistiksel yöntemler ve genetik algoritmayla hesaplanması
- ✓ `523795` [0.936] Türkiye'nin rüzgâr enerji potansiyelinin belirlenmesi

---

## q12 — `engineering`

**Question:** Beton karışımına nano malzeme katkılarının mekanik özelliklere etkisi nasıl incelenmiştir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.35 | 0.35 | +0.00 |
| faithfulness | 0.40 | 0.40 | +0.00 |
| coverage | 0.50 | 0.50 | +0.00 |
| holistic | 2 | 2 | +0 |

**Retrieval overlap (top-5):** 1/5 same chunks. 4 only in v1, 4 only in v2.

**v1 top-5 retrieved:**
-   `482605` [0.924] Çelik, sentetik ve karma lif katkılı betonların mekanik özelliklerinin incelenmesi
- ✓ `609554` [0.923] Kimyasal buhar çöktürme yöntemiyle üretilmiş karbon nanotüp ile takviyelendirilmiş betonun bazı özel
-   `450679` [0.922] Nano malzemelerin çimento bağlayıcılı kompozitlerin mekanik özellikleri üzerine etkileri
-   `735216` [0.919] Nano silikanın yüksek oranda uçucu kül içeren betonların taze hal, priz süresi ve mekanik ozellikler
-   `596970` [0.914] Farklı nanopartiküllerin ve endüstriyel atıkların çimento harcı üretiminde değerlendirilmesi

**v2 top-5 retrieved:**
-   `737058` [0.895] Nano silika-mikro silika içeren normal ve yüksek dayanımlı betonlarda donatı-beton aderans özellikle
-   `559967` [0.895] Nanosilika katkılı geleneksel betonların mekanik ve elastik özelliklerinin incelenmesi
-   `793846` [0.889] Nano silikanın çimentonun kısmi ikamesi olarak betonun özellikleri üzerindeki etkisinin incelenmesi
-   `661114` [0.887] Nano malzemeli farklı dayanımlara sahip betonlarda mekanik ve durabilite özelliklerinin incelenmesi
- ✓ `609554` [0.886] Kimyasal buhar çöktürme yöntemiyle üretilmiş karbon nanotüp ile takviyelendirilmiş betonun bazı özel

---

## q13 — `engineering`

**Question:** Endüstri 4.0 kapsamında Türk imalat sanayisinde dijital dönüşüm uygulamaları nasıl ilerlemiştir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.65 | 0.60 | -0.05 |
| faithfulness | 0.70 | 0.50 | -0.20 |
| coverage | 0.60 | 0.40 | -0.20 |
| holistic | 3 | 2 | -1 |

**Retrieval overlap (top-5):** 0/5 same chunks. 5 only in v1, 5 only in v2.

**v1 top-5 retrieved:**
-   `628481` [0.945] Üretimde dijital dönüşüm ve etkileri: Türkiye ekonomisi açısından bir analiz
-   `855726` [0.934] Türkiye'de firmaların endüstri 4.0 olgunluk seviyesinin analizi
-   `art-526700` [0.934] Türkiye’de Dijital Dönüşüme Başlangıç için AHP ve TOPSIS Yöntemleri ile Sektörel Sıralama
-   `730010` [0.928] Dijital dönüşümün işgücü piyasasına etkisi: Sektörel ve mesleki istihdam açısından Türkiye üzerine u
-   `688281` [0.926] Lojistik iş süreçlerinin dijital dönüşümü: Lojistik 4.0 uygulamalarında Türkiye'de mevcut durum

**v2 top-5 retrieved:**
-   `599891` [0.949] Nesnelerin interneti tabanlı endüstri 4.0 sanayi uygulaması
-   `539050` [0.947] Türkiye'de endüstri 4.0 farkıdanlığı
-   `711891` [0.937] Endüstri 4.0 ışığında Türkiye'de sanayi seviyesi: Tosya örneği
-   `568453` [0.935] Endüstri 4.0 sürecinde dijital dönüşüm ve sosyoekonomik yansımalar bağlamında insan kaynaklarının dö
-   `846983` [0.932] Üretim tezgahlarından toplanan verilerin standardizasyonu

---

## q18 — `agriculture`

**Question:** Türkiye'de organik tarım uygulamalarının toprak verimliliğine etkisi nasıl ölçülmüştür?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.60 | 0.60 | +0.00 |
| faithfulness | 0.50 | 0.50 | +0.00 |
| coverage | 0.40 | 0.25 | -0.15 |
| holistic | 2 | 2 | +0 |

**Retrieval overlap (top-5):** 1/5 same chunks. 4 only in v1, 4 only in v2.

**v1 top-5 retrieved:**
-   `480082` [0.933] Türkiye'de organik tarım uygulamalarınıntarihsel gelişimi ve İstanbul ili örneğinden yolaçıkarak Tür
-   `366844` [0.927] Türkiye'de organik tarımın ekonomik analizi: Doğu Karadeniz uygulaması
-   `art-38595` [0.922] Türkiye’deki Organik Tarımın Ekonomik Analizi
- ✓ `784708` [0.920] Organik ve konvansiyonel üretim yapılan tarım topraklarının karbon fraksiyonlarındaki değişimin ve b
-   `art-66905` [0.920] TURGUTLU – SALİHLİ ARASINDA ORGANİK TARIM FAALİYETLERİNİN TOPRAK ÜZERİNDEKİ ETKİLERİ

**v2 top-5 retrieved:**
-   `595629` [0.902] Organik tarımda bitki besleme ve gübre yönetimi
-   `680018` [0.897] Türkiye'de organik tarım piyasası: İlkeler ve uygulamalar
- ✓ `784708` [0.895] Organik ve konvansiyonel üretim yapılan tarım topraklarının karbon fraksiyonlarındaki değişimin ve b
-   `349201` [0.895] Organik tarım ve Türkiye'de organik tarımın istihdam yaratma potansiyeli
-   `773275` [0.887] Organik tarım sektörü potansiyeli: Aydın ili örneği

---

## q19 — `veterinary`

**Question:** Sığırcılıkta yapay tohumlama tekniklerinin döl verimi üzerindeki etkileri nedir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.10 | 0.50 | +0.40 |
| faithfulness | 0.10 | 0.60 | +0.50 |
| coverage | 0.20 | 0.40 | +0.20 |
| holistic | 1 | 2 | +1 |

**Retrieval overlap (top-5):** 0/5 same chunks. 5 only in v1, 5 only in v2.

**v1 top-5 retrieved:**
-   `687126` [0.912] Biyolojik ve kimyasal gübrelerin yulafın ot ve tohum verimi ile kalitesine etkileri
-   `377107` [0.908] Sperm dondurma yöntemlerinin gebelik sonuçlarına etkisi
-   `art-62602` [0.904] KİMYASAL GÜBRELERİN ÇEVRE KİRLİLİĞİ ÜZERİNE ETKİLERİ VE ÇÖZÜM ÖNERİLERİ
-   `406198` [0.902] Hücre içine girebilen bazı kriyoprotektanlarla dondurulan koç spermasının in vitro embriyonik gelişi
-   `483002` [0.898] Erkek infertilitesi nedeniyle yapılan intrasitoplazmik sperm enjeksiyonu sikluslarında mikroakışkan 

**v2 top-5 retrieved:**
-   `6702` [0.849] Hindilerde yapay tohumlama uygulamaları üzerine bir araştırma
-   `515881` [0.845] Farklı büyüklükteki süt sığırı işletmelerinde döl verimi parametrelerinin belirlenmesi
-   `738046` [0.841] Sağmal sütçü ineklerde cinsiyeti belirlenmiş spermanın kullanımı
-   `312018` [0.832] Akkeçilerde mevsim dışı kızgınlık oluşturma ve trans?servikal tohumlama olanakları
-   `786133` [0.831] Farklı sıcaklıklarda çözdürülen boğa ‎spermasının çözüm sonrası farklı periyotlarda ‎spermatolojik p

---

## q23 — `physics`

**Question:** Süperiletken malzemelerin enerji depolama uygulamaları üzerine yapılan deneysel çalışmalardaki bulgular nelerdir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.30 | 0.30 | +0.00 |
| faithfulness | 0.40 | 0.25 | -0.15 |
| coverage | 0.30 | 0.20 | -0.10 |
| holistic | 2 | 1 | -1 |

**Retrieval overlap (top-5):** 0/5 same chunks. 5 only in v1, 5 only in v2.

**v1 top-5 retrieved:**
-   `854798` [0.923] Enerji depolama aracı olarak süperkapasitörlerin ekstrapolasyon uygulamaları yardımı ile gelecek tah
-   `566287` [0.917] Süperkapasitif enerji depolama sistemlerinin elektrokimyasal ve empedans analizleri
-   `865183` [0.917] Nanolif süperkapasitörlerin etkin depolama mekanizmalarının araştırılması
-   `657663` [0.913] Bor katkılı ve biyokütle temelli karbon süperkapasitör enerji depolama malzemelerinin geliştirilmesi
-   `555047` [0.911] Yüksek ve düşük sıcaklık dayanımına sahip aktif karbon temelli süperkapasitörlerin geliştirilmesi

**v2 top-5 retrieved:**
-   `877555` [0.902] Bor ile güçlendirilmiş aerojel tabanlı süperkapasitörlerin geliştirilmesi
-   `202990` [0.887] Süper iletken manyetik yatakların analizi ve modellenmesi
-   `198389` [0.874] İkinci tür süperiletkenlerde yüksek sıcaklıkta vorteks dinamiği
-   `426753` [0.864] Yüksek değerlikli katyon (W, Mo) katkılı BSCCO külçe süper iletkenlerin üretimi ve fiziksel karakter
-   `737882` [0.863] Farklı asitlerle katkılanmış polianilinin sentezi, karakterizasyonu ve süperkapasitör uygulaması

---

## q24 — `chemistry`

**Question:** Yeşil kimya prensiplerinin ilaç üretim süreçlerindeki uygulamaları nelerdir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.70 | 0.60 | -0.10 |
| faithfulness | 0.65 | 0.50 | -0.15 |
| coverage | 0.60 | 0.40 | -0.20 |
| holistic | 3 | 2 | -1 |

**Retrieval overlap (top-5):** 1/5 same chunks. 4 only in v1, 4 only in v2.

**v1 top-5 retrieved:**
-   `art-579987` [0.917] Daha temiz analizler: Yeşil kimya
-   `725500` [0.901] Ayırma işlemlerinde yeşil kimya uygulamaları: Karşılaştırılmalı bir çalışma
-   `410736` [0.896] Yeşil laboratuvar uygulamaları
-   `830472` [0.885] Kozmetik ürünlerde çeşitli organik maddelerin belirlenmesi için farklı mikroekstraksiyon yöntemlerin
- ✓ `491367` [0.882] Yeşil tedarik zinciri uygulamaları üzerine kimya sektöründe bir alan araştırması /

**v2 top-5 retrieved:**
- ✓ `491367` [0.869] Yeşil tedarik zinciri uygulamaları üzerine kimya sektöründe bir alan araştırması /
-   `442602` [0.842] Mikrobiyal ve enzimatik reaksiyonlar kullanılarak biyoteknolojik yöntemlerle biyoaktif maddelerin se
-   `182329` [0.839] Kimya eğitiminde "yeşil kimya" konusunun öğretimi ile ilgili çeşitli değerlendirmeler
-   `526604` [0.836] Oksidasyon katalizörü olarak çeşitlikoordinasyon bileşiklerinin hazırlanması,karakterizasyonu ve etk
-   `221932` [0.831] 3,4-dihidroizokinolinyum klorokromat ve 3,4- dihidroizokinolinyum florokromat sentezi ve yükseltgeme

---

## q25 — `biology`

**Question:** Mikroplastiklerin sucul ekosistemlerdeki canlılar üzerindeki ekotoksikolojik etkileri nasıl araştırılmıştır?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.60 | 0.40 | -0.20 |
| faithfulness | 0.50 | 0.50 | +0.00 |
| coverage | 0.40 | 0.30 | -0.10 |
| holistic | 2 | 2 | +0 |

**Retrieval overlap (top-5):** 0/5 same chunks. 5 only in v1, 5 only in v2.

**v1 top-5 retrieved:**
-   `698530` [0.916] Küçükçekmece lagünü bağlantı alanı yüzey sularındaki mikroplastiklerin mevsimsel ve alansal değişiml
-   `art-53368` [0.915] DENİZEL MİKROALG BİYOTOKSİNLERİ VE ETKİLERİ - MARINE MICROALGAE BIOTOXINS AND THEIR EFFECTS
-   `904907` [0.910] Kültür ve doğal çipura (Sparus aurata L.1958) balığında olası mikroplastik kirliliğinin incelenmesi:
-   `art-1058792` [0.909] Mikroplastiklerin Canlılara Etkileri
-   `461741` [0.907] Atıksulardaki mikroplastik kirliliğinin incelenmesi

**v2 top-5 retrieved:**
-   `587791` [0.912] İstanbul'un Karadeniz kıyılarında mikroplastik kirliliğinin araştırılması
-   `734369` [0.905] Su kaynaklarında mikroplastik riski ve arıtma yöntemlerinin araştırılması
-   `678285` [0.900] Mikroplastikler için AHPve bulanık çıkarım sistemi kullanılarak bütüncül bir çevresel risk değerlend
-   `815780` [0.897] Antropojenik baskılar etkisinde aksu çayı ve kollarının zamana ve mekana bağlı mikroplastik kirliliğ
-   `881569` [0.886] Yüzme havuzlarında mikroplastik kirliliğinin araştırılması

---

## q28 — `multi_domain`

**Question:** Yapay zeka teknolojilerinin tıbbi tanı süreçlerine entegrasyonu hangi etik ve hukuki konuları gündeme getirmektedir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.70 | 0.70 | +0.00 |
| faithfulness | 0.80 | 0.75 | -0.05 |
| coverage | 0.80 | 0.80 | +0.00 |
| holistic | 4 | 3 | -1 |

**Retrieval overlap (top-5):** 1/5 same chunks. 4 only in v1, 4 only in v2.

**v1 top-5 retrieved:**
-   `art-1599210` [0.915] Tıp fakültesi öğrencilerinin sağlıkta yapay zekanın uygulanabilirliği ve etiği hakkındaki görüşlerin
- ✓ `905678` [0.910] Yapay zekâ sistemlerinin tıbbi görüntüleme alanında kullanımında etik: Radyoloji uzmanlarının görüş 
-   `art-1673372` [0.909] YAPAY ZEKA İLE TERAPİ: TERAPÖTİK SÜREÇTE ALGORİTMALARIN ETKİSİ VE ETİK SORUNLAR
-   `854325` [0.902] Sağlık alanında istifleme temelli yapay zeka yöntemleri ve uygulamaları
-   `828086` [0.897] Kişisel verilerin korunması hukuku bağlamında sağlık bilimlerinde yapay zeka kullanımı

**v2 top-5 retrieved:**
- ✓ `905678` [0.922] Yapay zekâ sistemlerinin tıbbi görüntüleme alanında kullanımında etik: Radyoloji uzmanlarının görüş 
-   `889346` [0.891] Geleneksel tıp teşhis yöntemlerinin yapay zeka ile geliştirilen uygulamalarına duyulan güven ve terc
-   `690018` [0.889] Yapay zekanın tıp alanında ikame edici veya tamamlayıcı kullanımının doktorlar üzerindeki etkilerine
-   `619505` [0.881] 5846 sayılı Fikir ve Sanat Eserleri Kanunu kapsamında eser kavramı ve yapay zeka ürünleri
-   `699553` [0.870] Sağlık alanında yapay zeka çalışmaları

---

## q29 — `multi_domain`

**Question:** İklim değişikliğinin Türkiye'deki tarımsal üretim üzerindeki ekonomik etkileri nelerdir?

**Judge scores (v1 → v2):**

| Metric | v1 | v2 | Δ |
|---|---|---|---|
| citation_accuracy | 0.70 | 0.70 | +0.00 |
| faithfulness | 0.60 | 0.60 | +0.00 |
| coverage | 0.60 | 0.40 | -0.20 |
| holistic | 3 | 2 | -1 |

**Retrieval overlap (top-5):** 2/5 same chunks. 3 only in v1, 3 only in v2.

**v1 top-5 retrieved:**
-   `886138` [0.952] Türkiye'de iklim değişikliği ve tarımsal üretim ilişkisi
-   `845663` [0.951] İklim değişikliklerinin Türkiye'deki tarım sektörü üzerine etkisi
- ✓ `896188` [0.945] İklim değişikliğinin Türkiye tarımına etkileri
-   `art-785160` [0.940] Türkiye’de İklim Değişikliğinin Tarım  Sektörü Üzerine Etkileri
- ✓ `726716` [0.937] İklim değişikliği ve Türkiye'de tarım üzerine etkileri

**v2 top-5 retrieved:**
-   `299776` [0.936] İklim değişikliği üzerine yapılan çalışmalarrın değerlendirilmesine yönelik bir araştırma
- ✓ `896188` [0.927] İklim değişikliğinin Türkiye tarımına etkileri
- ✓ `726716` [0.926] İklim değişikliği ve Türkiye'de tarım üzerine etkileri
-   `446097` [0.918] Küresel iklim değişikliğinin sektörel düzeyde ve Türkiye tarım sektörü üzerindeki etkilerinin incele
-   `261825` [0.912] İklim değişikliğinin Türkiye'de buğday, arpa ve mısır bitkilerinin verimleri üzerine etkilerinin pan

---
