# Öğrenilmiş duran top (D) maskesi

11 Kasım 2026. `development/learned_dead_ball.py`, yalnız oyuncu takibinden
kare bazında D maskesi üretir. Top, olay veya etiket girdisi yoktur.

## Neden bu veri?

[IDSSE](https://doi.org/10.6084/m9.figshare.28196177) (DFL, 7 maç, 25 fps,
CC BY 4.0) pozisyon dosyasında her top karesinde `BallStatus` (1 canlı,
0 ölü) vardır. Bu, D001'de eksik olan bağımsız ve eksiksiz D/canlı oyun
hedefidir. Kurallar başka maçlarda dış veriyi ve etiketi açıkça serbest bırakır.

Ölü top karelerin %41–52'sidir. **DFL top koordinatı her ölü karede sabit
tutulur (7 maçta %100).** Top özelliği etiketi sızdırır ve topun duruşta
kaybolduğu kaynaklara taşınmaz. Bu yüzden top tamamen dışarıdadır.
Hakem kayıtları (`TeamId="referee"`) atılır.

## Özellikler ve model

- 1 s ve 3 s yer değiştirmesinden oyuncu hızları (ortalama, p90, yavaş/yürüyen/
  koşan oranı), takım yayılımı, takım merkezleri, kenar/ceza sahası/saha dışı
  oyuncu sayısı, santra şekli. 1, 3, 8 s merkezli ve 3 s geçmiş/gelecek
  pencereleri; pencereler devre sınırını geçmez.
- Bütün ölçüler saniye ve metre cinsindendir; FPS'ten bağımsızdır.
- Girdi depo düzenindedir: köşe orijinli metre (`normalize x/y × saha`).
- Model: `HistGradientBoostingClassifier`. Her eğitim maçı temiz + 3 bozulmuş
  kopya (oyuncu kayıp segmentleri %0–50, konum gürültüsü 0–1.5 m, sabit tohum).
- Yumuşatma (pencere, eşik, en kısa koşu) yalnız doğrulama maçında seçilir.

**Bozulma eğitimi zorunlu:** temiz veriyle eğitilen ilk model %10 kayıp ve
0.3 m gürültüde D F1 0.93'ten 0.30'a düştü. Neden: 0.2 s hız farkı gürültüyü
~2 m/s büyütüyordu. 1 s/3 s hız + bozulma eğitimiyle aşağıdaki sonuçlar alındı.

## Split ve sonuçlar

Kayıt: `learned-dead-ball-plan.json` (indirmeden önce maç bazında).
Eğitim J03WN1, J03WOH, J03WOY, J03WPY, J03WQQ; doğrulama J03WMX; ayrılmış J03WR9.

Seçilen yumuşatma: pencere 2 s, eşik 0.5, en kısa koşu 4 s.

| Maç | D kesinlik | D duyarlılık | D F1 | Duruş (IoU≥0.5) | Başlangıç / bitiş hatası (medyan) |
| --- | --- | --- | --- | --- | --- |
| Doğrulama, temiz | 0.911 | 0.938 | 0.924 | 78/103 | 1.4 s / 0.8 s |
| Doğrulama, ağır bozulma | 0.894 | 0.891 | 0.893 | 70/103 | 2.2 s / 1.1 s |
| **Ayrılmış, temiz** | 0.920 | 0.929 | **0.924** | 78/92 | 1.2 s / 0.5 s |
| **Ayrılmış, ağır bozulma** | 0.894 | 0.887 | **0.891** | 69/92 | 2.2 s / 1.1 s |

Ağır bozulma: %30 kayıp oyuncu karesi, 0.8 m gürültü. Ayrılmış maç dondurmadan
sonra değerlendirildi; aynı dondurulmuş yöntem önce çalışma alanında, sonra bu
depo aracıyla iki kez çalıştırıldı ve sonuç seçime geri beslenmedi.

Metrica örnek maç 3 (farklı sağlayıcı, EPTS) yalnız değerlendirme içindir.
Olaylardan türetilmiş kısmi vekillerle ölçüldü: BALL OUT → SET PIECE,
FAULT RECEIVED → FREE KICK, gol → santra; canlı vekil PASS/CARRY içi kareler.

Durma vekili karelerinin %91.3'ü D, 64 duruşun 56'sı yakalandı;
canlı vekil karelerinin %4.6'sı yanlış D. Metrica takibi IDSSE kadar
pürüzsüzdür (medyan sapma 0.07 m), bu yüzden gürültü dayanıklılığını test etmez.

## Organizatör puanlayıcısıyla etki (IDSSE)

`tools/idsse_spell_eval.py`, dondurulmuş H/A/X temel modelini D maskesiyle ve
maskesiz, organizatörün `possession_metrics.py` puanlayıcısıyla (commit
`f8f2629`) puanlar. Gerçek etiket: DFL `BallStatus` + `BallPossession`.
Ham DFL topu ile; duruşta topu silinmiş akışta sonuçlar ±0.01 içinde aynı.

| Maç | Sürüm | spellF1 | macroF1 |
| --- | --- | --- | --- |
| Doğrulama | temel | 0.232 | 0.407 |
| Doğrulama | temel + öğrenilmiş D | 0.265 | 0.781 |
| Doğrulama | temel + gerçek D (üst sınır) | 0.313 | 0.831 |
| Ayrılmış | temel | 0.264 | 0.420 |
| Ayrılmış | temel + öğrenilmiş D | 0.321 | 0.788 |
| Ayrılmış | temel + gerçek D (üst sınır) | 0.384 | 0.848 |

D maskesi macroF1'i ikiye katlar; spellF1'e +0.03/+0.06 ekler, mümkün
kazancın yarısı kadar. Gerçek D ile bile spellF1 ~0.31–0.38'de kalıyor:
asıl darboğaz H/A sahiplik sınırları. Bunlar yarışma skoru değildir.

## Sınırlar

- D tanımı DFL'nindir. Yarışmanın D başlangıç/bitişiyle aynı olduğu
  doğrulanmadı. Sınır hatası medyanı ~1–2 s'dir.
- Yarışma takibi muhtemelen daha gürültülü. Gürültü düzeyi yarışma verisine
  bakılarak seçilmedi; geniş bir aralıkta eğitildi.
- ATD girdisinde devre bilgisi yok (`period` hep 1). Pencereler devre arasını
  geçebilir; devre arası boş karelerin D çıktısı doğrulanmadı.
- Yarışma maçı, onun etiketleri, görüntüleri veya public skoru hiçbir aşamada
  kullanılmadı.

## Çalıştırma

```bash
python -m pip install -r requirements-dball.txt
python -m tools.idsse_data --plan learned-dead-ball-plan.json --out /private/idsse
python -m tools.train_learned_dead_ball --plan learned-dead-ball-plan.json \
    --data /private/idsse --out /private/learned-dead-ball-v2 --metrica3 /private/metrica3
```

Çıktı: `model.pkl`, `model.json` (split, ayarlar, hash'ler), `checks.json`.
Ham veri, NPZ ve model deponun dışında kalır. Boru hattına bağlama:

```python
from development.learned_dead_ball import predict_mask
mask = predict_mask(model, inputs, (window_s, threshold, min_run_s))
predict(inputs, baseline, config, learned_dead_mask=mask)
```

`predict` maskeyi D yapar; gerekçe `learned_player_motion_dead_ball`.
Tag tabanlı D katmanı ile birlikte verilirse iki maske birleşir.
