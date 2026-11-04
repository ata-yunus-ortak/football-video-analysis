# Temiz geliştirme — 4 Kasım 2026

Çalışma dalı: `develop/dead-ball-data-audit`.
Karşılaştırma kaynağı: `main`, başlangıç commit'i `8962134`.

`model.json` ve `clean_model/` içindeki dondurulmuş H/A/X kaynakları korunur.
Yeni deney kodları `development/`, veri edinme ve kapsam inceleme araçları
`tools/` altındadır. Bu ilk çalışma D sınıflandırıcısı seçmez veya teslim
modelini değiştirmez.

İlk çalıştırmanın bulguları ve seçim yapılmamasının gerekçesi
[deney kaydında](DENEY_KAYDI_TR.md) bulunur.

## İlk geliştirme: duran top veri kapsamı

Kayıt: `dead-ball-data-plan.json`. Kaynak, Metrica Sports'un kamuya açık
iki anonim örnek maçıdır. Sabit commit ve dosya Git blob kimlikleri kayıtlıdır.
Maç 1 eğitim/kalibrasyon, Maç 2 doğrulama olarak indirmeden önce ayrılmıştır.
Önceki erişim geçmişleri doğrulanmadığından hiçbiri dokunulmamış test verisi
diye adlandırılmaz. Kaynak, kamuya açık kullanımda Metrica Sports'a atıf ister;
ayrı bir lisans dosyası bulunmadığı için ham verilerin sonraki dağıtım koşulları
ayrıca kontrol edilmelidir.

Her indirme boyut ve Git blob kimliğiyle doğrulanır; ayrıca SHA-256 manifesti
üretilir. Ham veriler ve kare düzeyindeki çıktılar kaynak deposunun dışında
kalır. Sağlanan yarışma maçı, onun görüntüleri/elle etiketleri ve public skorları
bu araçların girdisi değildir.

Özellikler: topun saha çizgilerine işaretli uzaklığı, gözlenen top merkezi için
saha dışı durumu, ardışık gözlemlerden top/oyuncu hızları, topun kayıp kaldığı
süre, kesintisiz gözlenen saha dışı süre, gözlenen çıkış ve dönüş adımları.
Devre sınırları süre ve hareket bağlarını keser. Kayıp ölçümler enterpole
edilmez; kayıp topun ardından gelen iç saha noktası tek başına dönüş sayılmaz.
CSV'nin sonlu koordinatları bağımsız görüntü tespit güveni anlamına gelmez.
Bu özelliklerde sınıflandırma için seçilmiş bir hız/bekleme/mesafe eşiği yoktur.

`BALL OUT` olayının son karesinden sonraki kareyle başlayıp, aynı devredeki
uygun `SET PIECE` olayının başlangıç karesinden önce biten aralıklar yalnız
**olaylardan türetilmiş aday duruş aralıklarıdır**. Araya kaydedilmiş canlı oyun
veya başka bir çıkış girerse eşleştirme reddedilir. Tekrar alınan başlangıçlar,
eşleşmeyen çıkışlar ve faul/avantaj durumları doldurulmaz. Bunlar eksiksiz,
kare kare doğrulanmış D etiketleri değildir. Geri kalan kareler canlı oyun veya
D kabul edilmez. X sahiplik etiketi hiçbir aşamada D'ye çevrilmez.

## Tekrarlama

Python 3.10+ ve mevcut `requirements.txt` yeterlidir. Her `--out` yeni bir
dizin olmalı ve kaynak deposunun dışında bulunmalıdır. İndirme yaklaşık
128 MB'dir; kare düzeyindeki hazırlanmış dosyalar için ek alan gerekir.

```powershell
python -m tools.metrica_data --plan dead-ball-data-plan.json --out C:/Users/Abra/FootballPrivate/dead-ball-development-20261104/metrica-coverage-v1
python -m tools.dead_ball_audit --data C:/Users/Abra/FootballPrivate/dead-ball-development-20261104/metrica-coverage-v1 --out C:/Users/Abra/FootballPrivate/dead-ball-development-20261104/audit-v1
python -m unittest discover -s tests -v
```

İndirme öncesindeki plan kaydı `before-access.json`, ham dosya kimlikleri
`download-manifest.json`, kapsam raporu `report.json` dosyasındadır.
Hazırlanan `inputs.npz` ve `features.npz`, aday olay aralıklarından ayrı
saklanır. Özellik çıkarıcı etiket/olay alanlarını girdi olarak reddeder.
Deney kaynaklarının hash'leri ve temel model hash'i rapora yazılır; temel
model kaynakları işlem öncesi ve sonrası doğrulanır.

## D sürümüne geçiş koşulları

1. Başka maçlarda D ve canlı oyun hedeflerinin kapsamını ve başlangıç/bitiş
   zamanlarının anlamını doğrula. Fauller, eksik başlangıçlar, tekrarlar ve
   görüntü/top kaybının D sayılmadığı negatif örnekler kapsanmalı.
2. Eğitim maçlarında aday ayarları üret; maç bazında ayrılmış doğrulama
   verisinde D duyarlılığı/kesinliği ve aralık/sınır hatalarıyla karşılaştır.
   Yalnız pozitif duruş aralıklarındaki başarı seçim için yeterli değildir.
3. Top güvenilirliğini ve sahiplik geçişlerini ayrı deneyler olarak incele;
   D katmanıyla aynı anda değiştirerek etki kaynağını karıştırma.
4. Veri/split/ayar/seçim gerekçesi ve kaynak hash'lerini kaydet; seçilen
   sürümü dondur. Ardından tam maçı otomatik üret ve biçimini doğrula.
   Sağlanan public bölüm yalnız dondurma sonrasındaki son kontrolde kullanılabilir;
   bu kontrol yeniden seçim döngüsü başlatmaz.

Sağlayıcı/sohbet temizliğinin tamamlandığı doğrulanmış değildir. Bu geliştirme
kaydı organizatör şartlarının tümünün tamamlandığı anlamına gelmez.

Kaynaklar: [Metrica Sports Sample Data](https://github.com/metrica-sports/sample-data),
[sabit sürüm](https://github.com/metrica-sports/sample-data/tree/e706dd506b360d69d9d123d5b8026e7294b13996).
