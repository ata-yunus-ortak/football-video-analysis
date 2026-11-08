# Dış veride doğal ölçekte top eğitimi — 8 Kasım 2026

V016 tam kare eğitimi yanlış adayları azalttı ancak doğru topları da kaybetti.
V017 güven eşiği seçimi doğru eşleşmeleri geri getirirken yanlış adayları
artırdı. Hiçbiri teslim modeline alınmadı. Yeni deney, topu tüm görüntüyü
küçülterek kaybetmemek için doğal piksel ölçeğinde parçalarla eğitim yapar.

## Veri ve ayrım

SoccerNet GSR'nin sabit sürümlü `train.zip` arşivinden 25 ek kesitte
1.875 kare edinildi. Kaynak maç 4: 1.050 eğitim; maç 6: 375 doğrulama;
maç 9: 450 sabit kontrol karesi. Bunlar aynı, daha önce erişilmiş üç maçın
başka sahneleridir; yeni bağımsız maç testi değildir. Her 10 kaynak karesinden
biri seçildi; bu dosyalar kesintisiz 25 fps video diye kullanılamaz.

Arşivin tamamı indirilmedi ve tam arşiv SHA-256 doğrulanmadı. İndirilen ZIP
üyelerinin CRC ve SHA-256 kayıtları yerelde tutulur. İlk metadata denemesinde
arşiv dışı sıra numarası, görüntü indirilmeden reddedildi; düzeltme kayıtlıdır.
Ham görüntüler, referanslar ve ağırlıklar GitHub'a konmaz. Araştırma kullanımı
ve kaynak koşulları: [SoccerNet FAQ](https://www.soccer-net.org/faq),
[GSR kaynak deposu](https://github.com/SoccerNet/sn-gamestate).

## Önceden kaydedilen yöntem

`ball-patch-training-plan.json` sonuçlar görülmeden kaydedildi. Kaynakta
1, 101, 201, … numaralı uygun kareler seçilir. Bilinmeyen top karesi negatif
sayılmaz. Her eğitim karesinden, topu içeren rastgele kaydırılmış bir 384×384
parça ve referans top kutusuyla kesişmeyen bir ızgara parçası alınır.
Ek işaretlenmemiş topların bulunması mümkündür; ikinci parça kesin olarak
"top yok" gerçeği değildir. Veri kümesinin referans kapsamıyla sınırlıdır.

106 eğitim karesi → 212 parça. Doğrulama: 40 kare → 960 sabit ızgara parçası.
Doğrulama ızgarası etiketin konumundan bağımsızdır; etiket değiştirme testi
çıktı görüntülerinin değişmediğini doğrular. Parçalar kayıpsız PNG olarak
kaydedilir; kırpılan özgün piksellerle eşitlik ve içerik hash'leri denetlenir.
Kontrol maçının 45 tam karesi eğitim parçasına dönüştürülmez.

COCO top başlığı korunmuş Nano başlangıcıyla iki epoch, öğrenme hızı 1e-5,
encoder 1e-6, batch 1 ve 16 adım biriktirme. En iyi epoch yalnız ızgara
doğrulama mAP değeriyle seçilir. Bu başarı, tam kare başarısı yerine geçmez.

Tam kare karşılaştırmasında orijinal Nano 512×768 tarama/eşik 0,3;
aday 384×384 tarama/ham eşik 0,05 kullanır. İkisinde örtüşme 0,2,
GREEDYNMM/IOS 0,5 ve tam görüntü tahmini bulunur. SAHI'nin düşük eşikte
otomatik NMS'ye geçişi `force_postprocess_type=True` ile kapatılır.
Bu uygulama ayrıntısı ilk eğitim sürerken, tam kare sonuçlarına bakılmadan
saptandı. Eğitim aynı kalır; eski otomatik geçişli değerlendirme kullanılmaz.
Düzeltilmiş değerlendirme aynı dondurulmuş checkpoint'ten yeniden üretilir.

İşletim eşiği yalnız doğrulamada ön kayıtlı sekiz değerden seçilir;
ardından sabit kontrol çalıştırılır. Her iki maçta temel modelin doğru
eşleşme sayısı korunmalı, eşleşmeyen adaylar en az %20 azalmalı.
Geçmek yalnız daha geniş dış doğrulamaya izin verir; sahiplik veya final
teslim doğruluğu anlamına gelmez. Barcelona görüntüsü kullanılmaz.

Araçlar: `tools.ball_data_expansion`, `tools.ball_detector_data`,
`tools.ball_patch_data`, `tools.ball_patch_training`.
Edinme ve veri kapsamı özeti: `ball-data-expansion-results-v1.json`.

## Sonuç ve karar

İki epoch tamamlandı; en iyi parça doğrulama mAP@50:95=0,20434,
mAP@50=0,55018. Tam görüntü doğrulamasında 40 karede 43 referans kutusu var.
Orijinal model 24 doğru eşleşme / 54 eşleşmeyen aday verdi. Adayın sekiz
eşikteki en yüksek doğru eşleşmesi 22; hiçbir eşik temel modeli korumadı.
0,3 eşikte 18 doğru / 21 eşleşmeyen aday var. Daha az yanlış aday,
kaybedilen gerçek top tespitleri nedeniyle kabul için yeterli olmadı.

**Aday reddedildi; ana model değişmedi.** Doğrulamada eşik seçilemediği için
45 karelik sabit kontrol çalıştırılmadı. Bu veri daha önce erişilmiş kaynak
maçtan gelir; çalıştırılmaması onu yeni bağımsız test yapmaz.
Özet ve tüm doğrulama eşikleri: `ball-patch-results-v1.json`.

267 testin 265'i temel ortamda geçti, iki AV testi atlandı; ilgili video
modülleri AV kurulu ortamda ayrıca çalıştırıldı ve toplam dokuz test geçti.
Sabit temel model ve kaynak bütünlüğü testleri korundu. Bu sonuçlar top
sahipliği doğruluğu veya tüm yarışma koşullarının tamamlandığı iddiası değildir.

Sonraki geliştirme, bu başarısız adayın eşiğini tekrar tekrar değiştirmek
yerine ayrı ön kayıtla daha çeşitli maçlar ve tam karedeki zor arka plan
örneklerini kapsamalı. Zamansal iz başarısı ayrıca ölçülmeli; seyrek kareler
kesintisiz iz verisi yerine kullanılamaz.
