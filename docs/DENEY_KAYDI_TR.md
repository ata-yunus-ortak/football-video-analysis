# Deney kaydı

## V021 — Geometri ve zamansal kanıtı birlikte öğrenme, 8 Kasım 2026

355 eğitim adayıyla öğrenildi. Doğrulamada normal/parçalı doğru eşleşmeler
47→46 / 71→71, eşleşmeyenler 104→55 / 220→75. Sabit kontrolde doğru
eşleşmeler 53 ve 85 korundu; eşleşmeyenler 95→83 / 222→165. Normal
kontroldeki %12,6 azalma gerekli %20'yi geçmedi; final kabul başarısız.
Eşik değiştirilmedi. Ayrı deneysel kanıt alanı 1.200 analiz paketine
eklendi; ham kutular, izler ve sahiplik korunuyor. 277 test: 275 geçti,
2 AV atlandı; ilgili 9 test AV ortamında ayrıca geçti.
[Yöntem, kapsam ve yeni dış maç metadata envanteri](TOP_ZAMANSAL_OGRENME_TR.md).

## V020 — Sınırlı gelecek kareyle tespit doğrulama, 8 Kasım 2026

27 sabit süreklilik adayı karşılaştırıldı. Normal taramada bazı adaylar
47 doğru eşleşmenin tamamını koruyup eşleşmeyenleri 104→37 azalttı;
parçalı taramada kayıplar nedeniyle ortak doğrulama koşulu geçilmedi.
Ayrı maç kontrolü çalıştırılmadı. Tahminler gerçek ölçüm yapılmadı;
bilinmeyen referanslar negatif sayılmadı. `ball-temporal-selection-results-v1.json`.

## V019 — Doğal ölçekte eğitim ve tam kare kontrolü, 8 Kasım 2026

212 eğitim parçasıyla iki epoch tamamlandı. Parça doğrulama mAP@50:95
0,20434; tam karede temel 24 doğru / 54 eşleşmeyen adaya karşı yeni model
0,3 eşikte 18 / 21 verdi. Sekiz eşiğin hiçbiri temel doğru eşleşme sayısını
korumadı (en yüksek 22). Aday reddedildi; ayrı maç kontrolü çalıştırılmadı.
SAHI düşük eşik otomatik NMS geçişi sonuç görülmeden kaynak incelemesinde
bulundu; eğitim korunup sabit ağırlıkla GREEDYNMM/IOS değerlendirmesi yeniden
üretildi. Eski kısmi tahminler kullanılmadı. `ball-patch-results-v1.json`.
267 test: 265 geçti, 2 AV atlandı; AV ortamındaki ilgili 9 test ayrıca geçti.
[Yöntem, kapsam ve sınırlamalar](TOP_PARCA_EGITIMI_TR.md).

## V018 — Dış sahne kapsamı ve parça verisi, 8 Kasım 2026

25 ek kesitten 1.875 seyrek kare edinildi: eğitim maçından 1.050,
doğrulamadan 375, sabit kontrolden 450. Aynı üç kaynak maç kullanıldı;
yeni bağımsız maç iddiası yok. Üye CRC/SHA doğrulandı, tam arşiv hash'i
doğrulanmadı. İlk hatalı sıra numarası görüntü erişiminden önce reddedildi.
Doğal ölçekte 212 eğitim / 960 sabit ızgara doğrulama parçası hazırlandı.
Kontrolün 45 tam karesi eğitim parçası yapılmadı. Bu veri kapsamı sonucudur,
algoritma başarı iddiası değildir. `ball-data-expansion-results-v1.json`;
[yöntem](TOP_PARCA_EGITIMI_TR.md).

## V017 — Sabit modelde güven eşiği kalibrasyonu, 8 Kasım 2026

Sekiz ön kayıtlı eşik yalnız doğrulama maçında karşılaştırıldı. Eşik 0,15
doğru eşleşmeleri korudu, fakat eşleşmeyenler doğrulamada 104→177,
sabit kontrolde 95→150 arttı. Kabul koşulu geçilmedi. Kontrolden sonra
eşik değiştirilmedi, model tekrar eğitilmedi. `ball-confidence-results-v1.json`.

## V016 — COCO top başlığını koruyarak eğitim, 8 Kasım 2026

37 numaralı top logiti yeni dense 0'a tüm başlıklarda aktarıldı; diğer
tensörlerin ve kurulan başlangıç modelinin bire bir korunduğu doğrulandı.
Üç epoch düşük öğrenme hızıyla eğitim yapıldı. Sabit 0,3 eşikte doğrulama
eşleşmesi 47→39, eşleşmeyenler 104→43; ayrı maçta 53→39 ve 95→42.
Doğru eşleşmeler azaldığı için kabul edilmedi. Mevcut model korundu.
`ball-transfer-results-v1.json`; [ayrıntı](TOP_COZUNURLUK_AKTARIM_TR.md).

## V015 — Sabit çözünürlük deneyi ve sınıf sözleşmesi, 8 Kasım 2026

120 dış karede aynı GPU/ağırlık/eşik kullanıldı. 384×384 parçalar,
512×768'e karşı üç kaynak maçta eşleşmeleri 17→25, 12→14, 15→15 yaptı.
Her maçta ≥%20 artış koşulu geçilmedi; süre yaklaşık 60→110 saniye.
Varsayılan dedektör değişmedi. Ayrı düzeltmeyle COCO analiz yolu,
tek sınıflı checkpoint'i model kurmadan reddeder; gerçek dosyalarla kontrol
edildi. [Plan ve yöntem](TOP_COZUNURLUK_AKTARIM_TR.md).

## V014 — Dış top dedektörü eğitim altyapısı, 8 Kasım 2026

Manifest-doğrulanmış 225 eğitim / 150 doğrulama görüntüsüyle yerel Nano
tek epoch eğitimi tamamlandı; ayrı 150 kontrol görüntüsü değerlendirilmedi.
İlk eksik bağımlılık ve ardından Windows konsol kodlama hatası çözüldü;
başarısız kayıtlar saklandı. mAP@50:95=0,0103, mAP@50=0,0382: kullanım
kalitesi kanıtlanmadı, final modele alınmadı. 248/249 omurga tensörü
güncellendi; güvenli yeniden yükleme ve sentetik çıkarım geçti. Yeni sınıf
numaraları eski COCO arayüzüne doğrudan uygulanamaz. Özet:
`ball-detector-feasibility-results-v1.json`. 248 test: 246 geçti, 2 atlandı.

## V013 — Top adayı filtresi ve konum hassasiyeti, 8 Kasım 2026

SoccerNet kaynak maçları 4/6/9 ayrımıyla geometri/güven filtresi öğrenildi.
Sabit aday kontrolünde parçalı tarama eşleşmeyenleri 442→224 azalttı,
85→84 doğru eşleşme korundu; normal tarama 134→128 ile %20 azalma
koşulunu geçemedi. Final modele alınmadı. Betimleyici IoU incelemesi
yer/boyut hatası yanında çok sayıda uzak adayı da gösterdi.
Maçlar daha önce erişilmiş dış veridir; Barcelona kullanılmadı.
[Ayrıntı, özetler ve eğitim veri hattı](TOP_ADAYI_DENEYI_TR.md).

## D004 — Top özellikleri olmadan D ve sağlayıcılar arası kontrol, 7 Kasım 2026

Dört eğitim / iki doğrulama maçında 18 aday karşılaştırıldı. Oyuncu hızları
ve yayılımı dışında özellik kullanılmadı. D F1 0,8781 / 0,8577; bir saniyelik
sınır F1 0,3430 / 0,4195. Ön kayıtlı ortalama sınır koşulu karşılanmadı;
aday final sisteme alınmadı. Sabit adayın iki Metrica kısmi olay proxy'sindeki
D F1 değeri 0,8497 / 0,7888; tam maç veya yeni bağımsız test değildir.
Sağlanan maç kullanılmadı, ayrılmış Sportec testi açılmadı. 236 testten
234 geçti, iki isteğe bağlı AV atlandı. [Ayrıntılar](D_OGRENME_DENEYI_TR.md).
Makine tarafından okunabilir terfi kararı: `dead-ball-promotion-decisions.json`.

## D003 — Öğrenilmiş D ve aktarım riski, 7 Kasım 2026

Dört Sportec eğitim ve iki doğrulama maçında 48 aday karşılaştırıldı.
Temiz doğrulama D F1: 0,9948 / 0,9952. Sayısal kabul geçmiş olsa da aday
final sisteme alınmadı: dört eğitim maçındaki ölçülebilir D top hızlarının
tamamı sıfır. Sağlayıcıya özgü sabit koordinat örüntüsünü öğrenmiş olma riski
var. Başarı yarışma/görüntü başarısı diye sunulmadı. Ayrı oyuncu-temelli
deney ve başka sağlayıcı denetimi gerekiyor. [Ayrıntılar](D_OGRENME_DENEYI_TR.md).
231 test: 229 geçti, 2 isteğe bağlı AV atlandı. Temel ve H/A adayı korundu.

## D002 — Sportec/DFL canlı ve duran oyun hedefleri, 7 Kasım 2026

CC BY 4.0 lisanslı dış kaynak, indirme öncesinde 4 eğitim / 2 doğrulama /
1 ayrılmış son kontrol olarak kaydedildi. İlk eğitim maçı J03WOH hazırlandı:
137.214 kare; 65.269 D karesinin tamamında sonlu top koordinatı mevcut.
71.945 canlı oyun karesi var. BallStatus/BallPossession yalnız ayrı hedef
dosyasında; özelliklere verilmez. Bu kapsam sonucu, D model başarısı değildir.
Yeni D sınıflandırıcısı veya birleşik teslim sürümü seçilmedi.

Araçlar: `tools.sportec_download`, `tools.sportec_prepare`,
`development/state_metrics.py`. Ayrılmış test maçına erişim kapalı.
9 yeni testle toplam 225 test: 223 geçti, 2 isteğe bağlı AV atlandı.
Ayrıntılar ve atıf: [Sportec dış veri](SPORTEC_DIS_VERI_TR.md).

## S001 — Dış maçlarda zamansal sahiplik seçimi, 7 Kasım 2026

Plan: `sequence-selection-plan.json`; sonuç: `sequence-external-results.json`.
SkillCorner'ın kayıtlı 12 eğitim / 4 doğrulama maçı kullanıldı. Önceden
erişilmiş dış veridir. 42 adayın ayarları doğrulama öncesinde sabitlendi.
Seçilen adayın ek dört maçtaki tahminleri hedefler puanlanmadan donduruldu.
Bu dört maç daha önce temel model kontrolünde görüldüğünden yeni test değildir.

| Ölçüm | Eski temel | Yeni aday |
| --- | ---: | ---: |
| Doğrulama: X doldurmalı bölüm proxy F1 | 0,360654 | 0,483879 |
| Doğrulama: H/A makro F1 | 0,681228 | 0,791318 |
| Ek kontrol: X doldurmalı bölüm proxy F1 | 0,350802 | 0,465224 |
| Ek kontrol: H/A makro F1 | 0,639107 | 0,736257 |

Her iki grupta da dört maçın tamamında bölüm proxy iyileşti. Bunlar otomatik
sağlayıcı hedefleriyle uyumdur, insan doğruluğu veya yarışma skoru değildir.
Eski X'i bölümlere ayıran proxy de raporda ayrı tutuldu. D ve görüntü başarısı
bu deneyde ölçülmedi; yeni birleşik teslim sürümü seçilmedi.

Seçilen geometri yarıçapı 3,807335 m, göreli hız ölçeği 3,417601 m/s,
azami kanıtsız bağlantı 5,9 s ve geçiş maliyeti 0,25 s. İlk üçü yalnız eğitim
verisinden, sonuncusu ön kayıtlı adaylar arasından dış doğrulamayla seçildi.
Ek dört maç sonucuyla değiştirilmedi. Kaynak/plan/veri hash'leri özel
`sequence-development-20261107` kaydında. Temel model bytes değişmedi.

11 yeni sentetik test; toplam 216 test, 214 geçti, 2 isteğe bağlı AV atlandı.
Dinamik program kaba kuvvet en iyi sonuçla, takım değişim simetrisi, FPS,
uzun kayıp/devre/kare kopması ve hedef sızıntısı reddiyle doğrulandı.

Öncelikli 3 Kasım kural e-postası yeniden okundu: sağlanan çıktı-video
karşılaştırması yasak. Önceki yerel gösterim yaklaşımı düzeltildi,
8776/8777 sunucuları durduruldu. Sağlanan maç bu deneyde kullanılmadı.
[Güncel süreç ve sonraki aşamalar](OTONOM_GELISTIRME_TR.md).

## V012 — Görüntü karar verir, tracking oyuncuyu etiketler, 7 Kasım 2026

`development/visual_possession.py`, `tools/visual_identity_context.py` ve
`tools/visual_possession_experiment.py` ayrı görüntü temelli sahiplik yolu eklendi.
Plan: `visual-possession-plan.json`; kullanım: `GORUNTU_TEMELLI_SAHIPLIK_TR.md`.
Tracking topu/sağlayıcı sahipliği/eski model çıktısı karar girdisi değildir.
Ölçülmüş görüntü topu ve oyuncu ayaklarının sürekliliğinden kontrol adayı çıkar.
Metadata kimliği karşılıklı izdüşüm yakınlığı ve zamansal onayla bağlanır.
Uygun yayındaki kontrol tercih edilir; uyuşmazlık, tekrar, dar kadraj ve toplu
sıçramada taktik karar korunur. Görünmeyen oyuncular taktikten kalır.

17 yeni test, toplam 195 test: 194 geçti, 1 isteğe bağlı AV atlandı.
8 karelik sentetik taktik koşuda X=4/H=4; uygun yayın görüntüsünde top A
oyuncusuna taşındığında X=4/A=4; eşleme geçersiz olduğunda X=4/H=4 oldu.
Kimlik adaptörü sayısal olmayan ATD top alanıyla da çalıştı; top ayrıştırılmadı.
Önceden görülen dış eğitim kesitlerinin 1.200 çıktı karesi kimlik kanıtı yokken
X kaldı. Bu gerçek sahiplik doğruluğu veya performans artışı değildir.

Özel ön kayıt ve rapor:
`C:/Users/Abra/FootballPrivate/visual-possession-development-20261107`.
Donmuş kaynaklar korundu. Yarışma görüntüsü/tracking'iyle geliştirme yapılmadı;
o maç için yeni tam çıktı üretilmedi. Kimlik/zaman/kalibrasyon ve gerçek görüntü
başarısı dış maçlarda doğrulanmadan yeni teslim sürümü seçilmedi.
İlk kural uçuşta pas sahipliği veya D çözmez; tag destekli görüntü sınırları
sonraki ayrı aşamadır. Eski tracking tabanlı hareket prototipi sessizce yeni
görüntü kararının yerine kullanılmadı.

## V011 — Tracking destekli top adayı, 7 Kasım 2026

Mevcut dedektör ve zamansal takip değiştirilmeden ayrı ilişkilendirme katmanı
eklendi. Sabit sentetik plan: `ball-support-plan.json`; uygulama ve sınırlar:
`TRACKING_DESTEKLI_TOP_TR.md`. Doğrulanmış kaynak/kare/saat/epoch, canlılık,
kalibrasyon ve zemin kanıtı ister; onaylı mevcut ölçümleri karşılaştırır.
Tahmin, hava topu, tekrar, uyuşmazlık ve yakın iki adayda seçim yapmaz.
İkinci kamera ayrı native kontroller ve tam çift eşlemesiyle destek verebilir.
Ortak tracking uyumu bağımsız gerçek kabul edilmez. Sahiplik güncellenmez.

12 yeni birim/entegrasyon testi geçti. Tüm paket: 178 test, 177 geçti,
1 isteğe bağlı AV atlaması. Sekiz önceden görülen dış eğitim kesitinde iki
mod/1.200 çıktı karesi işlendi; önceki paketlerin tüm eski alanları korundu.
Eşzamanlı bağımsız otomatik tracking bulunmadığından destek gerçek kesitlerde
etkinleşmedi; destek açık ve çift kamera yolu sentetik olarak sınandı.
Gerçek doğruluk artışı veya bağımsız test sonucu üretilmedi. Referans etiketler
girdi yapılmadı; yarışma maçı okunmadı; donmuş kaynaklar bütünlük testini geçti.

Özel ön kayıt ve rapor:
`C:/Users/Abra/FootballPrivate/ball-support-development-20261107`.
Seçilen yeni teslim sürümü yok. Gerçek eşzamanlı dış kaynakta açık/kapalı
karşılaştırması bekliyor. Sonraki görüntü+D aşaması: otomatik tag civarında
durma/başlama adaylarını ayrı belirsizlik aralıklarıyla çıkarıp dış D/canlı
oyun hedeflerinde doğrulamak; tüm tag aralığını veya top kaybını D yapmamak.

## V010 — Ayak bağlamı denemesi: kabul edilmedi, 7 Kasım 2026

Kullanıcının ayak/top karışması gözlemine karşı, yalnız otomatik kişi kutuları
ve hareketi kullanan isteğe bağlı `ball_foot_context` prototipi denendi.
Yakınlık tek başına eleme değildir: alt gövdede yüksek örtüşme, uzamış kutu ve
dört bağlı hareket gözlemi gerekir. Önceden iki bağımsız gözlem taşıyan top
izi korunur. Parametreler ve kabul koşulları `ball-foot-context-plan.json`
ile denemeden önce kaydedildi; kaynak maç 4 geliştirme, 6/9 daha önce görülmüş
tekrar doğrulama olarak belirtildi. Dokunulmamış test iddiası yoktur.

Sekiz eğitim kesitinin iki modunda mevcut V009 ile aynı sonuçlar alındı;
katman hiçbir adayı yeterli kanıtla elemedi. Eşleşmeyen kutular azalmadığı için
kabul koşulu geçilmedi, varsayılan akışa veya 8774 galerisine açılmadı. V1
kontrol koşusunun kare çıktısı önceki V009 dosyasıyla byte düzeyinde aynıydı.
Kullanıcı daha sonra ilk gözlemin net olmadığını, aday/tespit/tahmin gösterimini
karıştırmış olabileceğini açıkladı. Ayak hatası düzeltilmiş gibi sunulmadı;
gerekçesiz yeni sınıflandırıcı eğitilmedi. İsteğe bağlı kod yalnız deney olarak
kalır. 166 testlik paket bir isteğe bağlı AV atlamasıyla başarılı.

Kayıt: `C:/Users/Abra/FootballPrivate/foot-context-development-20261107`:
`before-run.json`, `association-audit-v1`, `acceptance.json`, `control-v1`.
Barcelona verisi kullanılmadı, donmuş temel değişmedi. Kaynak/etiket/başarı
ayrımı ve lisans durumu kullanıcıya ayrıca açıklandı.

## V009 — Dış kesitlerde zamansal top adayı takibi, 7 Kasım 2026

`ball-tracking-plan.json` sayısal mühendislik ayarları dış koşudan önce
kaydedildi. Konum/hız öngörüsü, kutu boyutu ve tespit güveniyle çoklu aday
ilişkilendirmesi uygulandı. Çift kutular ilişkilendirmede bastırılır, ham
veride korunur. Üç gözlemle onay, en fazla 0,2 s kısa öngörü; belirsizlik,
kesme/boyut/saat kopması ve sürede kimlik kapanışı vardır. Ölçüm ve tahmin
ayrı alanlardadır; tahmine dedektör ölçümü/kimliği yazılmaz.

Kaynak yalnız önceki SoccerNet eğitim galerisidir: üç görülmüş maçtan sekiz
kesit, iki modda 1.200 çıktı karesi ve önceki kısa örnekte 50 ek çıktı.
Barcelona verisi/görüntüsü kullanılmadı; dedektör ayarları veya donmuş sahiplik
modeli değişmedi. 161 testlik paket bir AV atlamasıyla başarılı; dokuz API
görünümünün takip alanları ve ölçüm/tahmin ayrımı kontrol edildi.

Tahminler dondurulduktan sonra eğitim referanslarıyla betimleyici ilişki
incelemesi yapıldı. SAHI 248/525 referans kutusuyla eşleşen ilişkili ölçüm
üretti, bunların 229'u onaylı izdeydi; 830 ölçüm eşleşmedi. Referans bulunan
216 öngörü gözleminin 27 merkezi referans kutusu içindeydi. Etiket kapsamı
olmayan anlar negatif sayılmadı. Kimlik değişimi sayısı yalnız ardışık
eşleşmiş referanslar arasındadır; düşük kapsamda sıfır olması kusursuzluk
kanıtı değildir. Başarı iddiası/model seçimi yapılmadı. Yanlış aday ve iz
kopmaları sürer; oyundaki top seçimi veya sahiplik girdisi üretilmez.

Kayıt: `C:/Users/Abra/FootballPrivate/temporal-ball-development-20261107`.
Galeri `http://127.0.0.1:8774/`; tahmin pembe kesikli, tespit düz, aday sarıdır.
Rehber: [zamansal top takibi](ZAMANSAL_TOP_TAKIBI_TR.md).
Sağlayıcı temizliği bekleyenleri sürer; bu bir teslim sürümü seçimi değildir.


## V008 — Aynı-kaynak saat ve tracking izdüşümü incelemesi, 7 Kasım 2026

Kullanıcının tracking/video kare saatini kontrol edip saha noktalarını görüntüye
taşıma isteği salt okunur yerel katmanla uygulandı. Kod matematiği/oynatma
kontrolleri yalnız sentetik kaynakta sınandı. Sağlanan maçta video görüntüsü
çözmeden MP4 paket PTS'leri, dosya bağları ve ATD/H kare şeması incelendi.

Taktik 199.319/199.319, yayın 164.487/164.488 video/tracking sayıları ve 25 FPS
ızgarası yapısal olarak uyumludur. Yayındaki son fazla tracking kaydı görüntüye
bağlanmaz. Bu, bağımsız görüntü hizası veya homografi doğruluğu doğrulaması
değildir; kayıtlarda bu alanlar false kalır. Offset arama/ayar/model seçimi yoktur.

`tracking_viewer` aynı karenin ham normalize kişi noktalarını H ile piksele
taşır. `tracking-projection.js` sunulan video karesiyle ATD/H kimliklerini
karşılaştırır; stale/missing/geçersiz veride işaret çizmez. Aspect ratio/DPR
dönüşümü korunur. Top, kutu ilişkisi, oyuncu kimliği ve sahiplik üretilmez.
Gerçek video yalnız kullanıcıya localhost üzerinden açılır, asistanla paylaşılmaz.

151 testlik paket 1 AV atlamasıyla başarılı; iki gerçek kaynağın API kare
sözleşmesi denetlendi. 50 karelik sentetik videoda oynatma ve geri adımda
görüntü/ATD/H aynı kaldı. Donmuş temel hash'i değişmedi; sağlayıcı temizliği
bekleyenleri sürer. Kayıt: `C:/Users/Abra/FootballPrivate/native-projection-review-20261107`.
Rehber: [izdüşüm incelemesi](IZDUSUM_INCELEME_TR.md).


## V007 — Proje görüntü ölçüm girişi ve bağlı inceleme, 7 Kasım 2026

`tools.match_analysis` kayıtlı video/config veya tamamlanmış dedektör koşusunu
`ImageAnalysis` ölçüm sözleşmesine bağlar. Kaynak/zaman, kişi/top adayları,
kutular, piksel konum/hızı ve kaynakla adlandırılmış izler korunur. Rol/takım/
oyuncu kimliği bilinmiyor, bütün top adayları seçilmemiş olarak kalır.
Referans alanları ve kanıtlanmamış rol iddiaları reddedilir; piksel/saha
koordinatları ayrıdır. Bu V1 sahiplik veya hibrit ölçüm kabulü üretmez.

Önceden görülen üç kaynak maçtaki sekiz eğitim kesitinin iki dedektör koşusu
aynı ayarlarla aktarıldı: 16×75 = 1.200 çıktı karesi, 600 farklı kaynak karesi.
Önceki kısa örnek ayrıca 2×25 çıktı verir. Yeni eğitim/ayar/model seçimi yoktur.
`image-integration-plan.json`, özel önce-kayıt ve kaynak/gözlem/çıktı hash'leri
izlenebilirliği sağlar. `vision_review --project-analysis` dokuz seçeneğin
tamamında bu proje çıktılarını okur; yeşil referans paneli modelden ayrıdır.

147 testlik paket bir isteğe bağlı AV atlamasıyla başarılı; JS sözdizimi,
dokuz bağlı API görünümü ve donmuş temel hash'i kontrol edildi. Görüntüden
rol/takım veya sahiplik başarısı ölçülmedi. Geliştirme girdisi yalnız izinli
dış/sentetik veri; sağlayıcı temizliği bekleyenleri korunur.

Özel kayıt: `C:/Users/Abra/FootballPrivate/project-image-integration-20261107`:
`before-integration.json`, `report.json`, `viewer-verification.json` ve
kesit/yöntem bazında `registration.json`, `frames.jsonl`, `summary.json`.
Rehber: [görüntü entegrasyonu](GORUNTU_ENTEGRASYONU_TR.md).


## V006 — Sekiz kesitli görsel inceleme galerisi, 7 Kasım 2026

Kullanıcının daha çok kesiti aynı arayüzde inceleme isteği için
`soccernet-gallery-plan.json` içerik görülmeden kaydedildi. Eğitim arşivinin
sıralı 0,8,16,24,32,40,48,56 indekslerinden SNGS-060/068/076/103/111/154/162/170
seçildi. Başlangıç kareleri 0,75,150,225,300,375,450,525; her kesit 75 kare,
25 FPS, 3 saniye. Metadata kaynak maç kimlikleri 4,6,9: sekiz ayrı maç
iddiası yoktur. Bu maçlar artık dokunulmamış test diye sunulamaz.

Kamuya açık, sabit HF commit'indeki eğitim ZIP'inden seçilmiş üyeler alındı.
Arşivde kareler karışık sırada olduğundan büyük blok önbellek denemesi
durduruldu; küçük HTTP aralıklarıyla paralel edinme tamamlandı. Başlık adı,
sıkıştırma türü, boyut ve ZIP CRC denetlendi; yerel SHA-256'lar kaydedildi.
Doğrulanmış başarılı aralıklar toplamı 193.609.622 byte; bu tam arşiv SHA
doğrulaması veya başarısız istekleri içeren ağ trafiği toplamı değildir.

Mevcut Nano/SAHI/ByteTrack ayarları değişmedi. Her iki yöntem aynı 600 kareyi
ayrı işledi; kaynak JPEG–FFV1 RGB eşitliği, 75'er karelik tahmin sırası ve
PTS, kaynak video bağı, aynı ağırlık/ayarlar, dondurulmuş temel hash'i ve
kutulu MP4'lerin 75'er kare çözülmesi denetlendi. Referans etiketleri
dedektöre verilmedi. Model seçimi veya yeni doğruluk ölçümü yapılmadı.

Oturum kesintisinde son kesitin normal koşusu 67 karede yarım kaldı.
`native-interrupted-20261107` altında ayrı korundu; son kesit yeniden
başlatılıp iki yöntemde de 75/75 tamamlandı. Tamamlanan yedi kesit yeniden
hesaplanmadı. Eski süreç kaydı ve edinme kaynak snapshot'ı ayrı saklandı.

Galeri `http://127.0.0.1:8770/`: sekiz kesit ve önceki bir saniyelik örnekle
dokuz seçenek. Seçici, önceki/sonraki kesit, döngü, peş peşe oynatma, dört
senkron görünüm, yavaşlatma ve yakınlaştırma var. Peş peşe geçiş tarayıcıda
doğrulandı; sekiz kesitin API, ilk/son JPEG ve kare eşleştirmeleri denetlendi.
141 testlik paket 1 isteğe bağlı AV atlamasıyla başarılı; JS sözdizimi de
kontrol edildi. Gerçek video dönüşümlerinin tamamı RGB hash denetiminden geçti.

Özel kayıt: `C:/Users/Abra/FootballPrivate/soccernet-gallery-20261107-v2`.
`acquisition.json`, `range-receipts.json`, `process-registration.json`,
`exposure-register.json`, `gallery.json`, `gallery-verification.json` ve
kesitlerin kaynak/tahmin/önizleme klasörleri. Ham veri Git deposu dışındadır.
Hibrit kabul koşulları ve dondurulmuş sahiplik modeli korunur; sağlanan yarışma
maçı bu geliştirmeye alınmadı. Sağlayıcı temizliği bekleyenleri sürer.


## V005 — SoccerNet profesyonel yayın eğitim örneği, 7 Kasım 2026

SoccerNet GSR 2024 kamuya açık eğitim arşivi, sabit HF commit'i
`3cc710eb6d53a23350a3d2863311c1c0a2e645d7` ile kaydedildi. İlk alfabetik
kesit SNGS-060'ın ilk 25 karesi ve referansı seçildi; görüntü başarı durumuna
göre seçilmedi. Test/valid/challenge içeriği okunmadı; game_id=4 aynı maça
ait kliplerin ileride ayrı doğrulama maçları sayılmasını önlemek için kayıtlı.
Araştırma kullanım koşulları korunur; ham veri/ağırlık yeniden dağıtılmaz.
İlk indirme zaman aşımında eksik kaldı; yeni edinme kaydı tamamlandı.

25 kaynak JPEG kayıpsız RGB video doğrulamasından geçti. Referans v1.3,
25 FPS ve kaynak boyutları eşleşti. Önceki Nano ve SAHI sayısal ayarları
değiştirilmeden iki koşu tamamlandı. Etiket/rol/takım/saha koordinatı girdi
yapılmadı; tahmin hash'leri kutu karşılaştırmasından önce kaydedildi.
IoU ≥0,5 bire bir karşılaştırmada normal yöntem kişi 409/425, top 0/25;
SAHI kişi 416/425, top 19/25 eşleşme verdi. SAHI'de ayrıca 175 kişi ve
11 top tahmini eşleşmedi; normal yöntemde 24 kişi eşleşmedi. Top ölçümü
şema denetimi sonrası keşifseldir; sonuçlar resmî metrik veya genel başarı
oranı değildir. Saha/kimlik/takım/sahiplik doğruluğu değerlendirilmedi.

Yeni model seçilmedi. Donmuş temel kaynaklar ve hibrit kabul koşulları
korundu; `hybrid_ready=false`. Sağlanan yarışma görüntüsü veya public skor
bu geliştirmede kullanılmadı. Sağlayıcı temizliği bekleyenleri sürer.
Ayrıntılar ve takip aşamaları: [SoccerNet planı](SOCCERNET_ASAMALARI_TR.md).


## V004 — Görüntü konumu, iz sürekliliği ve yerel kutulu video, 6 Kasım 2026

Mevcut RF-DETR/SAHI/ByteTrack prototipi doğrudan görüntü ölçümü üretecek
şekilde genişletildi. `vision_measurements.py`, kişi kutusu/ayak noktası ve
top merkezi adaylarını, kamera epoch'una bağlı kişi izlerini, piksel hızını
ve isteğe bağlı aynı-kaynak homografisinde saha metre adayını saklar.
Sahipsiz/çift iz kimliği, kayıp kare, kaybolma, kesme/boyut değişimi ve
kırpılmış ayak noktası bilinmeyen kalır. Kameranın değişmesi tekrar veya
canlılık sınıfı sayılmaz; epoch değişiminde gerçek ByteTrack sıfırlanabilir.

Kişi sınıfı futbolcu/takım değildir. Bütün top adayları korunur; havadaki
topun görüntü merkezi zemin/yükseklik ölçümüne dönüştürülmez. Matematiksel
homografi ve tespit güveni bağımsız kalibrasyon doğrulaması sayılmadı.
`frame_kind=unknown`, `calibration_validated=false`, `hybrid_ready=false`.
Mevcut hibrit güven koşulları ve donmuş H/A/X modeli değiştirilmedi.

Veri: önceden kayıtlı SoccerTrack 117092 eğitim klibinin ilk 125 karesi
mevcut kayıtlı byte-range önbelleğinden, yeni ağ isteği olmadan alındı.
Kayıpsız RGB hash'leri ve önceki ilk 10 kare eşleşmesi doğrulandı. Kaynak
klibin tamamı ve referansın tamamı alınmış/doğrulanmış sayılmaz; Drive
alternatifinin HF sürümüyle aynı içerik olduğu varsayılmadı. Önceden
görülmüş eğitim örneği yeni held-out test değildir.

Sayısal dedektör/dilimleme ayarları önceki prototipten değişmedi. Görüntü
değişimi ayarları sentetik mühendislik değerleridir. Kod ve iki çalışma
ayar hash'i işlemden önce kaydedildi. Native 125 karede 783 kişi gözlemi,
0 top adayı; SAHI ilk 25 karede 1.418 kişi gözlemi ve 3 karede toplam
3 top adayı üretti. Bunlar tekil/doğru kişi sayısı veya oyundaki doğru top
kanıtı değildir. Ayrı saha/rol/takım ve top adayı ilişkilendirmesi gerekir.
Gerçek dış klibe homografi verilmedi; saha koordinatı uydurulmadı.

Yerel CPU koşuları model yükü dahil yaklaşık 79/196 saniyede tamamlandı;
eşzamanlı küçük örnekler olduğundan temsil edici hız veya gerçek zamanlı
başarı iddiası yapılmadı. Kutulu MP4/JPG önizlemeleri kaydedildi, çıktı
kare sayıları çözülerek kontrol edildi. İzlemeyi kolaylaştıran 5 kat
yavaş gösterim yalnız sunum zamanını değiştirir. Görsel etiket yerleşimi
model kutularını veya ölçüm verisini değiştirmeden sadeleştirildi.
Görsel inceleme yalnız izinli dış SoccerTrack örneğinde yapıldı.

**126 test geçti.** Yeni testler piksel/saha aday hızını, kaynak kareyle
matris seçimini, kamera resetini, kayıp/çift izi, kesik ayak noktasını,
top yüksekliği belirsizliğini, kaynak homografisi provenansını, eksik
işlem aralığını ve sağlanan maçın önizlemeye kabul edilmemesini kapsar.
Normal ortam numpy 1.26.4 kaldı; mevcut ayrı görüntü ortamı kullanıldı.
Yeni ağırlık indirilmedi; resmî Nano SHA-256 aynı kaldı. Önceki görüntü
kaynakları ve yeni koşu kaynakları hash/snapshot ile ayrı korundu.

Özel kayıt: `C:/Users/Abra/FootballPrivate/vision-module-development-20261106`.
`sample-manifest.json`, `measurement-freeze.json`, `native-v2`, `sliced-v2`,
`native-preview-v3`, `sliced-preview-v3`, test kaydı ve `stage4-report.json`.
Sağlanan maç görüntüsü/etiketi/public skoru bu geliştirmeye alınmadı;
uzak görüntü çıkarımı veya yeni sağlanan-maç görüntü paylaşımı yapılmadı.
Futbol doğruluğu/parametre seçimi için referans sözleşmesi ve bağımsız
dış doğrulama hâlâ bekliyor. Rehber: [görüntü modülü](GORUNTU_ISLEME_TR.md).
Önceki sağlayıcı/sohbet temizliği bekleyenleri tamamlanmış sayılmaz.

## H003 — Taktik öncelikli hibrit ölçüm ve kaynak geçiş koruması, 6 Kasım 2026

Kullanıcı politikası deneysel ölçüm katmanına uygulandı: yeterli ve doğrulanmış
zaman/görünürlük/kalibrasyon/oyuncu uyumu varsa görünür yayın ölçümleri tercih
edilir; geri kalanı taktik kaynaktan korunur. Dar/iki oyunculu kadraj, tekrar,
boş/bilinmeyen görüntü, kaynak çelişkisi ve toplu aşırı hızda yayın kapatılır.
İlişki belirsizliği tekil oyuncuda taktik ölçümü korur. Kısa kayıpta yalnız
taze otomatik ilişki ve mevcut yayın ölçümü kullanılabilir; konum üretilmez.
Top görünürlüğü, hareketi ve zemin dönüşümü ayrı korunur.

`development/hybrid_tracking.py` ve `hybrid_pipeline.py` mevcut hareket
akışına bağlandı. `continuity.py`, kaynak geçişi/kare atlamasını kesen
oyuncu/top çift maskelerini sağlar. Hız, dripling, erişim, temas/pas, takım
hareketi, uzun top ve duran top katmanları bu süreklilikten yararlanır.
Kaynak geçişi temas veya pas diye yorumlanmaz; bilinmeyen görüntü D yapılmaz.
Her oyuncu/top için kaynak, kaynak karesi/yuvası ve karar nedeni saklanır.
Ham girdiler değiştirilmez; oyuncu noktaları ortalanmaz.

Ayarlar: `hybrid-data-plan.json`, yalnız sentetik mühendislik değerleri.
Yeni model/teslim sürümü veya futbol doğruluğu seçilmedi. Donmuş `model.json`
ve sekiz `clean_model` kaynağı korundu; ana numpy 1.26.4 ortamı değişmedi.
Yeni üçüncü taraf kod/model paketi veya servis eklenmedi.

Kontrol: **119 test geçti**. Sentetik durumlar görünür/görünmez alt kümeyi,
permüte yuvaları, iki oyuncu/boş/tekrar/bilinmeyen görünümü, toplu/tekil
sıçramayı, yanlış devre/FPS/eşlemeyi, kalibrasyon kaybını, kısa kimlik bağını,
topun eksik/çelişkili/havada-belirsiz durumunu ve kaynak geçişinde yapay
hız/temas/pas oluşturmamayı kapsar. İnceleme dosyası/API'sinin mevcut
`usable_for_possession=false` işareti nihai kullanım için terfi ettirilmez.

Dış çalışma: sabit Metrica commit'i ve mevcut hazırlanmış dosya hash'leri
doğrulandı. Sample 1 train, Sample 2 validation ayrımı korundu; her maçın
ilk 1.500 karesinde yedi kontrollü senaryo koşuldu. Son koşu 14 koşul/21.000
senaryo karesidir. İki oyuncu, tekrar, geometri çelişkisi, inceleme eşlemesi
ve bilinmeyen görünürlük koşullarında yayın katkısı sıfır kaldı. Pozitif alt
kümede uygun yayın noktaları tercih edildi; toplu sıçrama bölümleri reddedildi.
İlk koşunun kaynakları snapshot ile korundu; yalnız mevcut inceleme JSON/API
biçimini açıkça reddetme uyumluluğu eklendikten sonra ikinci koşu tekrarlandı.
Sayısal ayarlar değiştirilmedi.

İkinci görünüm gerçek bağımsız kamera değildir; aynı dış tracking'in kontrollü
ölçüm/maske değişimidir. Görünürlük/canlılık/zemin bayrakları sentetiktir.
Bu, gerçek çift kamera veya görüntü sınıflandırma doğruluğu ve daha iyi
sahiplik skoru iddiası değildir. Önceden kullanılan dış maçlar yeni held-out
test diye sunulmadı; gerçek kamera doğrulaması hâlâ gerekir.

Kural kontrolü için resmî FAQ erişimi, genel kuralların yanında sağlanan maça
özgü örnek/sınır açıklamaları da döndürdü. Bu tesadüfi erişim özel kayda
yazıldı; içerik özellik, eşik, etiket, eşleme veya değerlendirme girdisi
yapılmadı. Bu geliştirmede sağlanan maçın görüntü/tracking çıktıları okunarak
ayar yapılmadı; yeni görsel paylaşım yapılmadı. Mevcut aday eşlemeler veya
salt sonlu ATD noktaları bağımsız görsel görünürlük yerine kullanılmadı.

Özel kayıt: `C:/Users/Abra/FootballPrivate/hybrid-development-20261106`.
`controlled-v1` ve `controlled-v2` kaynak kayıtları, dış girdilerden türetilen
ölçüm/provenans dizileri ve senaryo özetlerini; `stage3-report.json` birleşik
durumu içerir. Gerçek görünürlük, kadraj/tekrar ve ölçüm güveni girdilerini
üretecek görüntü prosedürü sonraki adımdır. Yarışma maçında yayın düzeltmesi
bu aşamada açılmadı. Rehber: [hibrit politika](HIBRIT_KAYNAK_POLITIKASI_TR.md).
Önceki sağlayıcı/sohbet temizliği bekleyenleri değişmedi.

## S002 — Yerel saat OCR'ı, geometri desteği ve çift kamera incelemesi, 6 Kasım 2026

Amaç salt okunur otomatik zaman eşleme prototipidir. Hibrit sahiplik modeli
veya yeni teslim sürümü seçilmedi. `model.json` ve donmuş kaynaklar korundu.

Ayar kaynağı: `sync-review-plan.json`, yalnız sentetik mühendislik değerleri.
Sağlanan videoların ilk kare çözümünden önce OCR/ayrıştırıcı/geometri kodu ve
ayar hash'leri özel kayıtta donduruldu. Daha sonra yalnız video/ATD son kare
sözleşmesi ve ters zaman bağlantılarını reddetme gibi adaptör korumaları
eklenip geometri çalıştırmasından önce ayrıca kaydedildi. OCR, saat/geometri
algoritmaları ve sayısal ayarlar sağlanan sonuçlardan sonra değiştirilmedi.

Ortam: ayrı Python 3.10 CPU ortamında RapidOCR ONNX Runtime 1.4.4,
ONNX Runtime 1.23.2, av 16.0.1. Paket sürümleri `requirements-sync-lock.txt`,
paket içi OCR model SHA-256'ları ve kaynak/lisans bilgileri özel kayıtta.
Ana numpy 1.26.4 ortamı değiştirilmedi. Kareler/kırpmalar yalnız yerel OCR
belleğinde işlendi; görüntü kaydedilmedi veya asistan/uzak servise gönderilmedi.

Kontrol: 107 Python testi geçti. Normal/uzatma saatleri beş yapay görüntüde
okundu. Bilinen 3 saniye farkı ve tekrar aralığı olan iki yapay videoda
eşlenen bağlantıların farkı doğru bulundu, tekrar içi boş bırakıldı.
Sentetik TXT/XML/homografiyle uçtan uca koşucu, farklı takım sırası ve fazla
bir ATD kaydı sınandı. Sentetik geometri örneğinde slot permütasyonu ve
25/20 FPS desteklendi; statik/belirsiz zaman adayı doğrulanmadı.
Tarayıcıda çift oynatma, kare adımı/girişi, aralık seçimi ve boşlukta yayın
duraklatma/gizleme çalıştı. Ekran görüntüsü yalnız sentetik kayıttan alındı.

Sağlanan videolara uygulama: ilk kez yeni otomatik salt okunur saat okuması
yapıldı; önceki etiket/görüntü/türev veya public skorlar okunmadı. Taktikte
1.329 örnekten 1.008, yayında 1.097 örnekten 1.009 güven eşiğini geçen saat
okuması çıktı. Bunlar doğru okuma sayısı veya OCR doğruluğu ölçümü değildir.
846 benzersiz saat adayı incelendi: 494 geometrik destek, 81 belirsiz tepe,
268 yetersiz geometri ve 3 kaynak uyuşmazlığı. Derlenen 817 bağlantı toplam
4.968 saniye/82,8 dakika ve 21 kesintisiz aday aralık içeriyor. 388 bağlantı
geometri destekli, 429 yalnız saat adayı. Bu sayılar kapsam/gözlem bilgisidir;
bağımsız kare doğruluğu veya canlı yayın garantisi değildir. Seyrek örnekler
arasındaki kısa tekrarlar ayrıca doğrulanmalıdır.

Tüm bağlantılarda `usable_for_possession=false`. Oyuncu kimlikleri veya ham
tracking kaynakları birleştirilmedi, top/oyuncu görüntü modeli bu maçta
çalıştırılmadı, sahiplik çıkarımı değiştirilmedi. Kaynak çelişkisi, geçersiz
homografi ve eşleme boşluğu belirsiz kaldı. Eşleme doğrulaması başka maçlarda
tamamlanmadan bu adaylar teslim modelinin birleşim katmanı sayılmaz.

Özel kayıt: `C:/Users/Abra/FootballPrivate/video-sync-development-20261106`.
`stage2-freeze.json`, `alignment-freeze.json`, iki OCR kayıt/çıktı dizini,
`alignment-v1`, sentetik koşular ve kaynak bütünlüğü kayıtları burada.
Güncel izleyici girdisi `C:/Users/Abra/FootballPrivate/video-sync/alignment.json`.
Başlatıcı `ESLESME-IZLE.cmd`; rehber [ESLESTIRME_TR.md](ESLESTIRME_TR.md).
Önceki sağlayıcı/sohbet temizliği bekleyenleri bu işlemle tamamlanmış sayılmaz.

## I001 — Yayın dosyaları ve salt okunur izleyici entegrasyonu, 6 Kasım 2026

Resmî Drive yayın klasöründeki TXT, XML ve homografi CSV yeniden indirildi;
SHA-256 değerleri mevcut yerel veri paketiyle birebir eşleşti. Yeni MP4
İndirilenler'den bağlandı, kaynak deposuna taşınmadı. Dosya kimlikleri/hash'leri,
video metadata'sı ve son paket kontrolü özel edinme kaydında tutuldu:
`C:/Users/Abra/FootballPrivate/broadcast-acquisition-20261106`.

Yayın başlatıcısı kendi zaman çizgisindeki ATD/XML/CSV/video ile çalışır;
taktik olayları bu saate bağlamaz. Homografi adaptörü normalize saha → piksel
yönünü, kare numaralarını ve sağlayıcı geçerliliğini korur. Tekil/eksik matris
ve eksik nokta için dönüşüm üretilmez. Ters dönüşüm metre ölçeğini açıkça ister.
Video/tracking sonundaki bir kayıt farkı eşleme sınırıyla ele alındı; ham ATD
silinmedi. Matris geçerliliği tespit/temas doğruluğu olarak değerlendirilmedi.

95 Python testi geçti. Sentetik videoda geçerli/geçersiz matris, piksel konumu,
kare adımı ve video ortak sınırı tarayıcıda kontrol edildi. Gerçek maçın
görüntü kareleri çözülmedi; metadata, dosya bütünlüğü ve yerel servis bağlantısı
kontrol edildi. Bu veri/arayüz entegrasyonudur; yeni model, eşik veya sürüm
seçilmedi. Donmuş `model.json` ve sekiz kaynak dosyası korundu. İki kameranın
otomatik eşlenmesi ve modelde birleştirilmesi henüz tamamlanmadı.

## V001 — Erişim süresi entegrasyonu ve yerel görüntü çalışma kontrolü, 5 Kasım 2026

Dal: `feature/reachability-vision`. Yeni model/teslim seçilmedi. Donmuş H/A/X
çıkarımı, `model.json` ve sekiz kaynak dosyasının hash'leri korundu.

Uygulama: simetrik konum/hız tabanlı erişim süresi, mevcut top hareketi temas
adaylarında mesafe belirsizliğine ek destek olarak bağlandı. Tek başına sahiplik
veya D üretmez; uçuşta yakınlık engelini kaldırmaz. Olay/sahiplik hedefi girdi
olmaz. Kayıp hız, devre ve sıçramalar gözlem bağı üzerinden ele alındı.

Dış veri/split: daha önce kayıtlı Metrica Sample 1 train, Sample 2 validation;
bu çalışmada toplam 286.162 karede uçtan uca kontrol yapıldı. Bütün sayısal
ayarlar sentetik test değerleridir; parametre taraması/seçimi ve doğruluk
değerlendirmesi yapılmadı. Erişim süresi her maçta 5 belirsiz temas adayını
ayırdı. Bu sayı doğrulanmış temas veya sahiplik başarısı değildir. Otomatik
tag/D/LONG BALL katmanları bu veri çalıştırmasında etkin değildi.

Görüntü: ayrı Windows/Python 3.10 CPU ortamı; RF-DETR 1.11.2 Nano, SAHI 0.14.0,
Supervision 0.29.0 ByteTrack. Ana ortam numpy 1.26.4 kaldı. 66 paket sürümü
`requirements-vision-lock.txt` içinde kayıtlı. `pip check` geçti. Resmî Nano
ağırlığının MD5'i yayımlanan varlıkla eşleşti; SHA-256:
`d8d6b9ee57d4d0ed2b1f305163624712a0532cb7bce0c747317984fc5457440d`.
Ek model ağırlığı veya bulut çıkarım servisi kullanılmadan çalışma kontrolü yapıldı.

Önce geometrik yapay videoda native 2, dilimli 1 kare ve yapay kutu dizisinde
iz sürekliliği çalıştı. Sonra CC BY 4.0 SoccerTrack 117092 eğitim klibinin
önceden seçilen ilk 10 karesi HTTP byte aralıklarıyla edinilip kayıpsız RGB
örneğe dönüştürüldü; karelerin RGB SHA-256 değerleri kaynak çözümüyle eşleşti.
Bu gerçek dış örnekte native 10 ve SAHI 2 kare işlendi. Sonuçlar gözlemdir;
takım/sahiplik etiketi veya bağımsız doğruluk skoru değildir.

Veri erişimi: kaynak/maç ayrımı/dosya kimlikleri içerikten önce
`vision-data-plan.json` ve özel ön kayıtla kaydedildi. İlk referans şema
örneğinde 0 tabanlı kare/-1 bayraklar, güncel belgelenen GT sözleşmesiyle
uyuşmadı. Tam referans ve klip indirmesi sırasında sağlayıcı indirme kotası
yanıtı verdi; devam isteği yapılmadı. Başarı değerlendirmesi onaylanmadı.
Olay noktalarından yeniden kurulan yardımcı top izi de bağımsız top gerçeği
veya kendi olaylarına karşı temas değerlendirme girdisi sayılmadı.

Senkronizasyon: otomatik saat gözlemlerinden yalnız aday aralık üreten modül
eklendi; tekrar/donmuş/kopuk saatleri çözülmüş saymaz ve hiçbir saat adayını
sahiplik birleştirmesi için hazır işaretlemez. OCR/geometriyle son eşleme ve
iki kamera birleştirmesi henüz tamamlanmadı. Yayın MP4 yolu bulunamadı;
bilinen yerel pakette yayın ATD/homografi dosyaları mevcut.

Kontrol: **91 test geçti**. Bunlar yön, takım/koordinat simetrisi, 10/25 FPS,
kayıp/sıçrama, uzun top etkileşimi, referans sözleşmesi, zaman damgası,
hash/provenans ve donmuş kaynak bütünlüğünü kapsar. Sağlanan yarışma maçı
görüntüleri/etiketleri veya public skorları seçim için kullanılmadı.

Özel kayıt kökü:
`C:/Users/Abra/FootballPrivate/vision-development-20261105`.
`stage1-report.json` güncel kaynak hash'leri, çalışma kontrolü sonuçları ve
bekleyenleri; `motion-smoke-output-v2` kayıtlı dış tracking çalıştırmasını;
`runtime-smoke-v1`, `real-native-v1`, `real-sliced-v1` görüntü kontrollerini;
`soccertrack-mot-train/sample-manifest.json` kayıpsız örnek edinimini içerir.
Tam plan: [UYGULAMA_PLANI_TR.md](UYGULAMA_PLANI_TR.md).

Sağlayıcı/sohbet temizliğiyle ilgili önceki bekleyen durum değişmedi. Bu kayıt
organizatör şartlarının tümünün tamamlandığı iddiası değildir.

## L001 — LONG BALL aralığında hareket ve yakınlık engeli, 4 Kasım 2026

Kullanıcı isteğiyle otomatik LONG BALL aralıklarında kesintisiz hızlı ve
uzun yer değiştiren top hareketi aranır. Net mesafe, süre ve yol tutarlılığı
ölçülür; eksik noktalar, yön dönüşleri, devre ve sıçramalar diziyi keser.
D/dripling bölgeleri hariç tutulur. Uçuş içindeki salt yakınlık sahipliği
bastırılır; temas/pas gibi ek kanıt ve uç noktalar korunur. Yükseklik iddiası
yoktur. Tag tek başına uzun top veya takım sahipliği hedefi değildir.

Veri/split: yalnız sentetik testler ve sentetik uçtan uca dosyalar.
`tests/test_long_ball.py` sayıları mühendislik örnekleridir. Dış maç ayar
seçimi/başarı değerlendirmesi veya yeni teslim sürümü yoktur. 72 test geçti;
bu bir futbol doğruluk skoru değildir. Yarışma görüntüleri, elle notları
ve public skorları seçim girdisi yapılmadı. Temel sürüm korundu.
Ayrıntılar: `docs/UZUN_TOP_KATMANI_TR.md`.

## D002 — otomatik SET PIECES + ölçülen bekleme/başlangıç, 4 Kasım 2026

Kullanıcı isteğiyle beş yeniden başlama türü için deneysel D katmanı eklendi.
Etiket arama ön bilgisidir; tüm etiket aralığı D kabul edilmez. Ölçülen
bekleme, yakın gözlenen oyuncu, uygun saha bölgesi ve süreklilikle desteklenen
yeniden hareket aranır. D başlangıcı ölçülen bekleme/çıkıştır; kesin düdük
anı iddiası yoktur. Kayıp top veya N/A takım etiketi tek başına D/H/A üretmez.

Veri/split: sentetik mühendislik senaryoları ve sentetik uçtan uca dosyalar.
Dış eğitim/doğrulama ya da parametre seçimi yapılmadı; verilen maçın görüntü,
elle not veya public skorlarından seçim girdisi alınmadı. Ayarlar
`tests/test_set_piece_dead_ball.py` içinde sentetik olarak kayıtlıdır.
63 test geçti. Bağımsız dış maçların eşleşen otomatik tag dosyaları ve
değerlendirilebilir D/canlı oyun hedefleri henüz yoktur; bu eksik tamamlanmadan
yeni teslim sürümü seçilmiş sayılmaz. Temel sürüm değişmedi ve yeni tam maç
çıktısı üretilmedi. Ayrıntılar: `docs/DURAN_TOP_KATMANI_TR.md`.

## V002 — yerel Smart Tagging olay tarayıcısı, 4 Kasım 2026

Kullanıcının tüm otomatik olayları video yanında anlamak için istediği salt
okunur görünüm eklendi. 638 kaynak olay yerel arayüzde korunur. Tekrarlanan
etiket grupları, bilinmeyen alanlar ve N/A takım değerleri değiştirilmez.
Model girdisi, elle doğruluk etiketi, düzeltme veya skor oluşturulmadı.
Görsel karşılaştırma için zaman atlama/aralık oynatma, filtreler, arama ve
aktif fazlar sağlandı. 53 Python testi ve sentetik tarayıcı kontrolleri geçti;
gerçek maç kareleri veya olay payload'ları hosted LLM'ye aktarılmadı.
Model/eşik seçimi yapılmadı; dondurulmuş kaynaklar değişmedi. Bu görünüm
bilimsel doğruluk değerlendirmesi değildir. Ayrıntılar:
`docs/TRACKING_IZLEYICI_TR.md`, `tools/smart_tag_view.py`.

## V001 — salt okunur yerel tracking/video arayüzü, 4 Kasım 2026

Kullanıcının açık isteği üzerine ham tracking mantığını açıklayan yerel
oynatıcı eklendi. Yarışma tactical tracking'i ve İndirilenler'deki tactical
video yalnız kullanıcının bilgisayarındaki arayüze bağlandı. Algoritma veya
eşik seçimi, tahmin üretimi, elle anotasyon veya public skor okuması yapılmadı.
Maç verisi kaynak deposuna alınmadı ve gerçek maç kareleri sohbet/QA görseli
olarak aktarılmadı. Görsel QA sentetik veride yapıldı. Video codec/metadata
erişimi ve sürenin kare sayısı/FPS ile uyumu kontrol edildi. 50 Python testi
geçti; tarayıcıda oynatma, adım, seçim ve dar ekran taşması kontrol edildi.
Bu kullanıcı aracı eğitim/validasyon deneyi veya model başarısı değildir.
Ayrıntılar: `docs/TRACKING_IZLEYICI_TR.md`.

## M003 — ortak takım hareketi değişimi, 4 Kasım 2026

Kullanıcının iki takımın ani hız değişimini top kaybı/kazanımı bağlamı olarak
kullanma önerisi uygulandı. Aynı gözlenen yuvaların önce/sonra ortalamaları,
hız büyüklüğü ve yönlü vektör değişimi ayrı hesaplanır. İki takımda değişim
aranır. Önce/sonra farklı takımlara ait yerel temas/birlikte hareket kanıtı
yoksa top kaybı doğrulanmış sayılmaz; yeni H/A ataması yapılmaz.

Veri/split: yalnız sentetik örnekler; dış maç ayar seçimi veya doğruluk skoru
yoktur. Test ayarları `tests/test_team_transitions.py` içinde kayıtlıdır.
48 test geçti: aynı hızda yön dönüşü, hızlanma, görünür oyuncu kümesi
değişimi, tek takım değişimi, eksik top kanıtı, aynı takım kanıtı,
devre/ölçüm kaybı ve uçtan uca parametre/çıktı kaydı sınandı. Teslim sürümü
seçilmedi; dış gerçek geçişlere göre doğrulama gereklidir. Temel model
korundu. Kaynak: `development/team_transitions.py`.

## M002 — oyuncu/top birlikte hareketi ve takım özetleri, 4 Kasım 2026

Kullanıcının dripling önerisi deney sahiplik algoritmasına eklendi. Kalıcı
yakınlık, aynı yuvada süreklilik ve top/oyuncu hız vektörü uyumu birlikte
aranır. Hızlı dripling kanıtı hızlı top engelini aşabilir. Rakibin birlikte
hareket kanıtı üzerinden pas aralığı yazılmaz. Takım başına ortalama hız
vektörü, ortalama hız büyüklüğü ve katılan yuva sayısı ayrı çıkarılır;
takım özetleri tek başına sahiplik belirlemez.

Veri/split: yalnız sentetik senaryolar; dış maç eğitimi/doğrulaması ve sayısal
ayar seçimi yoktur. Ayarlar `tests/test_player_motion.py` içinde sentetik
olarak kayıtlıdır. 39 test geçti: hızlı dripling, ters yönde eşit hız,
sabit durma, belirsiz yakınlık, devre/kayıp/sıçrama sınırları, eksik takım
kapsamı, eşit takım vektörlerinde farklı sahiplik ve 25 FPS aktarımı sınandı.
Yeni parametre/NPZ çıktıları uçtan uca sentetik test edildi. Futbol doğruluk
skoru veya seçilen teslim sürümü yoktur; dış dripling/sahiplik doğrulaması
henüz yapılmadı. Temel kaynaklar korundu. Ayrıntılar:
`development/player_motion.py`, `docs/HAREKET_VE_TEMAS_TR.md`.

## M001 — hareket/temas/pas uygulaması, 4 Kasım 2026

Kullanıcının hızlı top, yön değişimi ve aynı takım temas zinciri önerisi
ayrı deney katmanında uygulandı. Ayrıntılar: `docs/HAREKET_VE_TEMAS_TR.md`.
Veri: sentetik hareket, ölçüm kaybı, rakip temas, belirsiz yakınlık, ölçüm
sıçraması ve pas dizileri; ayrıca sentetik uçtan uca çalıştırıcı testi.
Dış maçlarda sayısal ayar veya başarı seçimi yapılmadı. Eğitim/doğrulama skoru
yoktur; D001'in dış maç ayrımı ileride kullanılabilir. Sentetik test ayarları
`tests/test_motion_possession.py` içinde kayıtlıdır. Seçilen sürüm: yok.
Gerekçe: dış temas/pas değerlendirmesi henüz yapılmadı. Temel model korunur.
Yarışma tracking değerleri/görüntüleriyle ayar seçilmedi; XML şeması kontrol
edildi. 28 testin tamamı geçti; bu bir futbol doğruluk skoru değildir.

## D001 — dış veri kapsamı, 4 Kasım 2026

Amaç: D katmanından önce saha dışına çıkış, bekleme ve oyuna dönüş için hangi
ölçümlerin ve değerlendirme hedeflerinin mevcut olduğunu belirlemek.

Kaynak: Metrica Sports Sample Data,
`e706dd506b360d69d9d123d5b8026e7294b13996`.
Plan SHA-256: `547ef460d5da98a2739bf35d66cf7fd12971b3dc7f2a91ec30eccd9c2a7af517`.
İki maça ait altı CSV'nin boyutu ve Git blob kimliği doğrulandı; ayrıca yerel
SHA-256 manifesti oluşturuldu. Ham içerik ve kare düzeyindeki çıktılar özel
çalışma dizininde tutuldu.

| Kapsam | Maç 1: eğitim | Maç 2: doğrulama |
| --- | ---: | ---: |
| Kare | 145.006 | 141.156 |
| Top koordinatı bulunan kare | 88.251 | 83.272 |
| Top koordinatı bulunmayan kare | 56.755 | 57.884 |
| BALL OUT olayı | 51 | 49 |
| Eşleştirilen aday duruş aralığı | 39 | 39 |
| Aday duruş aralıklarındaki kare | 16.518 | 13.640 |
| Bu aralıklarda top koordinatı bulunan kare | 0 | 0 |
| Top koordinatı bulunan SET PIECE başlangıcı | 65 / 77 | 71 / 80 |

Ayrım maç bazında ve indirme öncesinde kaydedildi. Önceki erişim geçmişi
doğrulanmadığı için bunlar dokunulmamış test maçları olarak tanımlanmaz.
Doğrulama verisi bu çalışmada yalnız kapsam raporu için okundu; ayar veya
model seçimi yapılmadı.

Aday aralık protokolü: `BALL OUT` son karesini dışarıda bırak, sonraki uygun
`SET PIECE` başlangıcından önce bitir. Aynı devrede olmalı; arada başka çıkış
veya kaydedilmiş canlı oyun varsa reddet. Bilinmeyen kareleri etiketleme.
Bu protokolün olay zamanlarıyla elde ettiği aralıklar tam D gerçeği değildir.
Faul sonrası serbest vuruş, eşleşmeyen aut başlangıçları ve tekrarlar bu
protokolde değerlendirilmez. Çizgiyi geçme anı ve hakem düdüğü ayrıca
doğrulanmış değildir.

Seçilen sınıflandırıcı ayarları: **yok**. Hız/bekleme/mesafe eşiği taranmadı.
Rapordaki çeyrek değerler betimleyici kapsam özetidir; parametre önerisi değildir.

Karar ve gerekçe: **D modeli seçilmedi veya teslim sürümüne eklenmedi.**
İki maçtaki 78 aday duruş aralığının tamamında top koordinatı kayıptır.
Bu aralıklarda topun bekleme geometrisini doğrudan ölçmek mümkün değildir.
Eksikliğin sağlayıcının veri hazırlamasından kaynaklanıyor olması mümkündür;
bu bir çıkarımdır, sağlayıcıdan doğrulanmış bir açıklama değildir. Bu veriyle
yalnız “top yoksa D” öğrenmek, başka sağlayıcıdaki gerçek top kaybını D ile
karıştırabilir. Eksiksiz canlı oyun negatifleri ve bağımsız sınır doğrulaması
olmadan böyle bir sürüm seçilmeyecek.

Ek gözlem: ham ardışık top koordinatlarından hesaplanan en yüksek hızlar
Maç 1'de yaklaşık 1.321 m/s, Maç 2'de 700 m/s'dir. Bunlar fiziksel top hızı
olarak yorumlanamaz; ölçüm süreksizliklerini gösterir. Bu incelemede noktalar
kırpılmadı ve bu değerlere bakılarak güvenilirlik eşiği seçilmedi. Top
güvenilirliği ayrı deneyde değerlendirilecek.

Sonraki veri koşulu: başka maçlarda D/canlı oyun etiketlerini ve olay sınırlarını
bağımsız değerlendirebilen; mümkünse duruş sırasında da top gözlemi veya
izinli eşzamanlı görüntü içeren bir kaynak/protokol. Mevcut aday aralıklar
protokol geliştirme için kullanılabilir; tek başlarına D sürümü seçmeye yetmez.

Temel model SHA-256:
`1efa8f1073c0c204613cdd5ad1882e4525364ada7d982a70bb27387b854ff6cc`.
Dondurulmuş sekiz çıkarım kaynak dosyasının kimlikleri işlem öncesi/sonrası
doğrulandı. Sağlanan yarışma maçı veya public referansı okunmadı. X'ten D'ye
çevrilen kare sayısı: **0**. Yeni model seçilmediği için tam maç yeniden
üretilmedi; eski dondurulmuş çıktı yeni sürüm doğrulaması olarak gösterilmedi.

Doğrulama: 19 test geçti; buna sentetik uçtan uca veri hazırlama/kapsam
incelemesi, devre/kayıp ölçüm sınırları, olay eşleştirmesi, bozuk kaynak
içeriğinin reddi ve dondurulmuş temel kaynakların korunması dahildir. Gerçek
iki dış maçın kapsam aracı da başarıyla tamamlandı. Bunlar D doğruluk skoru
veya yarışma performansı değildir.

Tekrarlanabilir dosyalar:

- Veri planı ve kullanım: `dead-ball-data-plan.json`, `docs/GELISTIRME_TR.md`.
- İndirme kaydı:
  `C:/Users/Abra/FootballPrivate/dead-ball-development-20261104/metrica-coverage-v1/download-manifest.json`.
- Kaynak hash'leri, özellik dağılımları ve ayrıntılı kapsam raporu:
  `C:/Users/Abra/FootballPrivate/dead-ball-development-20261104/audit-v1/report.json`.
- Kare düzeyindeki girdi/özellikler ve ayrı tutulan aday olay aralıkları:
  aynı `audit-v1` dizininin iki maç alt klasörü.

Bu çalışma sağlayıcı/sohbet temizliğinin tamamlandığını veya yarışma
organizatörünün bütün koşullarının karşılandığını iddia etmez.
