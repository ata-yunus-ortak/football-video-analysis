# Deney kaydı

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
