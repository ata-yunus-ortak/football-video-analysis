# Top ölçümünde çözünürlük ve sınıf aktarımı — 8 Kasım 2026

Bu çalışma [gelişim planının](GELISIM_PLANI_20261108_TR.md) ilk iki adımıdır.
Barcelona verisi veya çıktısı geliştirme girdisi değildir. Önceki donmuş
sahiplik sürümü korunur; yeni deneyler final sisteme otomatik eklenmez.

## V015: aynı GPU'da çözünürlük karşılaştırması

Plan `ball-resolution-plan.json`, araç `tools.ball_resolution_experiment`.
Sekiz eski dış kesitin her beşinci karesi alındı: toplam 120 kare. Orijinal
JPEG hash'i ve çözülmüş RGB hash'i eski kayıpsız video eşlemesiyle doğrulandı.
İki modda aynı Nano ağırlığı, 0,3 eşik, 0,2 örtüşme ve GPU kullanıldı.
Referanslar bütün tahmin dosyaları dondurulduktan sonra puanlandı.

| Kaynak maç | Eski 512×768: eşleşen / eşleşmeyen | Yeni 384×384: eşleşen / eşleşmeyen |
| --- | ---: | ---: |
| 4 | 17 / 60 | 25 / 56 |
| 6 | 12 / 55 | 14 / 57 |
| 9, sabit kontrol | 15 / 92 | 15 / 92 |

Her maçta ≥%20 eşleşme artışı ve ≤%25 eşleşmeyen artışı koşulu geçilmedi.
Yeni tarama varsayılan yapılmadı. Yerel süre yaklaşık 60→110 saniye;
donanım benchmark'ı değildir. Maç 9'da top etiketi olmayan kareler de var;
onlardaki adaylar kesin yanlış pozitif diye yorumlanmaz. Seyrek kareler
zamansal takip veya sahiplik başarısını ölçmez. Özet:
`ball-resolution-results-v1.json`.

## COCO sınıf sözleşmesi koruması

Ortak `development.vision.LocalVision` adaptörü artık checkpoint'in
sınıflandırma tensörlerini model kurulmadan önce kontrol eder. 91 satırlı
COCO başlığı yoksa otomatik başlık değiştirmeyi reddeder. Kurulumdan sonra
sınıf adları ve 90 sınıflı yapı da doğrulanır. Kontrol adaptörü kullanan bütün
çağrı yollarında geçerlidir. Böylece tek sınıflı top
ağırlığı kişi/top COCO numaralarıyla sessizce yorumlanamaz.

Gerçek dış video ile bir karelik çalıştırmada orijinal model kabul edildi,
önceki tek sınıflı checkpoint beklenen hatayla reddedildi. Bu bir doğruluk
testi değildir. Eski kayıtların kaynak hash'leri yenilenmedi: eski ölçümü
tekrar entegre etmek için onun kayıtlı kaynak sürümü kullanılmalıdır.
Özet `vision-class-contract-results.json`; 257 testten 255'i geçti, iki
isteğe bağlı AV testi atlandı. Çözünürlük deneyi bu ortak adaptör kontrolü
eklenmeden önce çalıştı; rapor eski kaynak hash'lerini ve Git sürümünü korur.

## V016: öğrenilmiş top başlığını koruyarak eğitim

Plan `ball-transfer-training-plan.json`; araç `tools.ball_transfer_training`.
COCO'nun doğrulanan sports-ball ID 37 satırı, bütün sınıflandırma başlıklarında
yeni dense ID 0'a kopyalanır. Kullanılmayan ID 1'in ağırlıkları sıfır ve bias'ı
−10 olur. Diğer tensörler aynen korunur; model kurulduktan sonra başlangıç
durumunun tamamı tekrar karşılaştırılır. NumPy testi eski top logitinin yeni
başlıkta aynen üretildiğini doğrular. Bu, modelin bütün tahminlerinin aynı
olacağı anlamına gelmez: encoder sorgu seçimi de sınıf puanlarından etkilenir.

225 eğitim / 150 doğrulama görüntüsü, üç epoch, öğrenme hızı 1e-5 ve encoder
için 1e-6. En iyi epoch yalnız doğrulama mAP'siyle seçilir. Ayrı maç 9 eğitimde
değerlendirilmez. Sonrasında orijinal COCO, yalnız başlık aktarılmış ve
eğitilmiş sürümler aynı GPU/kare/eşikte karşılaştırılır. Yeni modellerde yalnız
ID 0 top kabul edilir; ID 1 kişi veya top diye etiketlenmez.

Kabul koşulu sonuçtan önce: doğrulama ve sabit kontrolün ikisinde de eski
modelin doğru eşleşmelerinin tamamı korunmalı; eşleşmeyen adaylar ≥%20
azalmalı. Başarılı olsa bile bu küçük, daha önce görülmüş ve yalnız top
etiketi olan görüntülerden oluşan grup final sürüm onayı değildir. Daha
geniş dış doğrulama, top yokken davranış, takip ve sahiplik ayrıca gerekir.

V016 tamamlandı. Sabit 0,3 eşikte sonuç:

| Grup / model | Eşleşen | Eşleşmeyen |
| --- | ---: | ---: |
| Doğrulama / orijinal COCO | 47 | 104 |
| Doğrulama / yalnız başlık aktarımı | 49 | 180 |
| Doğrulama / üç epoch eğitim | 39 | 43 |
| Sabit kontrol / orijinal COCO | 53 | 95 |
| Sabit kontrol / yalnız başlık aktarımı | 55 | 157 |
| Sabit kontrol / üç epoch eğitim | 39 | 42 |

Yanlış aday azalması doğru eşleşme kaybıyla birlikte geldiği için kabul
edilmedi. Yeni ağırlıklar mevcut dedektörün yerine geçirilmedi. Özet:
`ball-transfer-results-v1.json`. En iyi doğrulama epoch'u üçüncüdür.

## V017: sabit modelin çalışma eşiğini seçme

Farklı modellerin 0,3 puanı aynı doğruluk olasılığı değildir. Ayrı kayıt
`ball-confidence-calibration-plan.json`, aynı ağırlıklar için önceden
belirlenen 0,05–0,5 eşikleri yalnız maç 6'da karşılaştırır. Eski modelin
eşleşmelerini koruyanlar içinde en az eşleşmeyen üreten eşik sabitlenir;
sonra maç 9 çıkarımı/puanlaması yapılır. Önceki kabul koşulu aynen kalır.
Her iki maç daha önce görülmüştür; bu yeni bağımsız test diye sunulmaz ve
kontrol sonucundan sonra eşik yeniden ayarlanmaz.

V017 tamamlandı: seçilen eşik 0,15. Doğrulama eşleşmeleri 47→49 olsa da
eşleşmeyenler 104→177 arttı. Sabit kontrolde 53→57 ve 95→150 çıktı.
Kabul edilmedi; ağırlık ve eşik final sisteme alınmadı. Özet
`ball-confidence-results-v1.json`. Bu sonuç aynı küçük veri üzerinde
eşik ayarı yapmayı sürdürmek yerine sahne kapsamını büyütme ihtiyacını gösterdi.
