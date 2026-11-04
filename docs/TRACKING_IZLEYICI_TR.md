# Tracking Stüdyosu

## Smart Tagging + video

Üstteki “Smart Tagging + video” görünümü otomatik XML dosyasının tüm
olaylarını zaman sırasıyla gösterir. Doğrudan adres:
`http://127.0.0.1:8765/#smart-tagging`. Başlatıcı mevcut maçın XML'ini de bağlar.

- Olay türü, takım, devre ve alt tür filtreleri ile bütün etiket değerlerinde arama.
- Olayı seçince videoda ve tracking zamanında olayın başlangıcına gitme.
- Başlangıç/bitiş video zamanı, süre, yarı açık kare aralığı `[başlangıç,bitiş)`,
  orijinal olay kodu, XML sıra/ID'si ve sağlanan bütün ek alanları görüntüleme.
- Aynı grup altında tekrarlanan etiketleri kaybetmeden gösterme; eksik/N/A
  takım bilgisini bir takıma dönüştürmeme. Bilinmeyen etiket grupları da korunur.
- Seçilen aralığı oynat, aralık sonunda dur, tekrarla ve önceki/sonraki filtreli
  olaya geç. Elle zaman çizelgesiyle başka yere gidilirse aralık oynatma iptal olur.
- “Bu karedeki otomatik etiketler” bölümünde üst üste binen bütün aktif fazlar.
  “Yalnız bu anda aktif” seçeneği olay listesini o kareye daraltır.

Zamanlar maç saatinden değil tactical videonun başlangıcından itibaren saniyedir.
Dosyanın ham sınırları değiştirilmez; video dışındaki değerler uyarıyla korunur
ve gezinme video sınırına alınır. Sıfır uzunlukta aralık oynatılmaz.

Olaylar kesin sahiplik veya gerçek temas anları değildir. Görüntüyle birlikte
anlamak mümkündür; bu ekran doğruluk yüzdesi hesaplamaz, doğru/yanlış puanı,
elle etiket, düzeltme veya kişisel olay notu saklamaz. Buradaki incelemeyi
sağlanan maç üzerinde ayar/model seçimine dönüştürmemek gerekir.

CLI'de isteğe bağlı ek argüman: `--smart-tagging C:/path/smart_tagging.xml`.
Sentetik örnek olaylar `--demo` modunda otomatik gelir. API yalnız yerel
`GET /api/tags` ile çalışır; model koduna veya model girdilerine bağlanmaz.

Ek doğrulama: 53 Python testi geçti. Tarayıcıda filtre/arama, yinelenen alanlar,
üst üste binme, zaman atlama, aralık sonunda durma, tekrar ve elle gezinmede
tekrarı iptal etme sentetik olaylarla sınandı. Masaüstü/dar ekran görselleri
yalnız sentetik veriden üretildi. Gerçek XML'de yalnız yükleme ve toplam
638 kaydın korunması kontrol edildi; doğruluk başarısı ölçülmedi.

Yerel, salt okunur eğitim/inceleme arayüzüdür. Model çalıştırmaz veya ayarlamaz;
elle etiket, düzeltme, temas notu veya çıktı tahmini kaydetmez. Kullanıcı bu
arayüzü ham tracking mantığını anlamak için istedi. Bu görünümden alınan
gözlemler yarışma maçında model/eşik seçimi için kullanılmamalıdır.

## Açma

Ekip kurulumu için önce `TEAM_START_TR.md` oku. Proje kökündeki
`TRACKING-IZLE.cmd` dosyasını çalıştır. Kendi yollarını Git'e alınmayan
`viewer-local.cmd` içinde ayarlayabilirsin. Aşağıdaki yollar ilk geliştiricinin
yerel örnekleridir; başlatıcı artık kullanıcı profili veya ortam değişkenleri
üzerinden çalışır. Veri olmadan `TRACKING-DEMO.cmd` kullanılabilir.

Yerel örnek yollar:

- XML ve tracking: `C:/Users/Abra/FootballPrivate/mtah2027/bundle/tactical/`.
- Video: `C:/Users/Abra/Downloads/BAR-ATH_tactical.mp4`.
- Arayüz: `http://127.0.0.1:8765`.

Sunucu açıkken bağlantıyı tarayıcıda kullan. Başlatıcı terminalini kapatmak
sunucuyu da kapatır. Aynı portta açık bir örnek varsa mevcut bağlantıyı aç;
ikinci örneği başlatma. Kişisel dosya yolları başlatıcıda değiştirilebilir.

Genel komut:

```powershell
python -m tools.tracking_viewer --meta C:/path/match_atd.xml --tracking C:/path/match_atd.txt --video C:/path/match.mp4 --open
```

Video verilmezse arayüzdeki “Video seç” düğmesi yerel dosyayı tarayıcı içinde
açar. Farklı süredeki video otomatik eşleştirmeye alınmaz; aynı tactical
kayıt seçilmelidir. Başka maçın videosu bu tracking ile eşzamanlı değildir.

## Görünüm

- Sol: saha üzerinde takım renkli oyuncu çemberleri, takip yuvası numaraları,
  top, ham hız değerleri ve yön okları. Sağ: aynı tactical maç videosu.
- Oynat/duraklat, 0,25–4 kat hız, kare adımı, kareye git ve zaman çizelgesi.
- Video yüklüyken eşleştirme açıksa video saati tracking saatini sürer.
  Video karesi 0, ATD kaydı 1'dir. Tracking 25 FPS olarak metadata'dan okunur.
- Çember veya liste satırı seçildiğinde ham hız, konumdan türetilen hız,
  x/y, vx/vy ve yön açısı görüntülenir.
- Yön oku `vx=(x_t-x_(t-1))*saha_uzunluğu*FPS`,
  `vy=(y_t-y_(t-1))*saha_genişliği*FPS` ile hesaplanır. Birimi m/s'dir.
  Ham `s` sütunu km/saat hız büyüklüğüdür, yön içermez.
- x sağa, y aşağı artar. Açı sağa 0°, aşağı +90°, yukarı -90°'dir.
  Bunlar saha eksenleridir; takımın hücum yönü olarak yorumlanmaz.
- Oklar yarım saniyelik hareketi temsil eder ve okunabilirlik için en çok
  8 saha metresi uzunluğunda çizilir. Gerçek sayısal vektör ayrıntıda bulunur.
- Top izi son 1 saniyenin önbellekteki geçerli ölçümlerini gösterir; eksik
  noktaları birleştirmez. İlk karede veya kayıp noktadan sonraki ilk karede
  hız vektörü çizilmez. Sıfır vektörün yönü gösterilmez.

Bu ekran ham ölçümleri gösterir; hız sıçramalarını model filtresiyle gizlemez.
Slotlar gerçek oyuncu kimliği veya forma numarası değildir. Sonlu koordinat
bağımsız görsel tespit güveni anlamına gelmez.

## Yerel çalışma ve doğrulama

Sunucu yalnız 127.0.0.1 üzerinde dinler. Video diskten byte-range ile,
tracking küçük kare paketleriyle yerel tarayıcıya gider; harici servis, CDN,
LLM veya uzak sunucuya yükleme yapılmaz. Ham veriler kaynak deposuna alınmaz.

50 Python testi geçti. Okuyucunun x/y/s şeması, km/saat birimi, türetilen
vektörler, eksik koordinatlar, kare hizası ve video range istekleri sınandı.
Tarayıcı QA'sı sentetik veride yapıldı: oynat/duraklat, kare seçimi, kayıt
seçimi, masaüstü ve dar ekran görünümü. Sentetik ekran görüntüleriyle düzen
kontrol edildi. Gerçek videoda yalnız codec/metadata yüklenmesi ve
7.972,76 saniyelik sürenin 199.319 / 25 ile uyumu kontrol edildi;
gerçek maç kareleri QA görseli olarak aktarılmadı.

Sentetik örnek: `python -m tools.tracking_viewer --demo --port 8766`.
