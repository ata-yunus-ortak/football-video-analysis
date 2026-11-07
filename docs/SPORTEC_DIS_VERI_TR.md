# Sportec/DFL dış veri kapsamı — 7 Kasım 2026

Kaynak: Bassek, Rein, Weber ve diğerleri, *An integrated dataset of
spatiotemporal and event data in elite soccer*, Scientific Data 12, 195 (2025).
DOI: https://doi.org/10.1038/s41597-025-04505-y.
Veri sahibi DFL; sağlayıcı Sportec Solutions / TRACAB.

Lisans **CC BY 4.0**, hem [özgün Figshare kaydında](https://doi.org/10.6084/m9.figshare.28196177)
hem [PySport kopyasında](https://huggingface.co/datasets/pysport/idsse-data)
doğrulandı. Kullanım atfı bu belgede tutulur. Ham veri ve kare düzeyindeki
hazırlanmış dosyalar kaynak deposuna eklenmez.

## Ön kayıt

`sportec-data-plan.json`, ham veri indirilmeden önce 4 eğitim, 2 doğrulama,
1 ayrılmış son kontrol maçı tanımlar. Önceki erişim geçmişinin tamamı bilinmediği
için koşulsuz “hiç görülmemiş veri” iddiası yapılmaz. PySport kopyasının sabit
commit'i ve dosya kimlikleri kayıtta. `J03WMX` son kontrol için ayrılmıştır;
mevcut edinme ve hazırlama araçları bu maça erişimi reddeder.

## İlk eğitim maçı: J03WOH

İndirme SHA-256 ile doğrulandı; iki geçişli XML adaptörü çalıştırıldı.

| Kapsam | Sayı |
| --- | ---: |
| Kare, 25 FPS | 137.214 |
| H | 39.126 |
| A | 32.819 |
| D | 65.269 |
| D sırasında sonlu top koordinatı | 65.269 |
| Canlı oyunda sonlu top koordinatı | 71.945 |
| Eksik top kaydı | 0 |
| Devre içi native kare kopması | 0 |

Metrica örneklerinin aksine bu maçta D aralıklarında top koordinatı mevcuttur.
Bu bir veri kapsamı bulgusudur; öğrenilmiş D sınıflandırıcısının başarısı değildir.
Sağlayıcının koordinat kalitesi ile yarışmanın otomatik tracking kalitesi aynı
varsayılamaz. Sonlu koordinat, görüntüde gerçekten tespit edildiği anlamına gelmez.

`BallStatus` ve `BallPossession` yalnız ayrı `targets.npz` içinde hedef üretir.
`inputs.npz` yalnız ölçüm dizilerini içerir. Bilinmeyen hedef X kalır; hedefe
bakarak kare veya oyuncu elenmez. Hakemler metadata oyuncu listesine alınmaz.
Native kare saatleri ayrıca korunur; devre/kare kopmaları hareket bağını keser.
Görüntü veya olay dosyası bu aşamanın girdisi değildir.

Yeni H/A/D metriği, gerçek D aralığını maskeleyip yanlışlıkla birleşmiş iki
sahipliği doğru saymaz. Tahmin X'i yalnız bilinen hedef bloğu içinde doldurur;
gerçek duruş ve bilinmeyen hedef ayrıdır. Bu dış ölçüm resmî yarışma skoru değildir.

## Çalıştırma

```powershell
python -m tools.sportec_download --fixtures J03WOH --out /private/sportec/raw
python -m tools.sportec_prepare --raw-dir /private/sportec/raw --fixture J03WOH --out /private/sportec/prepared/J03WOH
```

9 yeni sentetik adaptör/metrik testi; toplam 225 test, 223 geçti, iki isteğe bağlı
AV testi atlandı. Hedef etiketlerini değiştirmenin özellik dizilerini değiştirmediği,
yanlış maç/çift kayıt reddi ve ayrılmış son kontrol erişim yasağı sınandı.

Sonraki adım: kalan eğitim/doğrulama maçlarının bütünlüğünü ve kapsamını kontrol
etmek; eğitimde belirlenen özelliklerle ayrı D modeli seçmek, eksik/gürültülü
ölçümlere dayanıklılığı dış maçlarda değerlendirmek. D modeli veya birleşik final
teslim adayı henüz seçilmiş değildir. Barcelona görüntüsü bu çalışmada kullanılmadı.
