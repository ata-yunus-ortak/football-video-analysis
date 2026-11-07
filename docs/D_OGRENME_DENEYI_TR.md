# Öğrenilmiş duran top deneyi — 7 Kasım 2026

İlk deney tamamlandı: dört Sportec eğitim maçı, iki ayrı doğrulama maçı;
48 aday, hedefler özelliklerden ayrı. Kod yalnız NumPy kullanır.
BallStatus/BallPossession, olay etiketleri ve maç saati girdiye alınmaz.
Plan `dead-ball-selection-plan.json`; ham veriler özel çalışma dizinindedir.

**Bu aday final sisteme alınmadı.** Sayısal kabul koşullarını geçmesine rağmen,
aktarım denetimi önemli bir veri özelliği buldu: dört eğitim maçında ölçülebilen
D karelerinin tamamında koordinattan türetilen top hızı tam sıfırdır.
Sağlayıcının duruşlarda top koordinatını sabitlemiş olması mümkündür; bu işlem
sağlayıcıdan doğrulanmış değildir. Modelin en güçlü özellikleri top hızlarıdır.
Topun duruş sırasında da hareket edebildiği farklı bir otomatik tracking
kaynağına bu başarıyı doğrudan taşımak savunulamaz.

Temiz doğrulamada D F1 değerleri 0,9948 / 0,9952 ve 1 saniye toleranslı sınır
F1 değerleri 0,9619 / 0,9834 çıktı. Bunlar kaynak içi ölçümlerdir; yarışma
başarısı, gerçek görüntü doğruluğu veya genel geçer D başarısı değildir.
Yapay eksik gözlem testi bu sabit koordinat özelliğini ortadan kaldırmadığından
tek başına aktarım sorununu çözmez. Tam sonuçlar
`dead-ball-external-results-v1.json`; denetim `dead-ball-transfer-audit.json`.

## D004: yalnız oyuncu hareketleri

İkinci deney tamamlandı. Top konumu, hızı, yakınlığı ve kayıp bilgisi
özelliklerden tamamen çıkarıldı. Oyuncu hız çeyrekleri ve mekânsal yayılımın
anlık ve 0,4/1,6 saniyelik özetleri kullanıldı. Aynı dört eğitim ve iki
doğrulama maçı yeniden kullanıldı; yeni bağımsız test iddiası yoktur.
18 adaydan seçilen tanısal aday: L2=0,001, D olasılık eşiği=0,65,
zamansal geçiş maliyeti=1 saniye. Özellikler hedef/olay bilgisi almaz.

| Dış doğrulama | D F1 | Sınır F1, ±1 saniye | H/A/D bölüm F1: D olmadan → adayla |
| --- | ---: | ---: | ---: |
| J03WN1 | 0,8781 | 0,3430 | 0,2242 → 0,3184 |
| J03WR9 | 0,8577 | 0,4195 | 0,2846 → 0,3788 |

**Bu aday da final sisteme alınmadı.** Ön kayıtlı ortalama sınır F1≥0,50
koşuluna karşı 0,3812 elde edildi. Duran oyunun genel aralığını yakalamak,
tam durma ve başlama anını yeterince doğru bulmak anlamına gelmiyor.
Sonuç görüldükten sonra kabul eşiği değiştirilmedi.

Sabit aday ayrıca iki Metrica maçında değerlendirildi. Tahminler olay hedefleri
puanlanmadan önce donduruldu. Eşleştirilmiş BALL OUT/SET PIECE aralıkları D,
yalnız geçerli PASS aralıkları canlı oyun proxy'si; diğer kareler bilinmeyen
bırakıldı. D F1: **0,8497 / 0,7888**. Bunlar kısmi, daha önce erişilmiş
verilerdir; pas aralıkları bütün canlı oyunu temsil etmez. Bu kontrol tam
maç kesinliğini veya sınır doğruluğunu doğrulamaz ve kabul kararını değiştirmez.

Plan: `player-dead-ball-selection-plan.json`. Özetler:
`player-dead-ball-external-results-v1.json`,
`player-dead-ball-transfer-results-v1.json`. İki deney için nihai terfi kararı
`dead-ball-promotion-decisions.json` içindedir; D003 raporundaki sayısal
`accepted_external_candidate` tek başına final sürüm onayı değildir.

Tekrarlama, ham veriler hazırlandıktan sonra, yeni özel çıktı dizinleriyle:

```powershell
python -m tools.player_dead_ball_selection --prepared /private/sportec-prepared --plan player-dead-ball-selection-plan.json --out /private/new-study
python -m tools.player_dead_ball_recheck --candidate /private/study/candidate-freeze.json --audit /private/metrica-audit --data /private/metrica-data --out /private/new-recheck
```

236 test: 234 geçti, iki isteğe bağlı AV testi atlandı. Top verisini değiştirme
testi oyuncu özelliklerinin aynı kaldığını; kısmi proxy testleri çakışmaların
ve devre dışındaki pasların etiketlenmediğini doğruladı. Ayrılmış J03WMX
test maçı açılmadı. Görüntü temelli karar ve iki kamera başarısı bu deneyle
ölçülmüş değildir. Sıradaki ihtiyaç, izinli dış veride daha güvenilir top
gözlemleri ve bağımsız durma/başlama kanıtıdır.

İlk deneyde altı yeni testle toplam 231 test: 229 geçti, iki isteğe bağlı
AV testi atlandı. Hedef sızıntısı reddi, takım simetrisi, kayıp gözlemde
abstention, devre/kare sınırları, deterministik öğrenme ve D sınır ölçümü sınandı.
Donmuş temel model ve seçilmiş H/A zaman katmanı değiştirilmedi.
