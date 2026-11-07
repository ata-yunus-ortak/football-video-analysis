# Dış görüntülerde top adayı deneyi — 8 Kasım 2026

Bu çalışma Barcelona görüntüsünü, tracking'ini veya etiketini kullanmaz.
Kaynak SoccerNet GSR eğitim arşivindeki daha önce erişilmiş sekiz kısa kesittir.
Kaynak maç 4 öğrenme, 6 seçim, 9 sabit aday kontrolü olarak ayrıldı.
Maç 9 daha önce başka deneylerde görüldüğü için bağımsız test değildir.

## Filtre: varsayılan modele alınmadı

`ball-candidate-selection-plan.json` sonuçlardan önce kaydedildi.
Girdiler: tespit güveni, kutunun en/boy ve görüntüye göre alanı, en yakın
tespit edilmiş kişinin ayağına göreli uzaklık ve boy oranı. Gerçek topun
ayağa yakın olabileceği dikkate alınarak otomatik ayak-yakınlığı yasağı yoktur.
Referans etiketler yalnız dış öğrenme ve değerlendirme içindir.

355 örneğin 129'u pozitifti; belirsiz IoU aralığı öğrenmeye alınmadı.
Top etiketi olmayan kareler öğrenmede negatif sayılmadı. Normal ve parçalı
tarama birlikte öğrenildi, kabul koşulları her modda ayrı sınandı.
Seçilen tanısal aday lojistik model, eşik 0,3. Kabul: eşleşmelerin en az
%95'i korunacak, eşleşmeyen adaylar en az %20 azalacak; iki ayrı maç ve
iki modda da geçmeli. Karşılaştırma IoU≥0,5 bire bir kutu eşleşmesidir.

| Sabit aday kontrolü, maç 9 | Önce eşleşen | Sonra eşleşen | Önce eşleşmeyen | Sonra eşleşmeyen |
| --- | ---: | ---: | ---: | ---: |
| Normal tarama | 53 | 53 | 134 | 128 |
| Parçalı tarama | 85 | 84 | 442 | 224 |

Parçalı taramada olumlu sonuç var, fakat normal modda azalma yalnız %4,5.
Ön kayıtlı ortak koşul sağlanmadı; **filtre final veya varsayılan sisteme
eklenmedi**. Sonucu gördükten sonra yalnız başarılı modu seçmek için deneyin
kabul kuralı değiştirilmedi. Model ve diğer adaylar özel çalışma kaydında.
Özet `ball-candidate-external-results-v1.json`.

## Konum/boyut hatasını ayrı inceleme

Bu betimleyici kontrol model veya eşik seçmez. Sekiz kesitte 525 top kutusu:

| Eşleşme koşulu | Normal | Parçalı |
| --- | ---: | ---: |
| IoU≥0,1 | 200 | 405 |
| IoU≥0,25 | 180 | 379 |
| IoU≥0,5 | 134 | 250 |
| IoU≥0,75 | 32 | 61 |

Bu fark, küçük top kutularındaki yer/boyut hatasının önemli olduğunu
gösteriyor; düşük IoU başarı standardına çevrilmedi. Etiketli karelerde
topla IoU<0,1 olan 162 normal / 584 parçalı aday da var: sorun yalnız
kutu hassasiyeti değil. Etiketsiz karelerdeki 39 / 220 aday ayrıca tutuldu;
kesin yanlış tespit diye adlandırılmadı. En yakın aday merkezi de yanlış
bir nesneye ait olabilir. Rapor `ball-localization-external-results-v1.json`.
Bu ölçümler oyundaki top kimliği, fiziksel saha doğruluğu veya sahiplik puanı değildir.

## Dedektör eğitimi için veri hattı

`tools.ball_detector_data` manifest hash'leri doğrulanmış dış JPEG ve top
kutularını COCO'ya dönüştürür. Pikseller değişmez; maçlar karışmaz. Bilinmeyen
top kareleri ve ignore bölgeleri dışarıda bırakılır; eksik etiketten negatif
örnek üretilmez. Yerel hazırlık: 225 eğitim / 150 doğrulama / 150 ek kontrol
görüntüsü, her birinde bir top. Ek kontrolün 75 etiketsiz karesi dışarıda kaldı.
Bu sınırlı, top-görünen veri grubu topun olmadığı durumları doğrulayamaz.

`ball-detector-training-plan.json` tek epoch yerel çalışabilirlik deneyi
tanımlar; `tools.ball_detector_train` kaynak ve ağırlık hash'lerini kontrol
eder, bulut kayıtlarını kapatır, ek kontrolü otomatik değerlendirmez.
Tek epoch veya eğitim kaybının azalması yeni modeli seçmek için yeterli değildir.
Daha geniş maç çeşitliliği ve küçük top çözünürlüğü ayrıca ele alınmalıdır.

Eğitim için ayrı ortamın doğrudan bağımlılıkları
`requirements-vision-training.txt` içindedir. Bu, mevcut donmuş NumPy
çalıştırıcısının gereksinimlerini değiştirmez. İlk deneme eksik Lightning
bağımlılığı nedeniyle eğitim başlamadan durdu; eğitim bağımlılıkları
tamamlanarak yeni özel çıktı dizininde tekrar başlatıldı. Eski başarısız
kayıt korunur. 248 testten 246'sı geçti, iki isteğe bağlı AV testi atlandı.

SoccerNet veri kullanımı araştırma amaçlıdır; ham veri yeniden dağıtılmaz.
RF-DETR Nano paketi/ağırlıkları Apache-2.0 kapsamındadır; proje sıfırdan
yazılmış dedektör iddiasında bulunmaz ve ilgili atıfları korur.
Kaynaklar: [SoccerNet koşulları](https://www.soccer-net.org/faq),
[RF-DETR lisansı](https://roboflow.com/model-licenses/rf-detr),
[eğitim belgesi](https://rfdetr.roboflow.com/learn/train/).

```powershell
python -m tools.ball_candidate_selection --gallery /private/gallery.json --analysis /private/analyses --out /private/new-filter-study
python -m tools.ball_localization_audit --gallery /private/gallery.json --analysis /private/analyses --out /private/new-localization-audit
python -m tools.ball_detector_data --gallery /private/gallery.json --out /private/new-coco
python -m tools.ball_detector_train --data /private/new-coco --weights /private/rf-detr-nano.pth --out /private/new-training
```
