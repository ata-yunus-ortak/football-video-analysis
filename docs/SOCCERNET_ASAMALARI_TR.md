# Profesyonel yayın görüntüsünden tracking ile birleşen sisteme

Başlangıç: 7 Kasım 2026. Bu, yeni deneysel geliştirmedir; mevcut donmuş
sahiplik sürümünü değiştirmez. Veri edinme planı `soccernet-data-plan.json`.

1. **Küçük ve izlenebilir veri:** kamuya açık SoccerNet GSR eğitim arşivini
   sabit HF commit'inden incele. İlk eğitim kesitinin ilk 25 JPEG karesini ve
   sağlanan etiketini al; tüm 9,76 GB arşivi indirme. Sıkıştırılmış parça
   aralıklarını ve dosya hash/CRC'lerini kaydet. Tam arşiv SHA doğrulandı deme.
2. **Görüntü analizi:** JPEG'leri RGB kayıpsız doğrulanmış videoya dönüştür;
   video karesi–kaynak resim eşlemesini sakla. Mevcut RF-DETR Nano/SAHI ve
   ByteTrack ayarlarını değiştirmeden çalıştır. Etiketler dedektörün girdisi
   değildir. Görüntü dizisine atanan FPS, orijinal video PTS ölçümü değildir.
3. **Ayrı ölçüm:** tahminler tamamlandıktan sonra referans şemasını/boyutunu
   kontrol et. İnsan kutusu, takip kimliği, takım/rol ve saha konumunu ayrı
   değerlendir. İlk kısa eğitim kesitindeki sonuçlar genel başarı veya bağımsız
   test sonucu değildir. Gerçek dosyada top kutusu bulunup bulunmadığını ayrıca
   kontrol et; kişi ölçümünden top başarısı çıkarma.
4. **Kapsamı büyütme:** farklı kaynak maçları belirleyip maç bazında geliştirme
   ve doğrulama ayrımı yap. Klip numaraları bağımsız maç kabul edilmez. Hareket,
   örtüşme, küçük top, kamera kesmesi ve dar kadraj örnekleri kapsanmalı.
   Top katmanı için gerçekten etiketli top kapsamını ve kayıp/örtülü top
   durumlarını ayrıca denetle; ilk GSR örneğinde top kutuları da bulundu.
5. **Tracking bağlantısı:** görüntüden ölçülmüş kişi/top adayını zaman,
   kalibrasyon, takım/kimlik ve belirsizlik bilgileriyle aynı sözleşmeye taşı.
   Referans saha koordinatını dedektör tahmini gibi sunma. Piksel hızını metre
   hızı sayma. Güvenilir eşleşme yoksa taktik tracking'i koru; görünmeyeni üretme.
6. **Birleşik sürüm:** taktik öncelikli mevcut hibrit katmana yalnız doğrulanmış
   ölçümleri al. Duran top, uzun top, temas ve sahiplik katmanlarını ayrı ölç;
   katkısı gösterilen sürümü dondur. Ardından yarışma maçını otomatik işle.
   Yarışma görüntüsündeki insan düzeltmeleri geliştirme girdisi olmaz.

SoccerNet araştırma kullanımı ve yeniden dağıtım sınırlamaları geçerlidir.
GSR veri kartındaki GPL-3.0 etiketi, maç yayınlarına ticari kullanım hakkı
vermez. Ham yayın erişimi ayrıca HF erişim/NDA adımı ister; burada sözleşme
kabul edilmedi. Ham görüntü/etiket/tahminler Git deposu dışında tutulur.

Kaynaklar: [GSR](https://github.com/SoccerNet/sn-gamestate),
[veri kartı](https://huggingface.co/datasets/SoccerNet/SN-GSR-2024),
[koşullar](https://www.soccer-net.org/faq).

## İlk çalışmanın sonucu

SNGS-060, kaynak `game_id=4`, eğitim arşivinden ilk 25 kare. Referans sürümü
1.3; metadata 25 FPS ve 1920×1080 boyutunu doğruladı. 15 oyuncu, 2 hakem ve
1 top için 25'er karelik etiketler mevcut; ilk karelerde ignore bölgesi yok.
Etiketler eğitim/değişiklik için kullanılmadı; tahmin dosyası hash'i ölçümden
önce kaydedildi. Etiketlerdeki saha koordinatı/takım kimliği modele verilmedi.

| Aynı 25 kare | Normal Nano | Aynı Nano + SAHI |
| --- | ---: | ---: |
| Kişi kutusu eşleşmesi / etiketli kişi kutusu | 409 / 425 | 416 / 425 |
| Eşleşmeyen kişi tahmini | 24 | 175 |
| Top kutusu eşleşmesi / etiketli top kutusu | 0 / 25 | 19 / 25 |
| Eşleşmeyen top tahmini | 0 | 11 |

Eşleşme, güven sırasıyla bire bir IoU ≥ 0,5 kutu karşılaştırmasıdır; resmî
AP/HOTA/sahiplik puanı değildir. Sayılar karelerde tekrarlanan gözlemlerdir.
Top sonuçları gerçek dosyada top kutuları bulunduğu görüldükten sonraki
keşifsel ölçümdür. Etiketin oyundaki tek doğru topu bütün koşullarda kapsadığı
ve bütün kenar kişilerini etiketlediği varsayılmaz. İki yöntem arasında seçim
yapılmadı; daha çok aday, daha çok doğru gözlem anlamına gelmez.

CPU/model yükü dahil yaklaşık 15/58 saniye; eşzamanlı kısa koşular donanım
benchmark'ı değildir. Takım/rol çıkarımı, kalibrasyon doğruluğu, iz kimliği
başarısı ve sahiplik ölçülmedi. İlk bir saniyelik eğitim kesiti genelleme
kanıtı değildir. `hybrid_ready=false` korunur.

Özel yerel kayıt: `C:/Users/Abra/FootballPrivate/soccernet-development-20261107`.
`sample-v2`, `video-v1`, `native-v1`, `sliced-v1`, iki `*-audit-v1` raporu ve
`sliced-preview-v1/detections.mp4`. İlk `sample-v1` aktarımı zaman aşımında
eksik kaldı, kullanılmadı. İkinci aktarımda doğrulanan HTTP aralıkları toplamı
35.449.013 byte; başarısız isteklerin kısmi ağ trafiği bu sayıya dahil değildir.
Tam arşiv hash'i doğrulanmadı; seçilen dosyalar ZIP CRC ve yerel SHA-256 ile
kayıtlı. Her JPEG'in RGB içeriği FFV1 video tekrar çözümünde bire bir doğrulandı.

Tekrarlama araçları: `tools.soccernet_sample`, `tools.soccernet_video`, mevcut
`tools.vision_experiment` / `tools.vision_preview`, `tools.soccernet_box_audit`.
Komutlar `--help` verir; çıktılar yeni ve depo dışı klasörlerde olmalıdır.

## Görsel inceleme — görüntü katmanı önce

Kullanıcının 7 Kasım yönlendirmesi: önce görüntü analizi üzerinde görerek
çalış, tracking ile hibrit geliştirmeyi sonraya bırak. `tools.vision_review`
ham kare, normal dedektör, SAHI ve sağlanan referansı aynı karede gösterir.
Kare seçimi, 0,1–1× oynatma, kişi/top kutusu açma, yakınlaştırma ve referans
top merkezine yakınlaşma sunar. Son seçenek yalnız görünümü değiştirir;
referans top modele verilmez. Ekranda eşik değiştirme veya düzeltme kaydı yoktur.

```powershell
python -m tools.vision_review --study C:/Users/Abra/FootballPrivate/soccernet-development-20261107 --port 8769
```

Adres `http://127.0.0.1:8769/`. Görüntüler yalnız loopback üzerinde sunulur;
dış servis çağrısı yoktur. Görsel geliştirme masası yalnız kayıtlı dış eğitim
örneğini kabul eder; yarışma maçı geliştirme girdisi olmaz. İlk örnek yalnız
bir saniyedir; kutu hataları görülebilir, uzun takip/örtüşme/kamera kesmesi
başarısı çıkarılamaz. Bunlar için daha uzun ve farklı maç kesitleri gerekir.

Görüntü aşamasındaki sıra: hatalı/tekrarlı kişi kutuları, kayıp/yanlış top,
top adayının zaman içinde seçimi, iz kimliği ve rol/takım ayrımı, kalibrasyon.
Her aşama farklı maçlarda karşılaştırılmadan hibrit giriş olarak kabul edilmez.
Kusursuzluk iddiası yerine hatayı ve belirsizliği ölçen kabul ölçütleri gerekir.

## Çok kesitli inceleme galerisi

`soccernet-gallery-plan.json`, eğitim arşivindeki sıralı 0,8,16,24,32,40,48,56
indekslerinden sekiz kesiti ve önceden belirlenmiş 75'er karelik aralıkları
kaydeder. Bunlar sekiz ayrı kaynak maç varsayılmaz; gerçek `game_id` metadata
alanından gösterilir. İçerik/başarıya göre örnek ayıklanmaz. Önceki Nano/SAHI
ayarları değişmez. Etiketler karşılaştırma görünümüdür, tespit girdisi değildir.

`tools.vision_gallery_build --mode acquire --plan soccernet-gallery-plan.json
--out C:/private/gallery` yalnız seçilen üyeleri indirir. ZIP içindeki kareler
karışık sırada olduğundan yerel üye başlığı, sıkıştırma türü, boyut ve CRC
doğrulanarak küçük byte aralıkları alınır; dört indirme işçisi kullanılır.
Tam arşiv hash'i doğrulandı denmez. İlk büyük blok önbellek denemesi durduruldu;
eksik dosyalar ve kaynak snapshot'ı özel kayıt altında ayrı korunur.

`--mode process --out C:/private/gallery --settings C:/private/sliced-config.json`
tamamlanan kesitleri bekleyerek RGB kayıpsız video, normal/dilimli tahminler
ve 3 kat yavaş kutulu MP4 üretir. Normal ve SAHI aralıkları aynı kareleri kapsar.
Tamamlanmış kesitler `gallery.json` listesine girer. Görsel inceleme sunucusu
`--gallery C:/private/gallery/gallery.json` ile listeyi yeniler; henüz tamamlanmamış
bir kesit hazır diye gösterilmez. Kesit seçici, önceki/sonraki kesit ve döngü
aynı dört görünümü korur. Yeni eşik/model seçimi veya resmî doğruluk ölçümü yoktur.

Tamamlanan yerel galeri `http://127.0.0.1:8770/` adresinde sekiz adet 3 saniyelik
kesit sunar; önceki kısa örnekle dokuz seçenek vardır. Kaynaklar üç ayrı maç
kimliğine aittir. Toplam 600 yeni kaynak karesi, her iki dedektörde aynı
ayarlarla işlendi. “Kesitleri peş peşe oynat” hazır kesitleri sırayla açar;
“Döngü” de açıksa listenin sonunda başa döner. Hata bildirmek için kesit adı
ve ekrandaki bir tabanlı kare numarası yeterlidir. Galeri ve bütün kesitlerin
ilk/son kare uçları `gallery-verification.json` ile kontrol edildi.
