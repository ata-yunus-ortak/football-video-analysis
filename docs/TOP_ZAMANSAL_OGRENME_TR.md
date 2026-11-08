# Zamansal top kanıtı — 8 Kasım 2026

Yeni katman, gerçek top adayının birkaç ardışık karede doğrulanmasını kutu
geometrisi ve dedektör güveniyle birlikte değerlendirir. Kaybolan top için
üretilen tahminler gerçek tespit sayılmaz. Mevcut sahiplik ve ham kutular
değişmez; aday final modele alınmış değildir.

## Yöntem ve ayrım

İlk V020 deneyi 2/3/5 gözlem, üç eşleme yarıçapı ve üç belirsizlik marjıyla
27 süreklilik filtresini karşılaştırdı. En fazla N−1 gelecek kareyle
doğrulanan izin başlangıçtaki **gerçek ölçümleri** de korunur. Tek karelik
aday, belirsiz eşleşme veya kamera kesmesi doğrulanmış iz yapılmaz.
Normal ve parçalı taramada ortak kabul koşulu geçilmedi; ayrı kontrol
çalıştırılmadı. Bu başarısız deneyin koşulları değiştirilmedi.

V021 ayrı ön kayıtla sürekliliği zorunlu koşul yerine öğrenilen özellik
yaptı: güven, kutu oranı/alanı, kişi ayağına göre uzaklık ve boyut ile
2/3/5 gözlemde doğrulanma bayrakları. Doğrulama en fazla dört gelecek
kareye bakar; bu **çevrimdışı** bir yöntemdir. Skor kalibre edilmiş
olasılık veya sahadaki gerçek top kimliği değildir.

Kaynak maç 4 eğitim: 355 uygun aday, 129 pozitif. Referans IoU ≥0,5 pozitif,
≤0,1 negatif; aradakiler dışarıda. Kesit/tarama gruplarının toplam eğitim
ağırlığı eşit. Üç düzenlileştirme ve dokuz eşik yalnız maç 6 doğrulamasında
seçildi; seçim sabitlenip maç 9 kontrol edildi. Geometriyle sınırlı ayrı
modeller de karşılaştırma için eğitildi. Etiketler özellik çıkarıcıya girmez.

Bütün metrikler yalnız etiketli, yok sayma bölgesi olmayan ve referans top
bulunan karelerde ölçülür. Maç 9'un 75 bilinmeyen karesi negatif sayılmaz.
Önceki bazı raporlardaki kapsamla bu fark dikkate alınmalıdır. Kısa kesitler
daha önce erişilmiş üç maçtandır; yeni bağımsız test iddiası yoktur.

## Ölçüm

| Grup | Tarama | Doğru eşleşme: ham → yeni | Eşleşmeyen: ham → yeni |
|---|---|---:|---:|
| Doğrulama | Normal | 47 → 46 | 104 → 55 |
| Doğrulama | Parçalı | 71 → 71 | 220 → 75 |
| Sabit kontrol | Normal | 53 → 53 | 95 → 83 |
| Sabit kontrol | Parçalı | 85 → 85 | 222 → 165 |

Doğrulama koşulu geçti. Sabit kontrolde doğru eşleşmeler korundu; fakat
normal taramada eşleşmeyen azalması %12,6 ile gerekli %20'nin altında.
**Tam kabul başarısız; teslim modeli değiştirilmedi.** Parçalı kontroldeki
%25,7 azalma, normal taramadaki başarısızlığı gizlemek için birleştirilmez.
Kontrol sonrası eşik veya model değiştirilmedi.

Özetler: `ball-temporal-selection-results-v1.json`,
`ball-temporal-learned-results-v1.json`. Öğrenilmiş ağırlıklar ve kare
düzeyindeki tahminler yereldedir. Kutuyla eşleşmeyen adayın kesinlikle
ayak olduğu veya yanlış sahipliğe dönüştüğü bu ölçümden çıkarılamaz.

## Proje bağlantısı

`tools.ball_temporal_evidence` sabit modeli, kayıtlı dış görüntü analizine
ekler. 8 kesit × 2 tarama × 75 kare = 1.200 analiz paketi üzerinde çalıştı;
bunlar **600 farklı kaynak karesinin iki taramasıdır**. Referans dosyalarını
okumaz. `experimental_ball_evidence` alanı aday puanlarını ve deneysel
filtre kararlarını taşır; `objects`, mevcut izler ve sahiplik korunur.
`possession_eligible=false`, `selected_in_play_ball=false` kalır.
Kaynak/model kimliği uyuşmazsa çalışmaz. Bu bağlantı doğruluk onayı değildir.

```powershell
python -m tools.ball_temporal_selection --gallery /external/gallery.json --analysis /external/analysis --out /private/new-temporal-selection
python -m tools.ball_temporal_learned --gallery /external/gallery.json --analysis /external/analysis --out /private/new-temporal-learning
python -m tools.ball_temporal_evidence --gallery /external/gallery.json --analysis /external/analysis --study /private/new-temporal-learning --out /private/new-evidence
```

277 testin 275'i temel ortamda geçti; atlanan iki AV testini içeren ilgili
modüllerde AV ortamında ayrıca 9 test geçti. Ölçüm/tahmin ayrımı, kaynak
karışması, kamera kesmesi, sınıf şeması, bilinmeyen hedef kapsamı ve mevcut
sahipliğin korunması test edildi. Dondurulmuş temel kaynaklar korunuyor.

## Maç çeşitliliği

[Resmî GSR veri deposunun](https://huggingface.co/datasets/SoccerNet/SN-GSR-2024/tree/main)
sabit sürümlü `valid.zip` arşivinde ön kayıtlı dört metadata örneği okundu.
Önceki 4/6/9 grubunun dışında kaynak oyun kimlikleri **2, 3 ve 5** bulundu.
Görüntü dosyası indirilmedi, model seçimi yapılmadı. Üye CRC/SHA kayıtları
var; tam arşiv hash'i doğrulanmadı. Önceki tüm erişim geçmişi bilinmediği
için dokunulmamış test sertifikası değildir. `ball-new-games-inventory-results-v1.json`.

Sonraki aşamada bu farklı maçlar için görüntü erişiminden önce ayrı eğitim,
doğrulama ve son kontrol planı kaydedilmeli; kesintisiz kesitler kullanılmalı.
Eski maça tekrar tekrar eşik ayarı yapmak yerine genelleme ölçülmeli.
Barcelona verisi bu çalışmaların girdisi değildir. Önceki süreç temizliğinin
ve bütün organizatör koşullarının tamamlandığı iddia edilmez.
