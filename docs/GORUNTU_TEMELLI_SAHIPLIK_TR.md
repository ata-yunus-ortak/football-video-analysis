# Görüntü temelli sahiplik — 7 Kasım 2026

Yeni deneysel giriş: `tools.visual_possession_experiment`.
Karar kodu: `development/visual_possession.py`.
Plan: `visual-possession-plan.json`. Donmuş `model.json` ve `clean_model/`
ayrı karşılaştırma sürümü olarak korunur. Yeni akış henüz seçilmiş teslim sürümü değildir.

## Verinin görevleri

1. RF-DETR/SAHI ve zamansal takip, mevcut karedeki kişi/top ölçümlerini üretir.
2. Otomatik tracking + XML yalnız kişi kimliği ve H/A takım eşleştirmesine yardım eder.
   `tools.visual_identity_context` ATD'nin oyuncu segmentini okur; top segmentini
   ayrıştırmaz. Metadata ve homografi kaynakları hash ile bağlanır.
3. Oyuncu konumu, görüntü kutusunun ayak noktasıdır. Tracking konumunu sahiplik
   hesabına kopyalamayız. Homografi görüntü ayaklarını ortak saha eksenine taşır;
   kişi eşleştirmesinde tracking oyuncusunu görüntüye taşımak için de kullanılır.
4. Sahiplik, mevcut görüntü topu ve kişilerin konum/mekânsal sürekliliğinden çıkar.
   Tracking topu, sağlayıcı sahipliği ve eski H/A/X sonucu kabul edilen girdiler değildir.

Metadata kimliği doğru eşleştirme garantisi değildir. Kişi kutuları hakemi otomatik
olarak tanımaz. Eşleşmeyen kişi bilinmiyor kalır; topa en yakın kişi bilinmiyorsa
onu atlayıp daha uzaktaki etiketli oyuncuya sahiplik verilmez. Kamera iz ID'si
kanonik oyuncu ID'si değildir. Farklı kameraların metadata ID'leri farklıysa
otomatik metadata temelli `canonical_player_ids` eşlemesi ayrıca gerekir;
aynı sayısal slot aynı kişi varsayılmaz.

## İlk görüntü kontrolü kuralı

Kişi ayak noktası ile tracking oyuncu izdüşümü karşılıklı en yakın, yeterince
ayrışmış ve zaman içinde tutarlı olmalıdır. İki takımın gözlem kapsamı ve kimlik
eşleme oranı aranır. Kırpılmış ayak noktaları kimlik eşlemesine alınmaz.

Mevcut karede tek, onaylı, gerçekten ölçülmüş top izi olmalıdır. Birden fazla
ölçülmüş aday (henüz onaylanmamış olan dahil), tahmin veya kayıp top X üretir.
Yakınlık kişi kutusu yüksekliğine göre ölçeklenir; topun oyuncuya göre göreli
hareketi ve bu ilişkinin belirli süre sürmesi gerekir. Kontrol tartışmalıysa,
göreli hareket hızlıysa veya kişi görüntü hareketi fiziksel olarak sıçrıyorsa
onay verilmez. Kamera/saat/iz kesintisi onay geçmişini sıfırlar; sahiplik kayıpta
otomatik taşınmaz.

Bu ilk kural **görüntüden sürekli kontrol adayıdır**; gerçek temasın, oyundaki
tek topun veya topun yerde olduğunun doğrulandığı anlamına gelmez. `ground_verified`
false kalır. Kamera ötelemesine göreli konum yardımcı olur; genel pan/zoom veya
perspektif etkisini kusursuz çözmez. Havadan geçen topun ayakla çakışması ve
yanlış dedektör adayları hâlâ hata kaynağıdır. Uçuş boyunca pas sahipliğini,
şut/temas sınıflandırmasını veya D'yi bu ilk sürüm çözmez. Önceki tracking tabanlı
temas/pas prototipleri bu akışa gizlice aktarılmadı.

## Taktik ve yayın seçimi

- Taktik video ana zaman eksenidir. Her kamera kendi native kareleriyle işlenir.
- Yayın ancak tam kaynak/kare/epoch çiftinin otomatik eşlemesi, hata sınırı,
  canlılık, kamera kalibrasyonu ve oyuncu kapsamı uygunsa değerlendirilir.
- Ortak kanonik oyuncuların **görüntüden türetilen** saha konumları karşılaştırılır.
  Yeterli ortak oyuncu ve geometrik uyum yoksa yayın devre dışıdır.
- Toplu aşırı görüntü hareketi, az oyuncu, tekrar, bilinmeyen canlılık, yanlış
  kaynak veya geometri uyuşmazlığında taktik karar korunur.
- Geçerli yayında uygun görünen oyuncuların ölçümü tercih edilir; yayın kadrajı
  dışındaki oyuncular taktikten kalır. Tekil çelişkili/sıçrayan yayın oyuncusu
  taktik ölçümünü değiştirmez.
- Yayın görüntüsünde onaylı kontrol adayı varsa onun H/A ve oyuncu kararı alınır.
  Yayında top/kontrol belirsizse taktik görüntünün kendi kararı kullanılır.
  Taktik de belirsizse sonuç X'tir. Kaynaklar arası ham piksel mesafesi hesaplanmaz.
- Her kameranın onay geçmişi ayrıdır. Birleşmiş koordinatlardan hız/temas türetilmez;
  böylece kaynak değişimi sahte vuruş üretmez. Geri giden/tekrarlanan eşlemeler
  önceki yayın sahipliğini canlandırmaz.

Yayın görüntüsünün detaylı olması tek başına doğruluk kanıtı değildir. Bu tercih
politikasının katkısı dış maçlarda ayrıca ölçülmelidir.

## Çalıştırma

Önce mevcut `tools.match_analysis` ile görüntü ölçümleri ve zamansal top izleri
üretilir. Ardından her kamera için kaynaklandırılmış otomatik kimlik bağlamı hazırlanır:

```powershell
python -m tools.visual_identity_context --spec C:/private/tactical-identity-spec.json --out C:/private/tactical-identity
python -m tools.visual_identity_context --spec C:/private/broadcast-identity-spec.json --out C:/private/broadcast-identity
python -m tools.visual_possession_experiment --tactical-manifest C:/private/tactical-identity/camera-manifest.json --broadcast-manifest C:/private/broadcast-identity/camera-manifest.json --pair-alignment C:/private/verified-pairs.jsonl --plan visual-possession-plan.json --out C:/private/new-video-led-possession
```

Yalnız taktik için yayın ve çift eşleme seçenekleri verilmez.

Kimlik hazırlama spec'i: `provided_fixture_used=false`,
`reference_annotations_as_inputs=false`, `source_kind`, `fixture_id`,
`analysis_path`, mutlak `tracking_path`, `metadata_path`, `homography_path` ve
üçünün SHA-256'sı; açık `tracking_frame_offset` / `homography_frame_offset`.
ATD satırları 1 tabanlı, video/homografi 0 tabanlıdır; ofsetler otomatik tahmin edilmez.
Kaynak XML'in takım sırası H/A olmalıdır; iki kamera ortak takım tanımını kullanmalıdır.

İsteğe bağlı `camera_evidence_path` / `camera_evidence_sha256`, kaynak/kare/epoch/
zamanla bağlı `automatic_camera_validation` satırları taşır. Sözleşme kodda açıkça
tanımlıdır. Bu kanıt yokken zaman/kalibrasyon/canlılık doğrulanmış sayılmaz.
Sadece matrisin geçerli olması yeterli değildir. Araç bunların doğrulayıcısını
uygulamaz; kanıtı başka doğrulanmış otomatik aşamadan bekler.

Koşucu önce kaynak/ayar hash'lerini kaydeder, sonra kare kare `frames.jsonl` ve
`possession.csv` yazar. CSV alanları: `frame,label,owner_id,decision_source,reason`.
Görüntü ve kimlik bağlamı akış halinde okunur; iki kameranın bütün tespitleri
bellekte tutulmaz. Ham veri ve çıktılar depo dışında kalır.

## Yapılan doğrulama

17 yeni test; toplam 195 testten 194'ü geçti, 1 isteğe bağlı AV testi atlandı.
ATD top alanına kasıtlı olarak sayısal olmayan veri yazılan sentetik koşu da
tamamlandı: bu alanın kimlik adaptöründe ayrıştırılmadığı kontrol edildi.

Kalıcı kontrollü denemede 8 karelik aynı oyuncu geometrisinde:

| Sentetik koşul | Sonuç |
| --- | --- |
| Taktik görüntü: top H oyuncusunda | 4 onay öncesi X, ardından 4 H |
| Eşleşmiş yayın: top A oyuncusunda | 4 onay öncesi X, ardından 4 A |
| Aynı yayın, eşleme geçersiz | 4 X, ardından taktikten 4 H |

Bu, yönlendirme ve görüntü kararının çalıştığını gösterir; futbol doğruluğu değildir.
Mevcut dış eğitim kesitlerinde 1.200 çıktı karesi, bağımsız otomatik oyuncu
kimlik/geometri eşlemesi olmadığında X kaldı. Gerçek görüntüden sahiplik başarısı
henüz ölçülmedi. Ayarlar sentetik mühendislik değerleridir; yeni sürüm seçilmedi.

Özel kayıt: `C:/Users/Abra/FootballPrivate/visual-possession-development-20261107`.

## Tam maç öncesi kalanlar

Eşzamanlı izinli dış videoda kimlik, zaman, kalibrasyon ve canlı/tekrar kanıtı
doğrulanmalı; görüntü kontrol adayları gerçek sahiplik hedefleriyle değerlendirilmeli.
Tek kamera ve yayın katkısı ayrı karşılaştırılmalı. Mevcut Barcelona saat eşlemeleri
inceleme adayıdır; bağımsız görüntü eşlemesi/kalibrasyon onayı değildir. Yeni akışla
Barcelona tam maç çizelgesi üretilmedi; önceki çizelge eski donmuş modele aittir.

Görüntü güvenilirliği ve eşleme doğrulandıktan sonra tag destekli D sınırları ayrı
katman olacak: tag aralığı içinde durma/yeniden başlama adayları ve belirsizlikleri.
Sabit top, top kaybı veya bütün tag aralığı otomatik D yapılmayacak.
