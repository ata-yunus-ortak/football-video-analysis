# Tracking destekli top adayı — 7 Kasım 2026

`development/ball_tracking_support.py` mevcut görüntü ve zamansal top takip
çıktısını değiştirmeden ek ilişkilendirme kanıtı üretir.
`tools/ball_support_experiment.py` kayıtlı dış/sentetik koşuların giriş noktasıdır.
Donmuş sahiplik modeline bağlanmadı; doğrulukla seçilmiş sürüm değildir.

## Kabul ve ret

Yalnız mevcut karede tespit edilmiş, zamansal olarak onaylanmış top adayları
değerlendirilir. Tahminler ve henüz onaylanmamış izler seçilemez. Otomatik
tracking'in kaynak, kare, kamera epoch'u ve video zamanı bağlanır. Ara değerleme
veya tahmin ölçüm gibi kabul edilmez. Canlı görüntü, zaman eşlemesi/hata sınırı,
kalibrasyon ve topun zemin düzlemine uygunluğu ayrıca doğrulanmış olmalıdır.

`project_ground_ball` metre -> normalize saha -> görüntü dönüşümünü sağlar.
Çağıran adaptör eksen/saha başlangıcını açıkça ortaklaştırmalıdır; merkezli
koordinat tahmin edilmez. Tekil/geçersiz matris kullanılmaz. Havadaki veya zemin
durumu bilinmeyen top için zemin homografisinden seçim yapılmaz.

Görüntü köşegenine göre yakınlık ve ikinci adaydan ayrışma aranır. Yakın iki
adayda belirsiz, büyük uyuşmazlıkta reddedilmiş sonuç çıkar. Parametreler
`ball-support-plan.json` içinde sentetik mühendislik değerleridir; futbol
başarısıyla veya yarışma maçında seçilmedi.

`supported_candidate` oyundaki topun doğrulandığı anlamına gelmez.
`selected_in_play_ball=false`, `fusion_eligible=false`, sahiplik bilinmiyor kalır.
Ham tespit, koordinat ve izler korunur; yeni ölçüm uydurulmaz.

## İkinci kamera

Yayın kendi native zamanında aynı kontrollerden geçer. Kaynak/kare/epoch çiftini
ve hata sınırını doğrulayan otomatik eşleme gerekir. İki kamera aynı tracking
örneğini gözlenmiş adaylarla desteklerse `corroborated_candidate` raporlanır.
Bir kamera reddedilirse bu onay yoktur; birincilin ayrı kanıtı korunur.
Piksel koordinatları farklı kameralar arasında doğrudan karşılaştırılmaz.

Bu modül canlı/tekrar sınıflandırıcısını, saha düzlemi doğrulayıcısını veya zaman
eşleme doğrulamasını üretmez; bunların doğrulanmış kanıtını ister. Bayrakların
varlığı bu araç tarafından bağımsız doğruluk kanıtı üretilmesi değildir.
İki görüntünün ortak tracking'i desteklemesi bağımsız gerçek etiket değildir;
özellikle aynı görüntüden türetilmiş kaynakların hataları ilişkili olabilir.

## Kullanma

```powershell
python -m tools.ball_support_experiment --analysis C:/private/temporal-analysis --plan ball-support-plan.json --out C:/private/support-off
python -m tools.ball_support_experiment --analysis C:/private/temporal-analysis --plan ball-support-plan.json --support-registration C:/private/automatic-support.json --out C:/private/support-on
```

İkinci komuta `--secondary-run C:/private/broadcast-support-on` ve
`--pair-alignment C:/private/verified-pairs.jsonl` birlikte eklenebilir.

Destek kayıt JSON'u: `origin=automatic_tracking`, `provided_fixture_used=false`,
`reference_annotations_as_inputs=false`, aynı `fixture_id`, mutlak
`tracking_path`, `tracking_sha256`, `projections_path`, `projections_sha256`.
Projeksiyon JSONL satırları modüldeki `HINT_FIELDS` sözleşmesini kullanır ve
kayıtlı tracking hash'ine bağlanır. Kamera eşleme satırları `cross_check`
sözleşmesini kullanır. İlk sürüm kaynaklandırılmış projeksiyonları kabul eder;
rastgele sağlayıcı TXT/XML şemalarını otomatik tahmin edip dönüştürmez.
Gerçek sağlayıcı adaptörü ve doğrulanmış geometri/zaman kanıtı ayrıca gerekir.

Koşucu girdi/plan/kod hash'lerini işlem öncesi kaydeder. Değişmiş girdi, farklı
maç, eksik kare, yinelenen destek veya kullanılmayan eşleme başarı raporunu
engeller. Çıktı yeni ve depo dışında olmalıdır. Referans etiket yükleyicisi yoktur.

## Sonuç ve sınır

12 yeni test destek açık/kapalı, iki kamera, yanlış kaynak/zaman, tekrar,
havadaki top, belirsizlik, tahmin/ölçüm ayrımı ve kaynak bütünlüğünü kapsıyor.
Toplam 178 testten 177'si geçti; isteğe bağlı AV testi atlandı.

Önceden görülen üç dış kaynak maçın sekiz eğitim kesiti native/SAHI iki modda
1.200 çıktı karesiyle işlendi. Eski görüntü/iz alanları aynen korundu. Bağımsız
otomatik tracking mevcut olmadığından tamamı `no_automatic_tracking` oldu.
Bu gerçek destek açık/kapalı doğruluk karşılaştırması veya başarı artışı değildir.
Referans kutuları tracking yapılmadı; yarışma maçı açılmadı.

Özel kayıt: `C:/Users/Abra/FootballPrivate/ball-support-development-20261107`.
Sıradaki veri: eşzamanlı dış video + otomatik tracking/homografi. Ölçülecekler:
doğru aday kesinliği, görünür topu yakalama, kayıp/geri bulma süreleri, yanlış
aday değişimi, destek kapsamı ve retler. Referanslar yalnız tahminler
dondurulduktan sonra değerlendirmede kullanılmalı. Düşük kapsamla görünen
iyileşme tek başına yeterli değildir.

## Sonraki aşama: görüntüyle duran oyun sınırları

SET PIECES / throw-in / goal-kick / free-kick / corner / kick-off tag'leri
arama aralığını daraltsın; tag'in tamamı D yapılmasın. Görüntüde oyuna sokma,
top/oyuncu hareketi ve görünürlükten ayrı `stop_candidate` ve `restart_candidate`
sınırları çıkarılacak. Sabit top canlı oyunda da vardır; tek başına duruş değildir.
Top kaybı, tekrar veya kamera kesmesi duruş başlangıcı sayılmayacak. Faul/avantaj
ve görünmeyen başlangıç çözülemiyorsa kesin kare uydurulmayacak.

Sınırlar belirsizlik aralığı ve kanıt kaynağıyla saklanacak. Başka maçlarda D,
canlı oyun ve sınır doğruluğu değerlendirildikten sonra sahipliğe alınacak.
Bu çalışmada D kararı veya yeni D modeli eklenmedi.
