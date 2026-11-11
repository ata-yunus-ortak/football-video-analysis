# Sahiplik v2 — dış veride seçilmiş H/A/D sistemi

> **Güncel durum (11 Kasım 2026, öğleden sonra):** teslim sistemi **v2.11**'dir
> (`python -m possession.run211`). v2.11, aşağıda anlatılan v2.5 sisteminin üstüne üç ek getirir;
> bunlar belgenin sonundaki "Güncelleme: v2.9" ve "Güncelleme: v2.11" bölümlerindedir. v2.9 bir alt
> teknik basamak olarak duruyor. Dosyayı üretmek için tek adım: `TESLIM-HAZIRLA.cmd`
> ("Teslim adımları" bölümü). Form'a yüklenecek kısa belge `TECHNICAL_DOCUMENT.md`'dir.

Bu belge `possession/` paketindeki sistemi ekip için anlatır. Ayrıntılı İngilizce kayıt
`TECHNICAL_DOCUMENT_V2.md` dosyasındadır. Aşağıdaki anlatım **v2.5**'e göredir. Çekirdeği v2.1
modelidir. v2.5 iki şey ekler:
- Tracking'in konum titreşimini ölçer. Titreşim 0,30 m'yi aşmıyorsa v2.1'i birebir
  çalıştırır, aşıyorsa yumuşatılmış konumlarla v2.3 yolunu çalıştırır (aşağıda "v2.4: gürültü
  kapısı").
- Yayın tracking'ini taktik zamana eşler (iki videodaki maç saatini okuyarak) ve taktik
  topun eksik olduğu kareleri yayın topuyla doldurur. Bunu yalnız iki kamera, ikisinin de
  topu gördüğü yerlerde çok yakın konum veriyorsa yapar (aşağıda "v2.5: yayın topuyla
  doldurma").

## Neden yeni bir sistem?

- Dondurulmuş `clean_model` yalnızca H/A/X üretiyordu; `D` (top oyun dışı) hiç yoktu.
  DFL dış maçlarında karelerin %41-52'si D. spellF1'de D sahiplikleri böldüğü için
  D'siz bir sistem iki ayrı sahipliği tek sahiplik gibi gösterir.
- S001 dizisel modeli H/A tarafında daha iyiydi, ama o da D üretmiyordu ve top görünmeyen
  karelerde X bırakıyordu.

## Veri ve kurallar

- Eğitim/ayar yalnızca dış maçlarda: Sportec/DFL açık verisi (CC-BY 4.0) ve Metrica örnek
  maçları. Barcelona maçı yalnızca son adımda, ekibin kendi bilgisayarında, dondurulmuş
  modelle otomatik çalıştırılır. Çıktı videoyla karşılaştırılmaz, 5 dakikalık açık pencere
  seçimde kullanılmaz, sağlanan veri hiçbir AI hizmetine yüklenmez.
- DFL verisinde her kare için "top ölü mü" (BallStatus) ve "hangi takım" (BallPossession)
  bayrakları var. Organizatör GT'yi aynı yapıda (düzeltilmiş tracking bayrakları) üretmiş.
- Metrica örnek maçlarında olay verisinden (RECOVERY, BALL OUT, SET PIECE...) Metrica'nın
  kendi sahiplik tanımına yakın bir vekil etiket türetildi. Bu tam GT değil, ikinci bir
  doğrulama alanıdır.

## Otomatik tracking'e benzetme (degrade.py)

DFL tracking temiz; yarışmanın ATD'si otomatik ve gürültülü (topun %41'i kayıp). Her eğitim ve
doğrulama kopyası rastgele bir bozulma profiliyle üretilir: top kaybı (kalabalıkta, hızlı
topta, saha dışında daha olası), konum gürültüsü, sahte top tespitleri, oyuncu izlerinde
boşluk ve kısa süreli yanlış takım izleri. Parametre aralıkları organizatörün yayınladığı
toplu istatistiklere göre geniş tutuldu; Barcelona verisine göre ayarlanmadı.

## Model

1. **Özellikler (features.py):** topun görünürlüğü ve son görüldüğü yer, saha çizgilerine
   uzaklık, top hızı/durgunluğu, top darbeleri (vuruş/temas), oyuncu hızları, dizilişler
   (ceza sahası, santra), her takımın topa en yakın oyuncusu, kontrol/temas göstergeleri,
   geçmiş ve gelecek pencerelerde hangi takımın topa yakın olduğu.
2. **İki karar ağacı topluluğu:** P(D) ve P(H | top oyunda). Takımlar yer değiştirilerek de
   eğitilir; çıkarımda iki yön ortalanır, böylece model ev sahibi/deplasman yanlılığı taşımaz.
3. **İkinci aşama (stack.py):** birinci aşamanın olasılıklarının çevredeki 0,2-10 saniyede
   nasıl değiştiğini özetleyen 48 özellikten aynı iki olasılığı yeniden tahmin eder. Eğitim
   girdisi, o maçı hiç görmemiş birinci aşama modellerinden gelir (maç dışarıda bırakmalı).
4. **Zamansal çözücü (decode.py):** H/A/D üç durumlu Viterbi. Takım değiştirme, oyunun durması
   ve yeniden başlaması için ayrı maliyetler var. Maliyetler dış doğrulama maçlarında resmi
   spellF1 ile seçilir (seçilen: takım değişimi 3, durma/başlama 60, ölü top eğilimi -0,3).
5. **Gürültü kapısı (noise.py, v2.4):** oyuncu ve top konumlarının kareden kareye titreşimini
   ölçer; 0,30 m'yi aşarsa konumları ±2 karelik ortalamayla yumuşatıp gürültülü veriyle
   eğitilmiş v2.3 modellerini kullanır (`smooth.py`, `models/possession-v23.npz`), aşmazsa
   v2.1'i aynen çalıştırır.

## Sonuçlar (dış doğrulama; yarışma puanı değil)

Aynı 8 bozulmuş doğrulama kopyası (DFL J03WN1/J03WR9 + Metrica 1-2, tohum 101/102), resmi
spellF1 ortalaması; her aday için çözücü maliyetleri aynı ızgaradan seçildi:

| aday | spellF1 | DFL | Metrica | macroF1 |
|---|---|---|---|---|
| v2, tek aşama | 0,6218 | 0,6359 | 0,6078 | 0,8577 |
| **v2 + ikinci aşama (seçilen)** | **0,6312** | 0,6466 | 0,6158 | 0,8607 |
| v3 özellikleri, tek aşama | 0,6199 | 0,6321 | 0,6078 | 0,8565 |
| v3 + ikinci aşama | 0,6302 | 0,6439 | 0,6166 | 0,8604 |
| organizatör baseline_smooth50 mantığı | 0,196 | 0,172 | 0,220 | 0,556 |
| ekibin S001 modeli | 0,196 | 0,145 | 0,247 | 0,400 |

**Ayrılmış test (dondurmadan sonra, tek sefer):** Son paket (DFL'nin 6 maçıyla eğitilmiş,
SHA-256 `1cd59ba5…`) Metrica örnek maç 3'ün iki bozulmuş kopyasında spellF1 **0,664** aldı
(kopyalar: 0,625 ve 0,702; macroF1 0,836). Aynı kopyalarda organizatör baseline mantığı 0,219,
S001 0,265. Bu sonuç hiçbir seçimi değiştirmedi.

**Stres testleri (yalnız rapor):** hafif bozulma 0,700 (baseline 0,296); sert bozulma 0,584
(0,170); sert + duraklamalarda top çok daha sık kayıp 0,621 (0,188). DATA.md'de anlatılan ama
eğitimde benzetilmeyen tracker hatalarından kopyalanmış oyuncular (maç başına ~140) etkisiz
(0,610→0,610). 1-5 s süren sahte top izleri (maç başına ~85) puanı 0,025 düşürüyor; en
hassas olduğumuz hata türü bu. Kimlik değişimi testinde yalnız 0-2 değişim oluştu, çünkü
değişim yalnız 2 m içindeki takım arkadaşları arasında benzetildi; bu test zayıf kaldı.

**Tekrar üretilebilirlik:** Dondurulmuş paket, Python 3.10/numpy 1.26.4 ve Python 3.13/numpy
2.5.3 ile aynı CSV'yi (aynı SHA-256) üretti. Bu, hem sentetik bir ATD'de hem de 143.761
karelik dış bir EPTS dosyasında denendi (Metrica örnek maç 3 tracking'i; etiketler okunmadı;
45 s, 1,2 GB bellek). Barcelona dosyası 199.319 kare olduğu için 1-2 dakika sürmesi beklenir.

**Bu sayılar ne demek, ne demek değil?** Başka sağlayıcıların etiketleriyle (DFL bayrakları,
Metrica olaylarından türetilmiş vekil etiketler), yapay olarak bozulmuş başka maçlarda ölçülmüş
uyumdur. Barcelona maçındaki puanı tahmin etmez; aynı koşullarda baseline'a göre ~3 kat daha
iyi olduğunu gösterir. Adaylar arasındaki 0,001-0,002'lik farklar gürültü düzeyindedir; kayıtlı
kural en yüksek ortalamayı seçmeyi söylediği için v2 + ikinci aşama seçildi.

**Nerede iyi, nerede zayıf?** Doğrulama kopyalarında gerçek duraklamaların %94'ü bulunuyor
(başlangıcın %74'ü, bitişin %81'i 1 s içinde). Takım değişimlerinde ise yalnız yaklaşık yarısı
1 s içinde yakalanıyor (duyarlılık %51, kesinlik %70). Sistem gerçekte olandan yaklaşık üçte bir
daha az takım değişimi tahmin ediyor; hızlı top alışverişlerini ve çekişmeli topları tek
sahiplikte birleştiriyor. İkinci aşamanın kazancı çoğunlukla duraklama sınırlarının
zamanlamasından geliyor.

## Çalıştırma (yalnız ekip bilgisayarında)

Tek adım: `TESLIM-HAZIRLA.cmd` (ayrıntısı "Teslim adımları" bölümünde). Elle:

```powershell
python -m pip install -r requirements-possession.txt
python -m possession.run29 --data-dir C:\yol\mtah2027-data --out C:\yol\yeni-cikti
python <organizer-repo>\evaluation\validate_submission.py C:\yol\yeni-cikti\submission.csv
```

Sonuçlar ve sınırlar için `TECHNICAL_DOCUMENT.md`, `TECHNICAL_DOCUMENT_V2.md` ve
`possession-v*-results.json`.

## Öğrenmek için: parçalar neden böyle?

- **spellF1 neyi ödüllendirir?** Her sahiplik (aynı takımın top oyundayken kesintisiz dönemi)
  tek bir nesne sayılır ve gerçek sahipliklerle zaman örtüşmesine (IoU) göre birebir eşlenir.
  Kare doğruluğu yüksek ama titreyen (çok sayıda kısa sahiplik üreten) bir sistem düşük puan
  alır. Bu yüzden kare kararlarının üstüne "sahiplik bütünlüğünü" koruyan bir çözücü gerekir.
- **D neden bu kadar önemli?** D sahiplikleri böler. H-D-H iki ayrı sahipliktir; D kaçırılırsa
  iki sahiplik tek bir uzun tahmin olur ve ikisi de eşleşmeyebilir. DFL maçlarında karelerin
  %41-52'si D.
- **Domain randomization (degrade.py):** Modeli temiz veride eğitip gürültülü veride
  kullanmak, yalnız temiz veride var olan ipuçlarına (ör. topun hep görünmesi) güvenmesine yol
  açar. Her eğitim kopyasını farklı ve geniş aralıklardan seçilmiş bozulmayla üretince model,
  bozulmadan bağımsız kalan ipuçlarını (oyuncuların toplu yavaşlaması, topun son görüldüğü yer,
  temas eden takım) öğrenmek zorunda kalır.
- **Gradyan artırmalı karar ağaçları:** Yüzlerce küçük karar ağacı sırayla bir öncekinin
  hatasını düzeltir. Eksik değerleri (NaN) doğal olarak işler; topun görünmediği karelerde de
  çalışır. Eğitilen ağaçlar numpy dizilerine aktarıldı; çıkarım için scikit-learn gerekmez.
- **Simetri:** Aynı özellikler ev sahibi/deplasman yer değiştirilerek de hesaplanır ve iki
  sonucun ortalaması alınır. Böylece model "ev sahibi daha çok topa sahip olur" gibi maça özgü
  bir yanlılık öğrenemez; karar yalnız geometriden gelir.
- **Viterbi çözücü:** Her kare için P(H), P(A), P(D) var. Çözücü bütün yarı boyunca en olası
  durum dizisini bulur; her takım değişimine ve her duraklama başlangıcı/bitişine bir "ceza"
  öder. Ceza küçükse titreme artar, büyükse kısa ama gerçek sahiplikler kaybolur. Cezalar dış
  doğrulama maçlarında resmi spellF1 ile seçildi.

- **EPTS dosya düzeni:** ATD'nin ham satırı `kare:grup;grup;...:top` biçimindedir. Hangi
  grubun hangi oyuncuya ait olduğunu metadata'daki `DataFormatSpecification` söyler; bu düzen
  kare aralıklarına göre değişebilir (Metrica örnek maç 3'te 35 oyuncu listelenmiş, satırda 22
  grup var, 11 ayrı düzen tanımı var). Okuyucu artık bu tanımı izliyor; tanım yoksa `Player`
  sırasını kullanıyor. Hata, ayrılmış test maçını çalıştırmaya hazırlanırken, sonuç görülmeden
  bulundu.
- **Ev sahibi kontrolü:** EPTS'de ilk `Team` ev sahibidir (organizatörün baseline'ı da böyle
  okur). DATA.md "ev sahibi Barcelona" dediği için `run.py` takım adlarını da kontrol eder;
  ihracatta sıra ters olsaydı tarafları değiştirirdi. Hangi kuralın uygulandığı `run.json`
  içindeki `teams` alanında yazar.
- **Stacking (ikinci aşama):** Birinci aşama her kareye yalnız o anın ölçümlerinden olasılık
  verir. İkinci aşama, bu olasılıkların çevresindeki saniyelerde nasıl değiştiğine bakar
  (kısa düşüş mü, kalıcı değişim mi?). Aşırı uyumu önlemek için ikinci aşamanın eğitim girdisi,
  o maçı görmemiş birinci aşama modellerinden gelir (maç dışarıda bırakmalı / out-of-fold).
- **Konum gürültüsü ve hız:** 25 fps'te 0,3 m'lik konum titremesi, ardışık karelerden
  hesaplanan hızı saniyede ~10 m'ye kadar bozar. v3 özellik setinde oyuncuların "tempo"su ~1 s
  yer değiştirmeden hesaplanır; gürültü ~25 kat azalır. Hangisinin seçildiği yalnız dış
  doğrulama sonucuna göre belirlenir.

## Denenen ama seçilmeyen genişletmeler (10 Kasım)

**Smart Tagging (v3.0 / v3.1, `possession/smarttags.py`).** Duran top pencereleri ve takım
etiketli evreler ikinci aşamaya kanıt olarak eklendi. Çalışma anındaki güven kapısı, etiketin
takımını yalnız tracking'e dayanan birinci aşamayla karşılaştırıyor; uyumu %60'ın altındaki
grup kapatılıyor. Dış maçlarda Metrica etiketi olmadığından etiketler benzetildi; sayıları
DATA.md'deki kod sayılarına eşitlendi, zamanlama/takım/sahte etiket hataları rastgele verildi.
Tipik etiketlerde kazanç küçük (+0,011 ve yeni kopyalarda +0,002), doğru etiketlerde
+0,019/+0,026, gürültülü etiketlerde hafif kayıp. Kayıtlı kapılar geçilmedi.

**Yayın kamerası (v4, `possession/broadcast.py`).** İki kayıt top yörüngeleri ve oyuncu
eşleşmesiyle otomatik eşlendi (sentetik akışta kabul edilen karelerin %98'i doğru, zaman hatası
0 kare), taktik top boşlukları yayındaki topla dolduruldu. Top daha çok kare görünür oldu ama
puan düştü (0,6312→0,6251): ikinci kameranın ~1 m'lik kalibrasyon hatası, "topa en yakın
oyuncu"yu değiştirip sahte sahiplik değişimleri üretiyor.

**Top konum hatasına duyarlılık ve v2.2.** v2.1, topa eklenen 0,5 m rastgele hatada
0,610'dan 0,537'ye, 1 m'de 0,492'ye, yavaş değişen 1 m kaymada 0,519'a düşüyor (havadaki
topun izdüşüm hatası etkisiz). Eğitimde yalnız 0,05-0,3 m hata görmüştü. v2.2 aynı modeli
daha geniş top hatasıyla (0,05-0,6 m + 0-0,6 m kayma) eğitti: gürültülü kopyalarda +0,016,
eski kopyalarda -0,005, toplamda +0,005. Kayıtlı +0,010 eşiği geçilmedi; v2.1 kaldı. Gerçek
top hatası küçükse v2.1, büyükse v2.2 daha iyi olurdu; bunu ölçmek yasak olduğu için kural
belirleyici oldu. Bu, teknik dokümanda en büyük bilinen risk olarak yazıldı.

**Oyuncu konum hatası ve v2.3.** Oyunculara 0,5 m rastgele hata eklenince v2.1 0,610'dan 0,495'e
düşüyor; bu, toptaki hatadan da büyük bir etki. v2.3 konumları ±2 karelik (0,2 s) hareketli
ortalamayla yumuşattı ve eğitimde 0,6 m'ye kadar top/oyuncu hatası gördü. 24 kopyada +0,014,
oyuncu hatası 0,38-0,44 m olan kopyalarda +0,044 kazandı. Ama hatanın 0,3 m'yi geçmediği eski
kopyalarda 0,014 kaybetti; kayıtlı en fazla 0,010 kayıp sınırı aşıldığı için seçilmedi. Sonuç
şunu gösteriyor: hata küçükse v2.1, büyükse v2.3 daha iyi.

**Ders:** Daha çok veri, ancak doğruluğu ölçülebiliyorsa yardım ediyor. Bu yarışmada hata
profilini ölçmenin tek yolu sağlanan maçın doğru cevabı ve o yasak. Bu yüzden ekleri ancak
bozulmaya karşı dayanıklıysa ve kazancı açıksa seçiyoruz.

## v2.4: gürültü kapısı (teslim sistemi, 10 Kasım)

**Sorun.** v2.1 küçük konum hatalarına güveniyor: eğitimde en fazla 0,3 m hata gördü. v2.3 büyük
hatada çok daha iyi, küçük hatada biraz daha kötü. Sağlanan maçın hatasını bilmiyoruz.
Doğru cevaba bakarak ölçmek yasak.

**Çözüm.** Hatanın "titreşim" kısmını verinin kendisinden ölçmek mümkün. Bir oyuncunun ardışık
üç karedeki konumundan ikinci fark alınır: `x[t+1] - 2·x[t] + x[t-1]`. Gerçek koşu 25 kare/s'de
bu farkı 1 cm'den az değiştirir; kareden kareye rastgele hata ise büyütür. Bağımsız hata için
bu farkın standart sapması hatanın √6 katıdır. Ölçü olarak sağlam ölçek (MAD) kullanılıyor, bu
yüzden vuruşlar ve kısa sahte tespitler sonucu kaydırmıyor. Oyuncularda slot başına ölçülüp
ortanca alınıyor.
- Dış maçlara eklenen 0,1 / 0,3 / 0,5 m hata 0,10 / 0,30 / 0,50 m olarak ölçülüyor.
- Temiz DFL verisi 0,006 m, Metrica örnek verisi 0,001 m çıkıyor (sağlayıcı yumuşatmış).

**Kural (sonuçlardan önce kaydedildi).** Oyuncu ya da top titreşimi 0,30 m'yi aşarsa v2.3 yolu
çalışır, aşmazsa v2.1 birebir çalışır ve dosya `possession.run` ile aynıdır. 0,30 m, v2.1'in
eğitimde gördüğü en büyük hatadır; sonuca bakılarak ayarlanmadı. Kapı etiket, video ya da doğru
cevap kullanmıyor.

**Doğrulama.** Kural, hiç kullanılmamış 24 yeni kopyada denendi. Her kopyanın kendi bozulma
tohumu vardı:

| kopyalar (8'er) | v2.1 | v2.4 | kapının seçtiği yol |
|---|---|---|---|
| v2.1 bozulması (hata ≤ 0,3 m) | 0,654 | 0,654 | 8/8 v2.1 |
| + top hatası 0,3-0,6 m ve kayma | 0,583 | 0,628 | 8/8 v2.3 |
| + oyuncu hatası 0,3-0,6 m | 0,572 | 0,644 | 8/8 v2.3 |
| 24 kopya | 0,603 | 0,642 | |

İki kayıtlı koşul da sağlandı: toplamda +0,039 kazanç (eşik +0,010), eski tip kopyalarda kayıp
yok (izin -0,005). v2.4 seçildi ve v2.3 modeli 6 DFL maçıyla yeniden eğitilip donduruldu.

**Ayrılmış test (dondurmadan sonra, tek sefer; karar kapısı değil).** Metrica örnek maç 3:

| kopyalar (2'şer) | kapı | v2.1 | v2.4 |
|---|---|---|---|
| v2.1 bozulması (201, 202) | v2.1, v2.1 | 0,664 | 0,664 |
| + top hatası ve kayma (401, 402) | v2.3, v2.3 | 0,645 | 0,660 |
| + oyuncu hatası (601, 602) | v2.3, v2.3 | 0,602 | 0,670 |
| 6 kopya | | 0,637 | 0,665 |

v2.1 paketi eski ayrılmış test değerlerini birebir üretti (0,6253 ve 0,7021); bu, hattın
değişmediğinin kanıtı.

**Tekrar üretilebilirlik.** `run24`, Python 3.10/numpy 1.26.4 ve Python 3.13/numpy 2.5.3 ile
aynı dosyaları üretti. Denenen durumlar: sentetik ATD'de iki yol; Metrica maç 3'ün tam boyutlu
tracking'i (titreşim 1 mm'nin altında, v2.1 yolu; dosya `possession.run` ile aynı); aynı
tracking'e 0,5 m oyuncu hatası eklenince v2.3 yolu. Her çalıştırma yaklaşık 60 s sürdü ve en
fazla 1,3 GB bellek kullandı.

**Dürüst sınırlar.**
- Kopyaların hatası ya ≤ 0,29 m ya da ≥ 0,34 m idi; kapı hep doğru yolu seçti. 0,30 m'ye
  çok yakın hatada ne olacağı ölçülmedi. Orada iki yolun da yakın sonuç vermesi bekleniyor.
- Yavaş değişen kayma ve sağlayıcının önceden yumuşattığı hata titreşim üretmez; kapı bunları
  göremez ve v2.1'i seçer.
- v2.4, v2.3 sonuçlarını gördükten sonra tasarlandı. Bu yüzden yeni kopyalarla doğrulandı,
  ama kopyalar aynı dört maçtan geliyor.
- Sağlanan maçta kapının hangi yolu seçtiğini `run.json` gösterir. Bu bilgi de sağlanan
  maçtan türetildiği için asistana iletilmez.

## v2.5: yayın topuyla doldurma (teslim sistemi, 10 Kasım)

**Neden?** Yalnız rapor amaçlı iki ölçüm hatanın yerini gösterdi:
- Temiz tracking'de puan 0,748, otomatik tracking benzeri bozulmada 0,610. Aynı bozulmada top
  hiç kaybolmasa 0,700 olurdu. Yani kaybın yaklaşık üçte ikisi topun kaybolmasından geliyor.
- "Top ölü mü" kararını doğru cevapla değiştirmek puanı yalnız 0,631'den 0,647'ye çıkarıyor.
  "Hangi takımda" kararını değiştirmek 0,912'ye çıkarıyor. Asıl hata oyun içindeki takım
  kararlarında; bunu da en çok eksik top bozuyor.

**Nasıl?**
1. Yayın karelerini taktik karelere eşle: önce iki videodaki maç saati otomatik okunur
   (OCR, 5 saniyede bir). Saatten her yarı için kaba zaman farkı çıkar (±1 s). Sonra 60 s'lik
   pencerelerde top ve oyuncu konumlarıyla kare düzeyine inilir. Saat okunamazsa iki top
   yörüngesinin benzerliğinden aranır.
2. Bir yayın karesi, en az 3 oyuncusu taktikteki aynı takım oyuncularına 2 m içinde (ortanca)
   düşüyorsa kabul edilir. Tekrarlar ve yakın çekimler böylece elenir: tekrarda saat canlı
   akar ama görüntü eskidir, oyuncular tutmaz.
3. **Güven kapısı:** iki kameranın da topu gördüğü karelerde aradaki ortanca uzaklık
   0,50 m'den küçükse ve en az 120 s örtüşme varsa doldurma yapılır. Bu uzaklık taktik
   hatayı da içerdiği için yayın hatasına bir üst sınırdır.
4. Yalnız taktik topun eksik olduğu kareler doldurulur. Taktik top asla değiştirilmez.

**Doğrulama** (sentetik yayın akışları, 16 yeni kopya, yarışma puanı değil):

| Yayın tracking kalitesi | v2.4 | v2.5 | Kapı açıldı |
|---|---|---|---|
| İyi (sapma ≤ 0,2 m, gürültü ≤ 0,25 m) | 0,651 | 0,675 | 15/16 |
| Orta | 0,651 | 0,655 | 1/16 |
| Kötü | 0,651 | 0,651 | 0/16 |

İyi akışlarda puanlanan karelerde top görünürlüğü %53'ten %63'e çıktı. Bir kopyada yörünge
araması yanlış eksen çevirmesine ve sahte bir zaman farkına kilitlendi: eşleme olmadı, kazanç
kayboldu ama zarar da olmadı. Saatle çapalanan sürüm (v2.5b), saat okumaları sentetik
olarak üretilmiş 16 yeni kopyada denendi: okunabilirlik %50-95, hatalı okuma %1-3, uzatma
dakikalarında saat tekrarı var. İyi akışlarda v2.4 0,635, v2.5 0,672, v2.5b 0,672 çıktı;
başarısız eşleme ikisinde de 0. Yani bu kopyalarda iki eşleme de çalıştı ve saatin faydası
(yukarıdaki türden bir başarısızlığı önlemek) yeniden görülmedi. Kayıtlı kural "v2.5'ten kötü
olmamak ve daha fazla başarısız eşleme yapmamak" olduğu için saat çapası teslim sistemine girdi.
Saat dosyası verilmezse sistem yörünge eşlemesine döner.

**Tekrar üretilebilirlik.** `run25`, Python 3.10/numpy 1.26.4 ve Python 3.13/numpy 2.5.3 ile
tam boyutlu bir dış çiftte aynı dosyayı üretti: bozulmuş Metrica maç 3 tracking'i, 146 bin
karelik sentetik yayın akışı ve sentetik saat okumaları. Saatli ve saatsiz eşleme de aynı
dosyayı verdi.

**Dürüst sınırlar.**
- Yayın akışları sentetik. Gerçek yayın tracking'inin doğruluğunu bilmiyoruz; çalışma anında
  kapı karar veriyor. Kapının sonucunu (`run.json` içindeki `fusion`) asistana iletmeyin.
- Gerçek yayının simülatörde olmayan kusurları (yakınlaştırmaya bağlı hata, geçerli
  işaretlenmiş tekrar, kısmi görüşte takım karışması) sonucu değiştirebilir.
- Denenen v2.6 (öğrenilmiş "takım değişimi olasılığı" ile değişken geçiş maliyeti) yeni
  kopyalarda yalnız +0,002 getirdi ve seçilmedi.

## Teslim adımları (ekip bilgisayarında)

**Sıra:** önce `GIT-YUKLE-V2.cmd` (kod GitHub'a gider), sonra `TESLIM-HAZIRLA.cmd` (dosya üretilir
ve denetlenir), sonra Form.

### 1. `GIT-YUKLE-V2.cmd`

Yalnız adı yazılı kaynak dosyalarını, iki model paketini, plan/sonuç kayıtlarını ve belgeleri
ekler. Commit'ten önce dosya listesini gösterip onay bekler. Listede `.csv`, `.xml`, `.mp4`
gibi veri türü bir dosya çıkarsa kendiliğinden durur ve hiçbir şey commit etmez. İki commit
oluşturur: sahiplik sürümü ve yalnız bu bilgisayarda duran dış kaynaklı kontrol referansı
araçları. Yüklemeden sonra GitHub'da **Actions** sekmesinde testlerin sonucuna bakın (Ubuntu ve
Windows). Windows satırı kırmızıysa hangi testin kaldığını (yalnız test adını) iletin.

CI'ın sahiplik testlerini gerçekten çalıştırması için bir satırı **sizin** değiştirmeniz gerekir
(asistan iş akışı dosyalarına yazamaz): `.github\workflows\tests.yml` içinde
`python -m pip install -r requirements.txt` satırının sonuna ` -r requirements-possession.txt`
ekleyin, sonra `GIT-YUKLE-V2.cmd` çalıştırın. Bu yapılmazsa CI yeşil görünür ama sahiplik
testleri atlanmış olur.

### 2. `TESLIM-HAZIRLA.cmd`

Bütün zinciri kendisi yürütür ve ekrana yalnız durum sözcükleri yazar. Programların çıktısı
`%USERPROFILE%\FootballPrivate\teslim\OZEL-log-*.txt` dosyasına gider.

- **Asistana iletilebilir:** ekrandaki `[..]` satırları ve `SONUC` satırı (aynısı
  `PAYLASILABILIR-durum.txt` dosyasında).
- **İletilmez:** log dosyası, `run.json`, `OZEL-kayit.json`, CSV ve belge kopyasının sonundaki
  çalışma kaydı (Ek R).

| satır | ne yapar | FAIL / FARKLI ne demek |
|---|---|---|
| ORTAM | `.venv-possession` ortamını kurar, sabitlenmiş paket sürümlerini denetler | internet ya da Python sürümü (3.10-3.12 gerekir) |
| DEPO | hangi commit'ten çalıştığını yazar | "commit edilmemiş" yazıyorsa önce 1. adım |
| SURUM | dondurulmuş kaynakların ve iki model paketinin sürüm bildirimiyle aynı olduğunu denetler | bir dosya değişmiş ya da bir paket eksik (adı yazılır); üretim yapılmaz |
| TESTLER | sentetik testler | kalan testin adı yazılır |
| PLATFORM | bu bilgisayar, sentetik paketlerde Linux'ta kaydedilen baytların aynısını üretiyor mu (yedi varyant: beşi v2.9 yolu, ikisi kaleci denetimi) | FARKLI olsa da dosya üretilir; fark belgeye yazılır. Yanında farklı çıkan varyantın adı yazar; iletin |
| VERI | sağlanan dosyalar beklenen yerde mi | `viewer-local.cmd` içindeki `MTAH_DATA_DIR` |
| GIRDI OKUMA | sürümün okuyucuları dosyalarda DATA.md'nin yayımladığı toplu olguları görüyor mu (kayıt ve slot sayıları, toplu kare sayıları, kullanılabilir homografi payı); ayrıca iki takip dosyası organizatörün `starter/baseline.py` kodunun okuduğu biçimde ikinci kez okunur ve iki okuma kare kare karşılaştırılır | yanında yalnız tutmayan denetimin adı yazılır (ör. `tactical_agrees_with_starter_reading__team_counts`, `tactical_reader_runs__ValueError`); dosya yine üretilmeye çalışılır. Adı iletin: bakılacak yer okuyucudur, model ya da eşik değiştirilmez |
| URETIM | sürümün giriş noktası; hata verirse `possession-release.json` içindeki bir alt basamak | basamak ve hata sınıfı yazılır, ileti yazılmaz |
| BICIM, MAKULLUK | organizatörün biçim kuralları; toplu makulluk aralıkları | MAKULLUK FAIL ise göndermeden önce bildirin |
| ON TESLIM, TESLIM | dosyayı `teslim\<takım>.csv` olarak kopyalar | |
| SAAT OKUMA, SAATLI URETIM | iki videonun saatini okur (ayrı OCR ortamı), dosyayı saat çapasıyla yeniden üretir | saat okunamazsa saatsiz dosya kalır |
| SAATSIZ KARSILASTIRMA | saatli ve saatsiz dosya aynı mı | FARKLI ise organizatörün yeniden üretimi için saat okuma adımı gerekir |
| TEKRAR URETIM | aynı komut ikinci kez aynı baytları veriyor mu | |
| TEMIZ KLON | GitHub'daki dalın taze kopyası aynı dosyayı üretiyor mu (organizatörün koşulu) | ATLANDI ise 1. adım yapılmamış |
| ORGANIZATOR DOGRULAYICI | organizatörün `validate_submission.py` betiği | |
| ACIK PENCERE | açık 5 dakikada yalnız geçti/kaldı denetimi; puan yazılmaz | FAIL ise yalnız eşleme ya da indeks hatası aranır |
| BELGE | `teslim\<takım>.md` = teknik belge + çalışma kaydı (Ek R) | |

İlk satırda takım adını sorar; Google Form'daki yazımla aynı girin. Seçenekler:
`TESLIM-HAZIRLA.cmd --quick` (tekrar, saatsiz ve temiz klon çalıştırmalarını atlar),
`--no-ocr` (saat okumaz), `--team "Takım Adı"`. Tam çalışma, saat okuma dahil bir saati
bulabilir; her dakika "calisiyor" satırı yazılır.

Açık 5 dakikalık pencereye `run_evaluation.py` ile **bakmayın**: o betik puan yazar. Zincirdeki
`ACIK PENCERE` adımı aynı denetimi puan göstermeden yapar ve eşikleri önceden kayıtlıdır
(`possession-final-check-plan.json`).

### Organizatör başlama karesi sorusuna "uygun değil" derse

11 Kasım'da organizatöre, FAQ.md'de yayımlanan ikinci yarı başlama karesinin (113.742) koda sabit
yazılmasının kurallara uygun olup olmadığı soruldu. Yanıt "uygun" ise ya da son güne kadar gelmezse
hiçbir şey değişmez. "Uygun değil" ise yedek yapılandırma kullanılır:

```
TESLIM-HAZIRLA.cmd --release-config possession-release-graded-windows.json
```

Bu yapılandırmanın basamakları `possession-v2.11g` → `possession-v2.9g` → v2.5b → v2.5b yalnız taktik
kameradır.
Hiçbirinde 113.742 sabiti yoktur; modeller ikinci yarının puanlanan penceresinin tamamında çalışır
ve başlama vuruşundan önceki karelere kendileri karar verir. Belgelerde 7. adımın anlatımı o durumda
değişmelidir (asistana haber verin). Sınır: başlama öncesinde modellerin ne yaptığı dış veride
ölçülemedi, çünkü dış takip verileri başlama vuruşuyla başlar. Tam boy provada (aşağıda) uydurma bir
başlama öncesi bölümde 2.934 karenin 2.625'i `D` etiketlendi; bu bir ölçüm değil, yalnız çalıştığının
denetimidir.

### İsteğe bağlı: ayrılmış dış maçta son test (`SON-TEST.cmd`)

Teslimden bağımsızdır; teslim dosyasını değiştirmez. 17 Kasım'dan önce herhangi bir gün, tercihen
teslim zinciri bittikten sonra çalıştırılabilir.

- **Ne:** 7 Kasım'da ayrılan ve o günden beri hiç indirilmeyen DFL maçı J03WMX indirilir (yaklaşık
  420 MB, kamuya açık veri, CC BY 4.0). Maçın dört bozuk kopyası, sağlanan dosyaların düzeninde
  dosyalara yazılır ve dondurulmuş sürümün giriş noktası (`possession.run211`) bu dosyalarda
  çalıştırılır: yalnız taktik kamera ve benzetilmiş iyi / orta / kötü yayınla. Sonuç sağlayıcının
  etiketleriyle, organizatörün ölçütüyle puanlanır.
- **Neden:** sürümün doğrulama maçları seçim sırasında defalarca kullanıldı. Bu, sürümün hiçbir
  kararında rol oynamamış bir maçtaki tek ölçüm olur ve teknik belgeye "ayrılmış maç, dondurmadan
  sonra bir kez" diye yazılır.
- **Kurallar (çalıştırmadan önce `possession-final-test-plan.json` içinde kayıtlı):** bir kez
  çalıştırılır; sonuç ne olursa olsun aynen yazılır; sürüm bu sonuca göre değiştirilmez. Kötü
  çıkarsa sınır olarak raporlanır.
- **Süre:** indirme, dönüştürme ve yaklaşık bir saat hesap. Yarıda kesilirse aynı komut kaldığı
  yerden sürer.
- **Paylaşım:** bu maç dış veri olduğu için ekrandaki sayılar ve
  `possession-final-test-results.json` asistana iletilebilir. Sonra `GIT-YUKLE-V2.cmd` ile sonuç
  dosyasını depoya gönderin.
- **Göstermediği:** yarışma maçındaki doğruluk. Başka sağlayıcı, bizim bozma benzetimimiz, başka
  bir etiket tanımı ve benzetilmiş yayın akışı.

### 3. Form

Yüklenecek iki dosya `%USERPROFILE%\FootballPrivate\teslim` klasöründedir: `<takım>.csv` ve
`<takım>.md`. Depo bağlantısı olarak bu dalın adresini verin. Form son tarihe (17 Kasım) kadar
düzenlenebilir; son yüklenen dosya puanlanır.

Organizatörün 20 Ekim e-postasına göre son teslim **17 Kasım 23:59 CET**, yani Türkiye saatiyle
**18 Kasım 01:59**; Form bağlantısı ve teslim talimatı "14 Kasım'a kadar" e-postayla gelecek. Takım adı,
bütün üyelerin kayıt formunda yazdığı adla aynı olmalı.

### Elle çalıştırmak isterseniz

```powershell
cd C:\Users\Abra\Desktop\Football_analysis-main\mtah-2027\submission-clean
py -3.10 -m venv .venv-possession
.\.venv-possession\Scripts\python.exe -m pip install -r requirements-possession.txt
.\.venv-possession\Scripts\python.exe -m possession.run211 --data-dir <veri kökü> --out <yeni klasör> --tactical-clock <saat>\tactical --broadcast-clock <saat>\broadcast
.\.venv-possession\Scripts\python.exe -m possession.validate <yeni klasör>\submission.csv
```

Veri kökü, içinde `tactical\` ve `broadcast\` klasörleri bulunan klasördür. Eski tek tek
başlatıcılar (`SAHIPLIK-V2-KURULUM.cmd`, `SAAT-OKU.cmd`, `SAHIPLIK-V211-URET.cmd`) duruyor, ama
ekrana toplu sayılar yazarlar; o çıktıyı asistana iletmeyin. Sağlanan veriyi, CSV'yi veya kare
düzeyindeki çıktıyı hiçbir AI hizmetine yüklemeyin.

## Güncelleme, 11 Kasım 2026: v2.9 (gönderim adayı)

Çalıştırma: `TESLIM-HAZIRLA.cmd` (içeride `python -m possession.run29`). v2.5b'ye iki ek:

1. **İkinci yarı başlama vuruşu.** Organizatörün FAQ sayfasına göre ikinci yarı 110.808'den
   puanlanıyor ama oyun 113.742'de başlıyor; aradaki kareler `D`. Sistem artık ikinci yarıyı bu
   kareden başlatıyor. Dış maçlarda ölçülemez; dayanak organizatör açıklaması.
2. **Yayın topunun hizalanması** (`possession/register.py`). İki kameranın birlikte gördüğü
   oyuncuların konum farkı, yayın kamerasının kalibrasyon hatasını ölçer; bu hata yayın topundan
   çıkarılır. Sonra eski kapı (iki kameranın topu 0,50 m içinde uyuşmalı) aynen uygulanır.
   Benzetilmiş yayınla, daha önce kullanılmamış 16 kopyada: orta kalitede 0,653 → 0,681, iyi
   kalitede 0,686 → 0,684, kötüde değişiklik yok. Bunlar yarışma puanı değildir; yayın akışları
   benzetimdir.

   *Düzeltme (K002):* burada önce yazan sayılar (0,647 → 0,678 ve 0,683 → 0,681, "16 yeni
   kopya") yanlış bir kümeye aitti: 16 kopyanın 8'i daha önce v2.6 için kullanılmıştı. Bu 8 kopya,
   sonuçlardan önce kaydedilen bir ek planla yenileriyle değiştirildi ve aynı dört eşik yeniden
   uygulandı; dördü de geçti. İyi kalitede ortalama fark −0,002, tek tek kopyalarda −0,020 ile
   +0,011 arasında: yayın zaten doğruysa hizalamanın etkisi tek maçta iki yöne de gidebilir.

Seçilmeyenler: v2.7 (kayıp topu köprüleyen özellikler, +0,002), v2.8 (eğitime Metrica maçı,
+0,001 / DFL'de −0,011). Ayrıntı: `docs/DENEY_KAYDI_TR.md` P010–P012, K001, K002, R002.
Gönderim belgesi: `TECHNICAL_DOCUMENT.md` (kısa); veri ve lisanslar: `DATA_SOURCES.md`.

## Güncelleme, 11 Kasım 2026 (öğleden sonra): v2.11 — kaleci takım denetimi

Çalıştırma değişmedi: `TESLIM-HAZIRLA.cmd` (içeride artık `python -m possession.run211`). v2.11 teknik
bir hata verirse zincir kendiliğinden bir alt basamağı, v2.9'u çalıştırır ve bunu `URETIM` satırında
yazar. Ayrıntılı kayıt: `docs/DENEY_KAYDI_TR.md` K004.

**Sorun neydi?** Takip dosyası her iz için yalnız konum ve takım veriyor. Takımı izleyici belirliyor;
kaleci ise takım arkadaşlarından farklı forma giyer. Kalecinin izi yanlış takımın kimliğini taşırsa
modellerimiz kalede bir rakip görür. İki kaleci birden yanlışsa daha kötüsü olur: özellikler hangi
takımın hangi kaleye saldırdığını her takımın *ortalama* konumundan çıkarıyor ve iki kaleci bu
ortalamayı ters çevirmeye yetiyor. Dış maçlarda ölçtük: spellF1 0,659 yerine 0,335.
Bozma benzetimimiz bu hatayı içermiyordu (yalnız 1-6 saniyelik takım değişimleri vardı).

**Denetim ne yapıyor?** Özellikler hesaplanmadan önce kaleci izlerini yalnız konumdan bulur: oyun öbür
yarı sahadayken kaleye en yakın olan *ve* herkesin en az 8 m gerisinde duran iz kalecidir. Böyle bir iz
o kaleyi savunmayan takımın kimliğini taşıyorsa savunan takıma aktarılır, ama yalnız iki durumda:

1. o kalenin o yarıdaki kaleci kanıtının çoğu yanlış kimlik altındaysa (kaleci bütün yarı boyunca yanlış
   etiketlenmiş), ya da
2. iz, zaman ve yer olarak bir kaleci izinin devamıysa (kaleci bir süreliğine yanlış etiketlenmiş).

Kimlikler doğruysa hiçbir şey değişmez ve çıktı v2.9'un çıktısıdır. Gürültü kapısı, yayın eşlemesi ve
0,50 m kapısı kimlikleri verildiği gibi kullanmaya devam eder; düzeltilmiş kimlikleri yalnız modeller
görür.

**Neden iki sürüm (v2.10 ve v2.11)?** İlk kural (v2.10) önceden kaydedilen dört eşiği geçti. Dondurmadan
önce neyi taşıdığına baktık: 80 parçanın 77'si gerçekten kaleciydi, 3'ü forvetti (biri, rakip kaleden
13 m uzakta maçın son 2,5 dakikasında hareketsiz duran bir oyuncu). Puan değişmemişti, ama neden
önemliydi: "kaleye en yakın oyuncu" kanıtı, kaleci izlenmiyorken yanlış kişiyi gösterir. Oyunu izleyen
bir kamera uzak kaleciyi hiç göstermeyebilir. Bu durumu benzettiğimizde v2.10 eğitim maçlarında maç
başına 1.700-8.400 saha oyuncusu konumunu yanlış takıma aktardı. Bu yüzden v2.10 yayımlanmadı; kural
yukarıdaki iki koşulla sıkılaştırıldı (v2.11) ve bu durum doğrulamaya iki ek eşik olarak eklendi.
*Öğrenilecek şey:* eşiklerin geçmesi, eşiklerin sormadığı sorulara yanıt değildir; bir düzeltmenin neyi
değiştirdiğine tek tek bakmak, ortalama puanın göstermediğini gösterir.

**Sonuç** (8 yeni bozuk kopya, dış maçlar; yarışma puanı değildir; altı eşik de geçti):

| durum | denetimsiz (v2.9) | denetimli (v2.11) |
|---|---|---|
| kimlikler doğru | 0,659 | 0,660 |
| iki kaleci bütün maç yanlış kimlikle | 0,335 | 0,656 |
| bir kaleci bütün maç yanlış kimlikle | 0,627 | 0,658 |
| iki kaleci maçın %30'unda yanlış kimlikle | 0,642 | 0,659 |
| uzak kaleciyi çoğu zaman göstermeyen kamera (±42 m), kimlikler doğru | 0,649 | 0,649 |
| daha dar kamera (±35 m), kimlikler doğru | 0,646 | 0,646 |
| ±42 m kamera, iki kaleci yanlış (eşik değil) | 0,557 | 0,634 |

Tam boy provada (sentetik paket, kaleci izleri öbür takımın kimliğiyle yazılmış) teslim dosyası denetimle
0,766, denetimsiz 0,431 aldı; kimlikleri doğru olan pakette 0,764 (v2.9 ile 0,763).
Bu prova puanları K005'te düzeltilen etiketlere göredir: K003'te A paketi için yazılan 0,715, duran top
aralıklarının yarısını yitirmiş etiketlerle hesaplanmıştı (`docs/DENEY_KAYDI_TR.md` K005).

**Bilmediğimiz.** Sağlanan takip verisinde böyle bir hata var mı, bakmadık ve bakmayacağız. Hatalar ve
kamera, bizim yaptığımız benzetimlerdir. Uzak kaleci çoğunlukla görüntü dışındaysa (benzetimde ±35 m)
denetim hiçbir şeyi düzeltmez; zarar da vermez. Denetimin sağlanan maçta bir şey taşıyıp taşımadığı
yalnız sizde kalan belge kopyasının Ek R bölümünde ve `run.json` içinde yazar; bunları asistana
iletmeyin.

