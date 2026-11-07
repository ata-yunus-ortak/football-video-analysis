# Görüntü analizi için açık kaynak adayları

İnceleme tarihi: **5 Kasım 2026**. Bu belge bir kaynak/lisans incelemesi ve
deney önerisidir. Yeni bir teslim modeli seçilmiş veya doğrulanmış değildir.
İncelenen 12 deponun sabit commit ve dosya SHA-256 kayıtları
[kaynak kaydındadır](vision-source-review.json). Sonraki kod/kurulum ilerleyişi
[uygulama planında](UYGULAMA_PLANI_TR.md) izlenir.

## Önerilen başlangıç

**RF-DETR Nano/Small + SAHI + ByteTrack** ilk dış maç karşılaştırmasının
adaylarıdır. RF-DETR görüntüde oyuncu/top adayları üretir; SAHI küçük topu
aramak için görüntüyü parçalara ayırır; ByteTrack oyuncu tespitlerini zaman
boyunca eşleştirir. Forma üzerinden takım ayrımı için Roboflow Sports'un
TeamClassifier bileşeni ayrıca değerlendirilebilir.

Top için **WASB-SBDT** özel bir karşılaştırma adayıdır. Futbola ait yayımlanmış
sonucu vardır; ayrı indirilen ağırlıkların koşulları netleştirilmeden hazır
checkpoint kullanımı onaylanmış sayılmamalıdır.

Bu öneri araştırma önceliğidir. Gerçek model/sürüm, eşik ve yöntem seçimi,
izinli başka maçlarda yapılacak deneyden sonra kaydedilir.

5 Kasım literatür kontrolü, dedektör/takip önerisini değiştirmedi. Aşağıdaki
[erişim süresi deneyi](#dar-kapsamlı-ek-deney-oyuncunun-topa-erişim-süresi)
tek yeni araştırma maddesidir. Ardından deneysel temas katmanına bağlandı;
seçilmiş bir teslim kuralı değildir.

## Adaylar ve kullanım kapsamı

### 1. RF-DETR — ilk genel tespit adayı

- [Resmî depo](https://github.com/roboflow/rf-detr).
- [Kod ve ağırlık lisanslarının resmî açıklaması](https://roboflow.com/model-licenses/rf-detr).
- **Paket ile Nano, Small, Medium, Large detection ağırlıkları Apache-2.0.**
  Atto/Femto/Pico/XL/2XL detection farklı Platform Model License koşullarındadır;
  bu incelemede başlangıç önerisine dahil değildir.
- [Yayımlanmış tablo](https://github.com/roboflow/rf-detr/blob/e8f5db605f1dbbb24bb61fbd014be29bc736d5e4/README.md#benchmarks):
  Nano COCO AP50:95 **48,4**, Small **53,0**. Bunlar geliştiricinin COCO
  ölçümleridir; futbol topu veya sahiplik başarı oranı değildir.
- Bizim kullanımımız: oyuncu ve `sports ball` adayları. Genel COCO sınıfları
  topun futbol topu, kişinin futbolcu veya hangi takım olduğu sonucunu tek
  başına vermez. Uzak/küçük top için dış maçlarda alan uyarlaması gerekebilir.
- Araştırma commit'i `e8f5db605f1dbbb24bb61fbd014be29bc736d5e4`.
  `develop` snapshot'ı kurulum sürümü diye seçilmedi; kurulumda kararlı sürüm,
  checkpoint hash'i ve bağımlılıklar ayrıca sabitlenecek.

### 2. SAHI — küçük top için görüntü dilimleme

- [Depo](https://github.com/obss/sahi),
  [MIT lisansı](https://github.com/obss/sahi/blob/10061afd5fa076e00f8eda55e2ee290f9d72f3c1/LICENSE).
- Bir dedektör değildir. Büyük görüntüyü örtüşen küçük parçalarda işler,
  sonuçları tam görüntü koordinatına taşır ve birleştirir. Küçük topun bütün
  kare küçültülürken kaybolması sorununa uygun bir adaydır.
- [İncelenen adaptör](https://github.com/obss/sahi/blob/10061afd5fa076e00f8eda55e2ee290f9d72f3c1/sahi/models/roboflow.py)
  yerel RF-DETR nesnesi/sınıfı ile çalışmayı destekler. Universe model kimliği
  kullanan ayrı yolun koşulları aynı değildir. Model adı, API ve paket sürümü
  eşleşmesi kurulumda doğrulanacak.
- Daha çok parça daha fazla işlem getirir. Futbol için doğrulanmış bir kazanç
  yüzdesi veya bilgisayarımızda gerçek zaman garantisi bu incelemede yoktur.

### 3. ByteTrack — oyuncuların iz sürekliliği

- [Depo ve yayımlanmış sonuçlar](https://github.com/FoundationVision/ByteTrack),
  [MIT lisansı](https://github.com/FoundationVision/ByteTrack/blob/d1bf0191adff59bc8fcfeaa0b33d3d1642552a99/LICENSE).
- Tespit kutularını zaman içinde eşleştiren katman. Yalnız eşleştirme kodu
  kullanılacaksa kendi sinir ağı ağırlığı gerekmez; dedektör ayrı seçilir.
- Yayımlanmış MOT17 test sonucu **80,3 MOTA / 77,3 IDF1**. Bu genel çoklu
  insan takibi sonucudur; futbol oyuncularında aynı başarı ölçülmüş değildir.
- Oyuncular çakışırken kimlik değişimini azaltmaya adaydır. Takım adını,
  oyuncunun gerçek kimliğini veya top sahipliğini kendiliğinden belirlemez.
  Ani yön değiştiren küçük top için ayrıca uygun bir hareket modeli gerekir.

### 4. Roboflow Sports + SigLIP — takım ayrımı

- [Sports deposu](https://github.com/roboflow/sports),
  [MIT lisansı](https://github.com/roboflow/sports/blob/42c80c06b6b65a7f89455b89fe31cdf4c38ba227/LICENSE).
- [TeamClassifier](https://github.com/roboflow/sports/blob/42c80c06b6b65a7f89455b89fe31cdf4c38ba227/sports/common/team.py)
  oyuncu kırpımlarından SigLIP özellikleri çıkarır; UMAP ve KMeans ile iki
  görünüm kümesi kurar. Kullanılan
  [Google SigLIP checkpoint kartı](https://huggingface.co/google/siglip-base-patch16-224)
  Apache-2.0 belirtir.
- Bizim kullanımımız: tracking'deki takım üyeliğiyle görüntü görünümünün
  tutarlılığını ölçmek. Küme 0/1 doğrudan ev/deplasman değildir. Kaleci,
  hakem, benzer forma, örtüşme ve ışık değişimi ayrıca değerlendirilmelidir.
- İncelenen kaynaklarda bizim görevimiz için sayısal takım doğruluk sonucu
  saptanmadı. Bu bir uygulanabilir yöntem adayıdır.
- **Depodaki futbol örneğinin requirements dosyasında `ultralytics` var.**
  Örneği bütünüyle MIT sayıp almak doğru değildir. TeamClassifier, bağımlılık
  lisansları incelenerek ayrı kullanılabilir; dedektörü RF-DETR seçmek önerilir.

### 5. WASB-SBDT — top için en ilgili araştırma adayı

- [Resmî depo](https://github.com/nttcom/WASB-SBDT),
  [MIT kod lisansı](https://github.com/nttcom/WASB-SBDT/blob/923462cacdeb3353b84ddebdedb3f4b7a8553b0f/LICENSE.md).
- Ardışık görüntülerden top konumu çıkarır. Oyuncu/takım/sahiplik modeli
  değildir. [BMVC 2023 makalesi, Tablo 2](https://arxiv.org/html/2311.05237)
  Soccer için Step=3 ile **88,3 F1 / 83,6 AP**, 4 piksel eşleştirme toleransı
  bildirir. Bu konum tespit ölçümüdür; top sahipliği skoru değildir.
- Önemli sınır: futbol deneyi altı senkron kamera videosunun dördünü eğitim,
  ikisini test için kullanır. Ayrı kamera, bağımsız başka maç testi anlamına
  gelmez. Bizim maçlar arası genelleme şartımızı tek başına karşılamaz.
- [Model Zoo](https://github.com/nttcom/WASB-SBDT/blob/923462cacdeb3353b84ddebdedb3f4b7a8553b0f/MODEL_ZOO.md)
  futbol ağırlığı sunar; incelenen belgelerde bu dış checkpoint için ayrı,
  açık ağırlık lisansı saptanmadı. Kodun MIT olması, veri ve bütün bağlantılı
  ağırlıklar için tamamlanmış bir izin incelemesi sayılmadı.
- [Başlangıç belgesinde](https://github.com/nttcom/WASB-SBDT/blob/923462cacdeb3353b84ddebdedb3f4b7a8553b0f/GET_STARTED.md)
  eğitim bölümü **TBA**. Hazır değerlendirme kodu var; eksiksiz eğitim sistemi
  diye sunulmamalı. Eski Python/CUDA ortamının taşınması da ek iş olabilir.

### 6. RT-DETRv2 — lisansı açık genel dedektör alternatifi

- [Orijinal uygulama](https://github.com/lyuwenyu/RT-DETR),
  [Apache-2.0 kod lisansı](https://github.com/lyuwenyu/RT-DETR/blob/df2a96c8c3a098567a1149bf0248da6efe6d495d/LICENSE).
- [PekingU/rtdetr_v2_r18vd model kartı](https://huggingface.co/PekingU/rtdetr_v2_r18vd)
  de Apache-2.0 belirtir; yaklaşık 20,2 milyon parametreli COCO modeli.
- RF-DETR'e karşı dış maçlarda bellek, süre ve tespit karşılaştırmasına uygun.
  Orijinal uygulama veya uygun lisanslı Transformers yolu kullanılmalı;
  aynı isimli Ultralytics uygulamasının lisansı otomatik olarak Apache olmaz.

## İkincil adaylar ve tercih edilmeme gerekçesi

| Kaynak | İncelenen kod lisansı | Karar |
| --- | --- | --- |
| [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) | Apache-2.0 | Olgun, Tiny/Nano seçenekli yedek dedektör. Kod ile indirilecek checkpoint koşulları ayrı kaydedilmeli. |
| [FootAndBall](https://github.com/jac99/FootAndBall) | MIT | Futbola özel oyuncu/top mimarisi; eski ortam ve checkpoint koşulları nedeniyle ikinci araştırma sırası. |
| [Supervision](https://github.com/roboflow/supervision) | MIT | Tespit nesneleri/çizim/video yardımcıları; kendi başına dedektör veya doğruluk kazancı değildir. |
| [TrackLab](https://github.com/TrackingLaboratory/tracklab) | MIT | Modüler araştırma altyapısı; bu aşamada daha fazla bağımlılık ve taşıma işi getiriyor. |
| [SoccerNet Game State](https://github.com/SoccerNet/sn-gamestate) | GPL-3.0 | Futbola çok ilgili referans sistem; MIT TrackLab lisansı bu deponun ve YOLO dahil bağımlılıklarının yerine geçmez. İlk entegrasyon önerisi değil. |

[Ultralytics'in resmî lisans açıklaması](https://www.ultralytics.com/license)
AGPL-3.0 veya Enterprise koşullarını belirtir. AGPL kullanımı yasak değildir;
dağıtım/ağ üzerinden kullanım ve türev eser yükümlülükleri sağlanmalıdır.
MIT lisanslı bir futbol örneği, içindeki Ultralytics bileşenini MIT yapmaz.
Bu nedenle başlangıç önerisi açıkça Apache/MIT olan bileşenlere öncelik verir.

## Projemize bağlama önerisi

1. Yerel video çözümü → RF-DETR → kutu/merkez, sınıf ve güven puanı.
2. Top için bütün görüntü taraması ile SAHI dilimlemeyi karşılaştır. Tracking
   ve Smart Tagging bölge bilgisini arama önceliği olarak ayrıca dene; yanlış
   tag'in gerçek topu arama dışında bırakmasını ölçmek için tam tarama koru.
3. Oyuncuları ByteTrack ile bağla; takım görünüm puanını ayrı üret.
4. Mevcut homography ile oyuncunun zemin temas noktasını saha koordinatına
   taşı; görüntü/tracking zaman eşleşmesini doğrula. Havadaki topun pikselini
   düzlem homography'siyle dönüştürmek gerçek zemin izdüşümü veya yükseklik
   vermez. Bu belirsizlik özellikle uzun toplarda korunmalı.
5. Görüntü ve mevcut tracking ölçümlerini kaynak, zaman ve güven bilgileriyle
   birleştir. Sahiplik/temas/pas/dribling, LONG BALL ve D kararları bizim
   mevcut zaman katmanımızda değerlendirilsin. Yeni görsel gözlemler hatalı
   tracking'i otomatik denetlemeye adaydır; düzeltmenin başarısı ayrıca ölçülür.

Tam veri birleştirme akışı henüz doğrulanmış değildir. Görüntüde tespit yokken boşluğu dolduran bir
tahminin, gerçekten gözlenen top noktası gibi işaretlenmemesi gerekir.

## Dar kapsamlı ek deney: oyuncunun topa erişim süresi

Mevcut birlikte hareket/dribling özelliği, oyuncu ile topun hızını
karşılaştırır. **Erişim süresi** ise oyuncunun konumu, hareket yönü ve tepki
süresinden bir noktaya ne kadar sürede ulaşabileceğini tahmin eder. Bunlar
farklı sorulardır. Bu ikinci sinyal, yakınlık bakımından belirsiz adayları
ayırt etmeye yarayabilir; bu henüz bizim görevimizde doğrulanmış değildir.

Kaynak: Friends of Tracking'in
[MIT lisanslı LaurieOnTracking uygulaması](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/tree/7ed3ff857940d3f4611be55f3c08c79525c32171).
[Pitch control kodu](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking/blob/7ed3ff857940d3f4611be55f3c08c79525c32171/Metrica_PitchControl.py)
hedef noktadaki olası kontrolü modeller. Bu, mevcut top sahipliğinin doğrudan
ölçümü değildir. Bir takım daha fazla alanı kontrol ederken rakip topu tutabilir.

Deney sınırı:

- İlk aday bütün saha ısı haritası yerine, güvenilir gözlenen top çevresindeki
  oyuncuların erişim sürelerini karşılaştırır. Mevcut sisteme bu sinyalin
  eklendiği/eklenmediği iki sürüm aynı dış maçlarda değerlendirilir.
- Tahmin için olayın sahiplik takımı kullanılmaz. Kaynağın
  `generate_pitch_control_for_event` yardımcısı bu takımı olaydan okur;
  sahipliğini bulmaya çalıştığımız girdiyi önceden bildiğimizi varsayamayız.
  Ev/deplasman tarafları simetrik ele alınmalı, gerçek etiket girdi olmamalı.
- Kodun varsayılan tepki süresi, koşu hızı ve kontrol katsayıları seçilmiş
  proje parametresi sayılmaz. Sayısal seçimler dış maçlarda yapılır. Eksik
  hızın sıfır kabul edilmesi ve kaleciye verilen öncelik aynen taşınmaz.
- Kimlik sıçramaları, kayıp ölçüm ve devre sınırlarında geçersiz hızdan erişim
  kanıtı üretilmez. Top güvenilirliği önkoşuldur. Uzun/havadaki topun yakınından
  geçmek erişim tahminiyle sahipliğe dönüştürülmez; bu katman D kararı vermez.
- Yalnız temas/yeniden kontrol desteğiyle birlikte değerlendirilen bir adaydır.
  Ayrı maçlarda sahiplik spellF1 ve geçiş sınırlarına katkısı gösterilmezse
  teslim sistemine alınmaz. Geliştirme maliyeti de karşılaştırmaya dahildir.

Saha hakimiyeti, xG, pas ağı ve varsayımsal taktik simülasyonu bu deneyin
hedefi değildir. İzinli, yeterli doğrulama verisi bulunamazsa deney bekler;
mevcut mimariye yeni bağımlılık eklenmez.

## Deney ve donanım koşulları

Yerel donanım envanterinde GTX 1650 Ti ve yaklaşık 4 GB ekran belleği görüldü.
İlk bellek/süre denemesi küçük model, batch=1 ve ardışık işlemeyle yapılmalı.
RF-DETR, dilimleme ve SigLIP'i aynı anda GPU belleğinde tutmanın uygunluğu
ölçülmedi. Başka GPU'da yayımlanmış FPS bizim makinenin FPS'i değildir.

- Eğitim/ayar seçimi ile doğrulamayı **farklı izinli maçlarda** ayır.
  Aynı maçtan rastgele kare bölmek veya farklı kamera seçmek yeterli değil.
- Veri/video/etiket hakları ile checkpoint kaynakları ayrı doğrulansın.
  Model dosyası SHA-256, sürüm, bağımlılık kilidi ve seçimin gerekçesi kaydedilsin.
- Top konum hatası, görünür topu bulma, sahte top, kayıp/örtüşme davranışı;
  oyuncu ID değişimi ve takım eşleştirmesi ayrı değerlendirilsin.
- Sonra sahiplik spellF1 etkisini, görüntüsüz karşılaştırmayla aynı dış maçlarda
  ölç. COCO AP, MOT MOTA ve top F1 birbirinin yerine kullanılamaz.
- Süre, en yüksek GPU belleği ve eksik gözlem oranı ölçülsün. Başarılı bir demo
  tek başına tüm maç başarısı değildir.

## Kullanım ve açıklama şartları

[Yarışma kuralları](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/RULES.md)
incelenebilir/açıklanabilir hazır modelleri ve algoritmik tracking iyileştirmesini
kabul eder. Sağlanan maça insan etiketi/düzeltmesi uygulanamaz. Bu projenin
temiz geliştirme protokolüne göre bütün yeni seçimler başka maçlarda yapılır;
sağlanan public pencere yalnız seçilip dondurulmuş sistemin son kontrolüdür.

MIT/Apache bileşenler lisanslarına uyularak kullanılabilir ve değiştirilebilir.
Kod alınırsa gereken lisans/telif bildirimleri, Apache NOTICE yükümlülükleri
ve değişiklik kayıtları korunur. Bağımlılıklar, veri ve ağırlıklar da ayrı
incelenir. Teknik raporda kullanılan projeler ve bizim katkımız açıkça ayrılır:
örneğin “RF-DETR tespiti kullanan, tarafımızdan geliştirilen veri birleştirme ve
sahiplik sistemi”. Başkasının mimarisini özgün icadımız olarak sunmayız.

Bu araştırmada yalnız kamuya açık kaynak/lisans belgeleri incelendi; maç
görüntüsü veya veri yüklenmedi, ağırlık çalıştırılmadı, donmuş temel model
değiştirilmedi. Kaynak incelemesi, bekleyen sağlayıcı temizliği dahil önceki
remediation koşullarının tamamlandığı anlamına gelmez.
