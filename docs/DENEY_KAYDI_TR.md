# Deney kaydı

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
