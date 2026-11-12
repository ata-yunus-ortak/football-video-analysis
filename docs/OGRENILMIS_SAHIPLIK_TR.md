# Öğrenilmiş H/A sahiplik modeli

12 Kasım 2026. `development/learned_possession.py`, canlı top karelerinde H/A
olasılığı üretir; D, `learned_dead_ball` maskesinden gelir. Hedef: IDSSE
pozisyon akışındaki kare bazında DFL `BallPossession` (yalnız canlı kareler).
Split D çalışmasıyla aynıdır (`learned-dead-ball-plan.json`).

## Özellikler ve çözümleme

- Top varsa: her takımın topa en yakın iki oyuncusu, 5 m içindeki oyuncu
  sayısı, topun hücum yönündeki konumu ve hızı. Top yoksa bunlar NaN olur.
- Top olmadan da çalışan: takımların ne kadar ileride olduğu, ileri hızı,
  yayılımı ve bunların farkı. 1/3 s merkezli ve 2 s geçmiş/gelecek pencereleri.
- Bozulma eğitimi: her eğitim maçı temiz + 3 kopya (oyuncu kaybı %0–50,
  gürültü 0–1.5 m; top kaybı %0–50, gürültü 0–1 m).
- Çözümleme (`decode`): P(H) yumuşatma, histerezis, kısa spell'leri öncekine
  katma, D üstte. Ayarlar yalnız doğrulama maçında spellF1 ile seçildi:
  pencere 0.5 s, marj 0, en kısa spell 1 s.

## Sonuçlar (organizatör puanlayıcısı, IDSSE)

Top duruşta silinmiş akış. Ağır bozulma: oyuncu %30 kayıp/0.8 m, top %30 kayıp/0.5 m.

| Maç | Akış | Temel + D spellF1 | Öğrenilmiş sahiplik + D spellF1 | macroF1 |
| --- | --- | --- | --- | --- |
| Doğrulama | temiz | 0.267 | **0.495** | 0.784 → 0.876 |
| Doğrulama | ağır | 0.166 | **0.417** | 0.673 → 0.836 |
| Ayrılmış | temiz | 0.328 | **0.599** | 0.794 → 0.884 |
| Ayrılmış | ağır | 0.235 | **0.492** | 0.701 → 0.838 |

Ayrılmış maç dondurmadan sonra bir kez değerlendirildi. Bunlar yarışma skoru
değildir.

## Sınırlar

- DFL'nin sahiplik tanımı yarışmanınkiyle aynı olmayabilir (örn. pas
  uçuşunda, ikili mücadelede).
- Model az spell üretiyor (doğrulamada 321'e karşı gerçek 511): kısa
  sahiplikleri birleştiriyor. Seçilen pencere ızgaranın en küçük değeri.
- Yarışma takibinin gürültü düzeyi bilinmiyor; geniş aralıkta eğitildi.

## Çalıştırma

```bash
python -m tools.train_learned_possession --plan learned-dead-ball-plan.json \
    --data /private/idsse --dball /private/learned-dead-ball-v2 \
    --scorer /private/organizer-eval --out /private/learned-possession-v1
```

MacBook Air M5'te ~4 dakika, tepe bellek ~3.3 GB (4 iş parçacığı).
