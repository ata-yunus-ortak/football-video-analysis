# Taktik ve yayın kaydını otomatik eşleme

`ESLESME-IZLE.cmd`, hazır otomatik eşlemeyi `http://127.0.0.1:8768` üzerinde
açar. Taktik video ana zaman çizgisidir. İki video ve iki ayrı ATD saha görünümü
yan yana gösterilir. Oynat/duraklat, hız, kare adımı, kare numarası, zaman
çizgisi, ilk eşlemeye gitme ve kesintisiz aday aralık listesi bulunur.

Eşleme yoksa yayın durur, üzerinde uyarı görünür ve yayın tracking'i gizlenir.
Önceki bir görüntü aynı oyun anı gibi gösterilmez. İki kaynakta takım renkleri
XML takım adlarıyla tutarlı tutulur; oyuncu takip numaraları birleştirilmez.
Yerel eşleme yolu Git'e alınmayan `viewer-local.cmd` içindeki
`MTAH_ALIGNMENT` değişkeniyle ayarlanabilir. Varsayılan yol
`%USERPROFILE%/FootballPrivate/video-sync/alignment.json`.

## Otomatik işlem

1. `tools.clock_observations`, video karelerinin yalnız bellekteki sol üst
   bölgesini yerel RapidOCR/ONNX Runtime ile okur. Anahtar kareler arasından
   en az beş saniye aralıkla örnek alır; kaynak PTS ve FPS korunur. Normal
   MM:SS ve açık `45+02:03`/`90:00+01:12` biçimleri ayrıştırılır. Skor
   rakamları saat kabul edilmez; harfler rakama çevrilmez. Saat belirsizse
   gözlem eksik kalır. Açık devre bilgisi yoksa dakika 45 üzerinden devre
   uydurulmaz.
2. `development/clock_alignment.py`, saat ilerleyişi tutarlı dizileri bulur.
   Donmuş/geri giden saat, uzun okuma boşluğu ve devre değişimi diziyi keser.
   Bir oyun saati birden çok video bölümünde bulunuyorsa eşleme kesinleştirilmez.
3. Her benzersiz saat adayı çevresinde iki takımın oyuncu konumları üç
   ardışık anda karşılaştırılır. Aynı takım içinde karşılıklı en yakın
   gözlenen konumlar geçici geometrik destek sağlar; bunlar kalıcı oyuncu
   kimliği eşlemeleri değildir. Geçersiz homografi, eksik takım kapsamı,
   kaynaklar arası belirgin uyuşmazlık ve birbirinden ayrı benzer zaman
   adayları ele alınır. Top tek başına eşleme kanıtı değildir.
4. Yalnız uygun komşu bağlantılar arasında parça parça zaman dönüşümü kurulur.
   Kesintilerin üzerinden enterpolasyon veya uçlardan dışarı uzatma yapılmaz.
   Çakışan/ters sıradaki bağlantılar elenir. Video sonunda ATD'de fazla bir
   kayıt varsa geometri araması mevcut video kareleriyle sınırlanır.

“Yalnız saat adayı” yaklaşık gezinme içindir. “Saat + tracking desteği” ek
geometrik uyum bulunduğunu belirtir. İkisi de bağımsız kare doğruluğu ölçümü,
canlı yayın/tekrar garantisi veya sahiplikte kullanılabilirlik onayı değildir.
İki seyrek saat okuması arasında kısa bir tekrar hâlâ gözden kaçabilir.
Bu nedenle bütün bağlantılar `usable_for_possession=false` olarak korunur.
Kayıttaki `uncertainty_s` mühendislik çözünürlüğüdür; kalibre edilmiş bir
istatistiksel güven aralığı veya kanıtlanmış hata üst sınırı değildir.

## Kaynak ve tekrar çalıştırma

`sync-review-plan.json` içindeki ayarlar yalnız sentetik mühendislik
kontrollerinden gelir; sağlanan maç üzerinde ayar/model seçimi yapılmaz.
Donmuş H/A/X modeli değişmez. Görüntüden top/oyuncu tespit modeli bu işlemde
çalışmaz; yalnız saat OCR'ı çalışır. Gerçek maç görüntüleri asistanla veya
başka bir servise paylaşılmaz; saat kırpmaları diske kaydedilmez.

OCR için ana modelden ayrı ortam:

```powershell
python -m venv .venv-sync
.\.venv-sync\Scripts\python -m pip install -r requirements-sync-lock.txt
.\.venv-sync\Scripts\python -m tools.clock_observations --video C:/private/tactical.mp4 --config C:/private/tactical-ocr-config.json --out C:/private/tactical-clock-v1
.\.venv-sync\Scripts\python -m tools.clock_observations --video C:/private/broadcast.mp4 --config C:/private/broadcast-ocr-config.json --out C:/private/broadcast-clock-v1
.\.venv-sync\Scripts\python -m tools.sync_alignment --bundle C:/private/bundle.json --plan sync-review-plan.json --out C:/private/alignment-v1
python -m tools.paired_viewer --alignment C:/private/alignment-v1/alignment.json --open
```

Her çıktı dizini yeni ve kaynak deposunun dışında olmalı. OCR kayıt dosyası
`purpose=automatic_read_only_synchronization`, `parameters_selected_on_provided_fixture=false`,
`human_anchors_used=false`, kaynak açıklaması, video SHA-256 ve planın `clock_ocr`
ayarlarını içerir. `fixture_kind`, izinli dış video için `permitted_external_video`,
sentetik için `synthetic_fixture`; yalnız sağlanan kaydın salt okunur otomatik
incelemesi için `provided_fixture_review` olur. Bu alan veri/model seçimi izni
vermez. Video hash'i işlemden önce doğrulanır; kod/model hash'leri, paket
sürümleri, video parmak izi, otomatik saat gözlemleri ve eksiklikleri kaydedilir.

`bundle.json`, `tactical` ve `broadcast` anahtarlarının her birinde `video`,
`meta`, `tracking`, `homography`, `clock_dir` dosya/dizin yollarını taşır.
Tamamlanmamış OCR çıktısı veya farklı kaynak dosyası sessizce yeniden kullanılmaz.
Ham videolar, TXT/XML/CSV, saat çıktıları ve eşleme dosyası Git'e alınmaz.

OCR: [RapidOCR](https://github.com/RapidAI/RapidOCR),
[RapidOCR ONNX Runtime 1.4.4 dağıtımı](https://pypi.org/project/rapidocr-onnxruntime/1.4.4/),
[Apache-2.0 lisansı](https://github.com/RapidAI/RapidOCR/blob/main/LICENSE).
Önceden eğitilmiş OCR ağırlıkları bu dağıtımın içindedir; bizim eğittiğimiz
veya sıfırdan yazdığımız bir OCR modeli olarak sunulmaz. Depoda bu ağırlıklar
yeniden dağıtılmaz. Kesin paket sürümleri `requirements-sync-lock.txt` içindedir.

## Hibrit sahiplik için sonraki koşul

Taktik tracking ana zaman/alan kapsamını sağlar; doğrulanan yayın aralıkları
ek ölçüm kaynağı olabilir. Önce başka maçlarda zaman hatası, kısa tekrarlar,
oyuncu/takım eşlemesi ve kaynak güveni doğrulanmalıdır. Kaynaklar anlaşırsa
destek artabilir; çelişirlerse körlemesine ortalama veya sahiplik değişimi
yapılmamalıdır. Eksik top/oyuncu ve eşleme boşluğu belirsiz kalmalıdır.
Mevcut eşleme görüntüleyicisi henüz hibrit sahiplik çıkarımı değildir.
