# Tracking noktalarını aynı kaynağın videosuna taşıma

7 Kasım 2026. Yerel, salt okunur inceleme; oyuncu kutusu/kimliği eşleme veya
sahiplik modeli seçimi değildir. Gerçek maç görüntüsü dış servise aktarılmaz.

## Hazır görünümler

- Taktik: `http://127.0.0.1:8771/`
- Yayın: `http://127.0.0.1:8772/`

Her video kendi ATD XML/TXT ve homografi CSV'sini kullanır. Kaynaklar arasında
oyuncu kimliği veya zaman dönüşümü uygulanmaz. Nokta takım renginde çizilir;
etiket ATD takip yuvasıdır, forma numarası veya tanınmış oyuncu adı değildir.
Top bu katmanda izdüşürülmez: havadaki top için saha düzlemi yeterli değildir.

## Doğrulanan ve açık kalan kısım

`tools.source_clock_audit`, video görüntüsü çözmeden MP4 paketlerinin PTS
ızgarasını, bildirilen kare sayısını, 25 FPS saatini, sıfır zaman başlangıcını,
ATD'nin ardışık kayıtlarını ve homografi kare sayısını kontrol eder. Kaynak
adları/dosya hash'leri/parmak izleri kayıtlıdır. Eşleme video 0 → ATD 1 → H 0.

Taktik: 199.319 video karesi / 199.319 ATD ve homografi kaydı. Yayın: 164.487
video karesi / 164.488 ATD ve homografi kaydı; sondaki fazla kayıt görüntüye
bağlanmaz. Başarılı yapısal saat uyumu, gerçek görüntü ile tracking'in bağımsız
olarak kare hassasiyetinde doğrulandığı anlamına gelmez. Tracking'in üretimindeki
olası gecikme ve homografinin görsel doğruluğu burada ölçülmedi. Bütün kayıtlar
`independent_image_alignment_validated=false`, `usable_for_possession=false`.
Zaman kaydırması aranmadı, insan referansı/etiketi/ayar seçimi yapılmadı.

## Çizim

Normalize saha noktası aynı karenin H matrisiyle görüntü pikseline taşınır.
API noktayı ham normalize x/y'den hesaplar; ekrandaki yuvarlanmış sayılardan
yeniden üretmez. Tarayıcı `requestVideoFrameCallback` ile gerçekten sunulan
görüntü karesini kullanır. Paket/ATD/H kimlikleri aynı değilse veya veri henüz
gelmediyse katman temizlenir. Eksik/geçersiz matris ve kayıp nokta doldurulmaz.
Görüntü dışındaki nokta kenara kırpılıp görünürmüş gibi gösterilmez.

Piksel noktaları, videonun `object-fit: contain` boşlukları ve cihaz piksel
oranıyla ekrana taşınır. Yeniden boyutlandırma ve duraklatılmış kare adımı
desteklenir. Kullanıcı başka video seçerse denetlenen kaynak bağı geçersiz
olur; işaretler gizlenir. “Videoyla eşle” kapalıyken de işaret çizilmez.

## Yeniden çalıştırma

Ayrı görüntü ortamında (PyAV gerekir), yeni bir depo dışı çıktı klasörüyle:

```powershell
python -m tools.source_clock_audit --meta C:/private/MATCH_tactical_atd.xml --tracking C:/private/MATCH_tactical_atd.txt --homography C:/private/MATCH_tactical_homography.csv --video C:/private/MATCH_tactical.mp4 --out C:/private/new-clock-audit
python -m tools.tracking_viewer --meta C:/private/MATCH_tactical_atd.xml --tracking C:/private/MATCH_tactical_atd.txt --homography C:/private/MATCH_tactical_homography.csv --video C:/private/MATCH_tactical.mp4 --clock-audit C:/private/new-clock-audit/report.json --port 8771
```

Bu bilgisayardaki denetim:
`C:/Users/Abra/FootballPrivate/native-projection-review-20261107`.
Sentetik kontrol:
`C:/Users/Abra/FootballPrivate/native-projection-synthetic-20261107`.
151 testlik paket 1 isteğe bağlı AV atlamasıyla başarılı. Bir kayıt fazla olan
kuyruk, yanlış FPS/PTS/kaynak, H geçersizliği, topu dışlama ve letterbox/DPR
kontrolleri kapsandı. 50 karelik üretilmiş videoda oynatma ve geri kare adımı
tarayıcıda doğrulandı. Gerçek maçta yalnız dosya/saat/API yapısı incelendi;
görüntü üzerinden eşik veya model seçimi yapılmadı.
