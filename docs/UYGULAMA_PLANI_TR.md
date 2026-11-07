# Sahiplik, görüntü ve iki video: uygulama planı

7 Kasım güncellemesi: kullanıcının istediği karar düzeni için ayrı görüntü
temelli sahiplik yolu eklendi. Tracking yalnız oyuncu kimliği/takımı sağlar;
top ve kontrol görüntü ölçümlerinden gelir. Doğrulanmış yayın tercihi ve taktik
geri dönüşü uygulanır. Çalışan sözleşme, deneyler ve gerçek doğrulama eksikleri
[görüntü temelli sahiplik rehberindedir](GORUNTU_TEMELLI_SAHIPLIK_TR.md).
Bu, aşağıdaki tracking tabanlı hibrit hareket prototipinden ayrı giriş noktasıdır.

Başlangıç: 5 Kasım 2026. Çalışma dalı: `feature/reachability-vision`.
Amaç, güvenilir otomatik gözlemlerden daha iyi sahiplik aralıkları üretmek.
Yeni katmanlar deneysel; donmuş `clean_model/` ve `model.json` karşılaştırma
modeli olarak korunur. Bir modülün çalışması, doğruluğunun kanıtlandığı veya
teslim sürümüne seçildiği anlamına gelmez.

## 1. Topa erişim süresi — uygulandı

`development/reachability.py` oyuncunun konumunu ve ölçülmüş hız vektörünü
kullanır. Basit tahmin:

```
tepki_sonrasi_konum = konum + hiz_vektoru * tepki_suresi
erisim_suresi = tepki_suresi + mesafe(tepki_sonrasi_konum, top) / kosu_hizi
```

Bu, gelecekteki erişim için bir model varsayımıdır; gözlenmiş temas veya
kalibre edilmiş sahiplik olasılığı değildir. Hızın yönü sonucu değiştirir.
Eşiğe bağlı bütün sayılar açık yapılandırmadan gelir; seçilmiş futbol
parametresi diye yerleşik varsayılan kullanılmaz.

İlk entegrasyon bilinçli olarak dar tutuldu: topun hareket değişiminden
zaten çıkarılmış bir temas adayında, mesafe farkı yetersizse erişim süresi
adayları ayırabilir. İki aday da mevcut temas yarıçapında olmalı; zaman farkı,
zaman ufku ve iki takımın gözlem kapsamı yeterli olmalıdır. Açık mesafe
kanıtını geçersiz kılmaz. Tek başına topa yaklaşan oyuncuya sahiplik vermez.

Kayıp hız sıfır yapılmaz. Kayıp gözlem, devre sınırı ve fiziksel olarak
olanaksız oyuncu adımı hız bağını keser. Gözlenmeyen/saha dışı/güvenilmez
top için süre kanıtı yoktur. D kararı üretmez. Uzun topun yakınından
geçmeyi temas saymaz. Temaslar ve bunlardan çıkan paslar hâlâ adaydır.

Bağlantı: `development/motion_possession.py` içindeki
`reachability_config`; koşucu: `tools/motion_experiment.py` içindeki
`reachability_parameters`. Çıktıda oyuncu/takım süreleri, gözlem sayıları ve
temasın hangi kanıttan geldiği saklanır.

Referans yaklaşım:
[Friends of Tracking / LaurieOnTracking](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/tree/7ed3ff857940d3f4611be55f3c08c79525c32171),
MIT. Olaydan sahiplik takımını okuyan örnek yardımcısı kullanılmadı. Buradaki
uygulama iki takımı simetrik ele alır; etiket/olay girdi olarak kabul edilmez.

Doğrulama: yön, eşit aday, veri kaybı, sıçrama, takım/koordinat simetrisi ve
10/25 FPS birim aktarımı sentetik testlerde kontrol edildi. Kayıtlı iki dış
Metrica maçında toplam **286.162 kare** uçtan uca işlendi; erişim süresi
10 belirsiz temas adayını ayırdı. Bu sayı doğru temas/sahiplik sayısı veya
başarı artışı değildir. Sayılar sentetik test ayarlarıdır; eşik seçimi ve
bağımsız gerçek sahiplik doğrulaması yapılmadı. Otomatik tag kullanılmadı.

## 2. Yerel görüntü ölçümü — ilk uygulama hazır

`development/vision.py` ve `tools/vision_experiment.py`:

- RF-DETR Nano veya Small ile görüntü tespiti.
- SAHI ile dilimleme açık/kapalı karşılaştırması.
- Supervision'ın MIT lisanslı ByteTrack uygulamasıyla yalnız kişi takibi.
- İlk çözülen kareye sıfırlanmış video sunum zamanları (PTS), kaynak kare, kutu, sınıf, güven puanı ve
  iz kimliği kaydı. Tespit olmayan kare de kayıtta kalır.
- Takibi henüz doğrulanmamış kişi tespitleri kaybolmaz; iz kimliği bilinmiyor
  olarak kalır. Bütün top adayları saklanır. Kişi sınıfı doğrudan futbolcu veya
  takım demek değildir. Bu aşama sahiplik çıktısı üretmez.

`requirements-vision.txt` ayrı ortama kurulur. Ana numpy-only ortam ve donmuş
gereksinimler değiştirilmez. Nano/Small dışındaki farklı ağırlık lisanslı
boyutlar yükleyiciye dahil değildir. `tools/vision_weights.py` resmî kaynağı,
yayımlanmış varlık özeti ve indirilen SHA-256 ile kaydeder.

Kurulum sürümleri API uyumluluğunu sınamak içindir, futbol başarısına göre
seçilmiş sürümler değildir. Supervision 0.29.0'da ByteTrack mevcuttur; sonraki
API'deki taşıma nedeniyle bu sürüm açıkça sabitlendi. Ayrı bir taşımayı aynı
başarı deneyiyle karıştırmayacağız.

İşlem sırası: ortam kurulumu → yapay videoda model yükleme/PTS/dilimleme ve
izleyici çalışma kontrolü → izinli dış maçlarda gerçek tespit değerlendirmesi.
CPU/GPU çalışma kontrolü ile futbol doğruluğu ayrı kaydedilecek. Yerel kart
4 GB GTX 1650 Ti; mevcut genel PyTorch CPU sürümüdür. GPU kullanılabilirliği
ayrı doğrulanacak; kurulumla otomatik sürücü değişikliği yapılmaz.

İlk çalışma kontrolü tamamlandı: resmî Nano ağırlığı yayımlanan MD5 ve yerel
SHA-256 ile doğrulandı; ayrı CPU ortamında native iki kare, SAHI bir kare ve
yapay kutu dizisinde ByteTrack iz sürekliliği çalıştı. Ortamın bağımlılık
kontrolü geçti. Futbol doğruluğu ölçülmedi. 66 kurulu paket sürümü
`requirements-vision-lock.txt` içinde kayıtlıdır.

Sonra izinli dış eğitim maçı SoccerTrack 117092'nin önceden belirlenen ilk
10 karesi de işlendi. İlk kareler, kaynak MP4'nin gerekli byte aralıklarından
alınıp RGB değerleri tek tek doğrulanmış kayıpsız klibe dönüştürüldü. Native
10 kare, SAHI 2 kare üzerinde çalıştı. Bunlar küçük çalışma kontrolleridir;
bağımsız doğruluk, model seçimi veya temsil edici hız testi değildir.
91 birim/entegrasyon testi geçti; donmuş çıkarım kaynakları korundu.

Windows/Python 3.10 CPU çalışma kontrolünü tekrar etmek için:

```powershell
python -m venv .venv-vision
.\.venv-vision\Scripts\python -m pip install --upgrade pip
.\.venv-vision\Scripts\python -m pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv-vision\Scripts\python -m pip install -r requirements-vision-lock.txt
python -m tools.vision_weights --size nano --out C:/private/vision/nano
.\.venv-vision\Scripts\python -m tools.vision_smoke --weights-manifest C:/private/vision/nano/manifest.json --out C:/private/vision/smoke-v1
```

Çıktı dizinleri yeni olmalı ve kaynak deposunun dışında kalmalıdır. Genel
deney koşucusu `python -m tools.vision_experiment --help`; gerçek dış video
çalıştırması kaynak/izin/video hash'i, ağırlık hash'i ve açık parametreler
içeren ön kayıt ister. Bu komutlar sağlanan maç üzerinde ayar seçmez.

## 3. Görüntüyü tracking'e bağlama — ilk ölçüm adaptörü hazır

`development/vision_measurements.py` ilk ölçüm adaptörünü ekler. Kutular,
ayak/top merkezi adayları ve kesintisiz kişi izlerinin piksel hızları
kaydedilir. Görüntü değişimi/kare kaybında izleyici sıfırlanır; kamera epoch'u
aynı sayısal iz ID'sinin farklı görüntülerde karışmasını önler. Aynı kaynak
homografisi verilirse kişi ayak noktası saha metre adayına çevrilir; topun
zemin/yüksekliği ve gerçek kalibrasyon doğrulanmış sayılmaz. Yerel kutulu
video üretimi ve son dış çalışma [görüntü rehberinde](GORUNTU_ISLEME_TR.md).

Önce aynı kaynak içindeki zaman/koordinat eşleşmesi doğrulanır. Oyuncu için
kutunun alt orta noktası, homografiyle zemin temas noktası adayı olabilir.
Matrisin yönü, birimi, ilgili karesi ve geçerliliği kontrol edilir. `vision.py`
zemin izdüşümü için yardımcı hesap içerir. `development/homography.py`
kaynak CSV'nin sıfır tabanlı karelerini ve normalize saha → görüntü pikseli
yönünü okur; ters dönüşümde saha metre ölçeğini açıkça uygular. Geçersiz,
eksik ve tekil matrisleri kullanmaz; aralarını doldurmaz. Adaptör sentetik
geometriyle sınandı; gerçek kamera/geometri doğrulaması henüz tamamlanmadı.

Topun görüntü merkezi için aynı düzlem varsayımı havada hatalıdır. Homografi
tek başına top yüksekliği veya gerçek zemin izdüşümü üretmez. Görüntü kanıtı,
tracking ölçümü ve model tahmini ayrı tutulmalı; çelişkili kaynaklar körlemesine
ortalama alınmamalıdır. Güven düşükken belirsizlik korunur.

Takım görünümü gerekiyorsa Sports/SigLIP sınıflandırması ayrıca denenecek.
Küme numarası ev/deplasman etiketi değildir; takım eşleştirmesi doğrulanmadan
görsel oyuncu izi sahiplik takımına dönüştürülmez. Bu bileşen henüz kurulmadı.

## 4. Taktik ve yayın videosu — ayrı zaman çizgileri

Taktik video ana çıktı eksenidir. Yayın yakın çekimleri, bazı temaslarda daha
ayrıntılı görsel kanıt sağlayabilir; kadraj dışında kalan oyuncular için
kapsama sağlamaz. Her kaydın kendi ATD ve homografi dosyası kullanılır.

[Organizatör FAQ](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/FAQ.md#can-i-use-the-broadcast-video-and-its-tracking)
yayının kesmeler/tekrarlar nedeniyle ayrı zaman çizgisinde olduğunu ve hazır
eşleme verilmediğini açıkça belirtir. Sabit başlangıç farkı yeterli değildir.

Uygulama sırası:

1. İki videonun dosya kimliği, kare/zaman bilgisi ve devre kapsamını kaydet.
2. Yerel otomatik saat okumasından devre ve maç saati adaylarını çıkar.
   Normal süre/uzatma, saat görünmemesi ve düşük okuma güveni ele alınmalı.
3. Saat aynı saniyedeki aday aralığı daraltsın. Tek saniye birden çok kare
   içerir; OCR sonucu kesin kare eşlemesi sayılmasın.
4. Tekrar, donmuş saat ve kesinti durumlarında birden çok aday varsa çözülmüş
   sayma. Saat ilerleyen bir tekrar da olabilir; saatin tek görünmesi yeterli
   değildir. Yerel top/oyuncu geometrisinin ve ardışık hareketin tutarlılığıyla
   canlı eşleşmeyi ayrıca doğrula.
5. Yalnız doğrulanan aralıkta, eşleme belirsizliği yeterince küçükse görüntü
   kanıtını ana eksene taşı. Doğrulanmayan aralığı kullanma. İki kameradaki
   iz numaralarını aynı kişi numarası kabul etme.

`development/video_sync.py` ilk saat adayı modülüdür. Yeni
`tools/clock_observations.py` yerel otomatik saat okuyucusunu,
`development/clock_alignment.py` saat dizileri ve oyuncu konumlarından
geometrik destek aramasını, `tools/sync_alignment.py` kaynak kayıtlı eşleme
koşucusunu sağlar. `ESLESME-IZLE.cmd` iki video ve ayrı tracking görünümlerini
eşleme adaylarıyla açar. Hiçbir bağlantı sahiplik birleştirmesi için hazır
işaretlenmez. Gerçek kare doğruluğu ve kısa tekrarları yakalama henüz başka
maçlarda bağımsız doğrulanmadı; mevcut çıktı deneysel inceleme içindir.
Ayrıntılar: [otomatik eşleme rehberi](ESLESTIRME_TR.md).

6 Kasım'da yayın MP4 İndirilenler'e geldi: 1920×1080, 25 FPS, 6.579,48 sn,
164.487 video karesi. Yayın ATD ve homografi 164.488 kayıt içeriyor. Üç
yardımcı dosya resmî Drive klasöründen yeniden indirildi; SHA-256 değerleri
mevcut yerel paketle birebir eşleşti. MP4'ün tamamının SHA-256'sı ve son
paket zamanları görüntü karesi çözülmeden kaydedildi. Bu biçim/bütünlük
kontrolüdür; görsel eşleşme veya tespit doğruluğu kanıtı değildir.

`YAYIN-IZLE.cmd` kendi yayın TXT/XML/CSV ve videosunu 8767 portunda salt
okunur açar. Eşleme ortak kare sayısıyla sınırlıdır; eşleme kapalıyken son
tracking kaydı korunur. Taktik Smart Tags yayın saatine kopyalanmaz.
Bu entegrasyon iki kamera eşlemesini veya sahiplikte görüntü kullanımını
tamamlamaz; top/oyuncu görüntü modeli bu maç üzerinde çalıştırılmadı/seçilmedi.

## 5. Karşılaştırma, seçim ve teslim

Taktik öncelikli kaynak seçimi `development/hybrid_tracking.py` ve
`development/hybrid_pipeline.py` ile mevcut hareket akışına bağlandı.
Doğrulanmış zaman/görünürlük/kalibrasyon ve yeterli oyuncu uyumu varsa uygun
yayın ölçümleri tercih edilir; diğerleri taktikten kalır. Tekrar, dar kadraj,
toplu sıçrama veya çelişkide yayın kapatılır; kaynak geçişleri hareket bağı
oluşturmaz. Şimdilik sentetik ve kontrollü dış tracking senaryolarında
sınanmıştır; gerçek çift kamera doğrulaması yapılmadı. İnceleme eşlemeleri
nihai sahipliğe açılmaz. [Katman sözleşmesi](HIBRIT_KAYNAK_POLITIKASI_TR.md),
sonraki görüntü işleme adımının sağlaması gereken kanıtları açıklar.

Her katman aynı dış maçlarda kendisi kapalı sürümle karşılaştırılacak:
erişim süresi, görüntü, dilimleme, takım görünümü ve ikinci kamera ayrı deneyler.
Maçlar eğitim/ayar ve doğrulama olarak ayrılacak; rastgele kare veya aynı maçın
farklı kamerası bağımsız maç testi sayılmayacak.

Top tespitinde konum hatası/kayıp/yanlış aday; oyuncuda iz değişimi/takım hatası;
sahiplikte spellF1 ve geçiş sınırları; ayrıca süre/bellek ve eşleme hatası
ölçülecek. Veri/etiket/video hakları ve organizatör erişimi kaydedilecek.
Mevcut Metrica örnekleri çalışma kontrolünü sağlar; eksiksiz D gerçeği veya
eşzamanlı görüntü doğrulama paketi diye sunulamaz.

Bir sonraki görüntü veri adayı
[SoccerTrack v2](https://huggingface.co/datasets/atomscott/soccertrack-v2),
yayımlanan veri lisansı CC BY 4.0. Tam paket yerine önce kısa MOT kliplerinin
ve referanslarının kapsamı incelenecek. Maç içeriği açılmadan önce kaynak,
önerilen maç ayrımı ve sınırlamalar [veri planına](../vision-data-plan.json)
kaydedildi. Hugging Face dosya erişimi oturum/koşul kabulü gerektiriyor.
Sağlayıcının aynı proje sayfasında yayımladığı Google Drive alternatifi
erişilebilir bulundu. İlk eğitim maçı 117092'nin kısa MOT klibi ve referansı
için dosya kimlikleri/boyutları içerik indirilmeden kaydedildi. Drive kopyası
Hugging Face v1.2 ile özdeş varsayılmıyor; gerçek dosyaların sözleşmesi ayrıca
incelenecek. Veri atfı: Atom Scott ve arkadaşları, SoccerTrack v2 (2025),
CC BY 4.0; [kaynak ve makale](https://github.com/AtomScott/SoccerTrack-v2),
[veri lisansı](https://github.com/AtomScott/SoccerTrack-v2/blob/a752d294df2a0e816e827b70f284980698f5a50e/LICENSE-DATA).

Erişimin devamında Google Drive indirme kotası yanıtı verdi; başka istekle
aşılmaya çalışılmadı. Tam kaynak klip ve tam referans edinilmedi. Yalnız ilk
10 karelik kayıpsız örnek ve önceden alınan 2.048 byte referans şema örneği var.
Bu örnekteki 46 tam satırda kareler 0'dan başlıyor; conf/class alanları -1.
Bu, güncel belgede anlatılan 1 tabanlı GT sözleşmesiyle farklı. Alanlar yeniden
yorumlanmadı ve doğruluk skoru üretilmedi. Tam referans erişimi/şema ve
zaman eşlemesi doğrulanana kadar veri adayı model seçimi için hazır değildir.

Önemli sınır: kaynağın `ball/` dizisi olay noktalarından doğrusal hızla yeniden
kurulmuş; bağımsız ölçülmüş top gerçeği değildir ve olay zamanını taşır. Bunu
girdi yapıp aynı olaylara karşı temas başarısı ölçülmeyecek. GSR şema/görüntü
boyutu uyumsuzluğu uyarıları da var. Gerçek dosya/çözülmüş video kontrolü
yapılmadan bu aday doğrulanmış eğitim veya tam sahiplik/D gerçeği sayılmaz.
Kaynaklar: [veri kartı](https://huggingface.co/datasets/atomscott/soccertrack-v2),
[şema uyarıları](https://github.com/AtomScott/SoccerTrack-v2/blob/a752d294df2a0e816e827b70f284980698f5a50e/docs/format-gsr.md).

Katkı göstermeyen bileşen alınmayacak. Seçilen yapılandırma, kaynak/ağırlık
hash'leri ve bağımlılıklar dondurulduktan sonra tam yarışma maçı otomatik
işlenecek. Public pencere bu işlem sonrası son kontrol içindir; yeniden ayar
seçimi başlatmaz. Sağlayıcı temizliğiyle ilgili bekleyen durum ayrıca korunur.
