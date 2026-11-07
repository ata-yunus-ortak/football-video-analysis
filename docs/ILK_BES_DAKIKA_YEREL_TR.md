# İlk beş maç dakikası: yerel inceleme

**7 Kasım düzeltmesi:** Bu belge geçmiş üretimin kaydıdır, yeni kullanım
talimatı değildir. Öncelikli 3 Kasım e-postası çıktıyı sağlanan videoyla
karşılaştırmayı yasaklıyor. 8777 sunucusu kapatıldı. Bu çıktı geliştirme veya
doğrulama girdisi olarak kullanılmayacak. [Güncel süreç](OTONOM_GELISTIRME_TR.md).

Kullanıcı iki saniyelik gösterim yerine maç saati 00:00–05:00 bölümünü,
algoritmanın seçtiği oyuncuyla birlikte istedi. Yerel ekran:
`http://127.0.0.1:8777/`.

`tools.visual_long_review` ilk üç otomatik saat okumasından kayıt başlangıcını
yaklaşık bulur. Bu kayıt için kaynak başlangıcı 449. saniye; 25 FPS'de 7.500
ardışık kare işlenir. Video dosyasının başındaki maç öncesi bölüm gösterilmez.
Tespit örneklemesi veya kare atlama yoktur. Çizimli görüntü normal hızdadır;
10 saniyelik parçalar kapandıkça izlenebilir. Sonunda tek parça video oluşur.
Hazır olan süre ve tamamlanma durumu yerel `status.json` kaydından okunur;
bir parçanın varlığı beş dakikanın tamamlandığı anlamına gelmez.

## Seçilen oyuncuyu okuma

Kalın yeşil kutu ve ok mevcut görüntü kontrol kuralının seçtiği oyuncu adayını
gösterir. Büyük `ALG SECIMI` yazısı takım/forma bilgisini taşır. Oyuncu yoksa
`BELIRSIZ (X) - OYUNCU SECILMEDI` yazar. En yakın oyuncuya zorla sahiplik
verilmez. Küçük yeşil/sarı/pembe top işaretleri sırasıyla gözlenen onaylı iz,
henüz onaylanmamış iz ve kısa tahmindir.

Görüntü kontrol kararı ayrı, açıkça işaretli varsayım görünümüdür: native
zaman, sağlayıcı homografisi ve canlılık varsayılır. Bunlar bağımsız olarak
doğrulanmış sayılmaz. `strict decision` eksik doğrulama nedeniyle X kalır.
Oyuncu/takım/forma bilgisi tracking/XML eşleme adayıdır. Görsel kimlik veya
hakem tanıma iddiası yoktur. Tracking topu ve eski sahiplik çıktısı okunmaz.

Yayın ham görüntüsü yaklaşık eşleme olan aralıklarda karşılaştırma için
gösterilir; bu ekranda yayın üzerinde yeni tespit çizilmez. Eşleme yokken
gizlenir. Yayın eşlemesi doğrulanmadığı için sahiplik birleştirmesi kapalıdır.
X, duran oyun etiketi değildir; D ve uçuş boyunca pas sahipliği bu ilk kuralda yoktur.

## Ayarlar ve çalışma

Daha önce dış veride tamamlanmış **native** RF-DETR Nano koşusunun ayarları
kullanılır. Önceki iki saniyelik gösterim SAHI modundaydı; bu uzun sürümün
native seçimi işleme maliyeti içindir, Barcelona başarısıyla model/ayar
seçimi değildir. Ağırlık, güven eşiği ve sahiplik/top takip planları korunur.
Çalışma grafiği float32 TorchScript ile derlenir; eğitim yapılmaz.

CPU'da başlayıp GPU hazır olunca kapalı parça sınırında devam edilebilir.
İzleyici/kimlik/kontrol geçmişi yalnız yerel, kendi üretilmiş ve hash'i
doğrulanan checkpoint'ten taşınır. Yeni runtime ayrı kaydedilir. CPU/GPU
çıktıları bit düzeyinde özdeş diye sunulmaz. GPU bağımlılıkları ayrı ortamda
kurulur; önceki ortam ve model kaynakları değiştirilmez.

Kaynak/ayar/kod hash'leri çözmeden önce kaydedilir; işlem ve devam etme
aşamalarında denetlenir. Kare düzeyinde sahiplik/tespit CSV veya JSON'u
üretilmez. Çizimli videolar, sunum eşlemesi, yapısal durum ve gerekirse
yerel devam checkpoint'i izole inceleme dizinindedir. Bunlar geliştirme,
eğitim, ayar seçimi veya referans etiket değildir; görüntüler dış servise
aktarılmaz. Kullanıcı arayüzünde düzeltme/etiket kaydetme işlemi yoktur.

Kaynaklar: `tools/visual_long_review.py`, `tools/visual_review_server.py`,
`viewer/long-visual.html`. Özel çalışma dizini:
`C:/Users/Abra/FootballPrivate/local-view-only-20261106/barcelona-first-five-v5`.
Tamamlanma yalnız `complete.json` ve `status.json` içindeki `complete=true`
ile, çıktı kare/süre kontrolleri sonrası doğrulanır.

## Tamamlanan yerel gösterim

7 Kasım'da tek kesintisiz GPU koşusu tamamlandı: 7.500 çözülebilen çıktı karesi,
25 FPS, 300 saniye, 1280×720. Bütün çıktı PTS'leri sıra sıra kontrol edildi;
30 parçadan birleştirilen tek videoda boşluk/tekrar kare zamanı bulunmadı.
Bu video yapısı kontrolüdür, sahiplik doğruluğu değerlendirmesi değildir.
Tamamlanınca ekran tek parça beş dakikalık dosyayı varsayılan açar.

İlk CPU denemesi 150 saniyelik hazır parçadan sonra cihaz değiştirme
checkpoint'inde durdu. Son gösterim bu parçaların devamı veya CPU/GPU karışımı
değildir; GPU'da baştan işlenen tek takip geçmişidir. ByteTrack'in kullanımdan
kaldırma sarmalayıcısı nedeniyle sınıf nesnesi yerine durum sözlüğü kaydetme
düzeltmesi yapıldı ve gerçek ByteTrack durumuyla sentetik round-trip testi geçti.
Eski deneme ve hata kaydı özel inceleme alanında ayrı korunur.

Kaynak test paketi 205 testten 203 başarılı, 2 isteğe bağlı AV atlamasıyla
tamamlandı; görüntü ortamında altı uzun-inceleme testi (gerçek ByteTrack durum
taşıma ve video birleştirme dahil) ayrıca geçti. Donmuş model hash'i korundu.
Son çalışma cihaz/sürüm bilgisi, görüntü paylaşımı yapılmadığı ve varsayım
görünümü olduğu `registration.json` / `final-verification.json` içinde kayıtlıdır.
