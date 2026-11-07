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

Sonraki ayrı deneyde topa bağlı özellikler tamamen çıkarılacak. Oyuncu hız
dağılımları ve takım kimliğinden bağımsız mekânsal yayılım kullanılacak.
Yeni aday dış maçlarda seçilecek; ilk deneyin kayıtları değiştirilmeyecek.
Metrica'nın olaydan türetilmiş kısmi duruş/canlı aralıkları başka sağlayıcı
kontrolü olarak kullanılabilir, fakat eksiksiz kare düzeyi gerçek sayılmaz.

İlk deneyde altı yeni testle toplam 231 test: 229 geçti, iki isteğe bağlı
AV testi atlandı. Hedef sızıntısı reddi, takım simetrisi, kayıp gözlemde
abstention, devre/kare sınırları, deterministik öğrenme ve D sınır ölçümü sınandı.
Donmuş temel model ve seçilmiş H/A zaman katmanı değiştirilmedi.
