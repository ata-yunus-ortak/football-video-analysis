# Sahiplik başlangıç/bitiş ölçümü — 8 Kasım 2026

Sahiplik aralıklarının genel örtüşmesi, geçiş zamanlarının doğru olduğunu
tek başına göstermez. Yeni ölçüm H→A ve A→H değişimlerini ayrı yönlerde,
aynı devre ve kesintisiz bilinen hedef bloklarında değerlendirir. Bir takımın
bitişi diğerinin başlangıcıdır; aynı değişim iki başarı olarak sayılmaz.

0,2 / 0,5 / 1 / 2 saniye toleranslarında bire bir eşleştirme yapılır.
Dinamik program önce eşleşme sayısını artırır, eşitlikte toplam mutlak
zaman hatasını azaltır. F1, kesinlik, duyarlılık, imzalı ortalama hata ve
eşleşenlerin mutlak hata P90 değeri raporlanır. Eşleşmeyen geçişler F1'i
düşürür; yalnız eşleşenlerin küçük zaman hatası başarı diye sunulmaz.

Kayıp hedefler değerlendirme bloklarını keser. H–X–A tahmini tek kesin
zaman sayılmaz: önceki gözlemden sonraki kare ile ilk yeni takım karesi
arasındaki belirsizlik aralığı ayrı verilir. Sahiplik çizelgesi yarı açık
aralıklar kullanır: başlangıç dahil, bitiş hariç. X sürelerine sahiplik
atanmaz; X duran top değildir. Devre/kare kopmaları birleştirilmez.
Aralık sınırlarının kayıp veya kayıt başlangıcı/sonu nedeniyle belirlenemediği
durumlar `start_censored` / `end_censored` alanlarıyla belirtilir.
Kesin komşu etiket değişimi de gerçek temas doğruluğu iddiası değildir.

## Deney S002

Ön kayıt: `possession-boundary-plan.json`. Önceki dış veriyle seçilmiş
ölçüm özellikleri sabit tutuldu; yalnız takım değiştirme maliyeti
0 / 0,025 / 0,05 / 0,1 / 0,25 / 0,5 saniye karşılaştırıldı.
Dört eski SkillCorner doğrulama maçı kullanıldı. Tahminler hedef puanlamadan
önce kaydedilip hash ile sabitlendi. Oyuncu kimliği, D ve görüntü modeli
bu deneyin kapsamı değildir. Hedefler otomatik sağlayıcı tahminidir;
insan tarafından doğrulanmış top temasları veya resmî yarışma skoru değildir.

| Değişim maliyeti | Ortalama 0,5 s geçiş F1 | Ortalama aralık F1 proxy |
|---:|---:|---:|
| 0,25 (mevcut aday) | 0,11277 | 0,48388 |
| 0 | 0,12705 | 0,09860 |
| 0,025 | 0,16856 | 0,30809 |
| 0,05 | 0,15870 | 0,38598 |
| 0,1 | 0,14109 | 0,45931 |
| 0,5 | 0,09706 | 0,47340 |

Mevcut adayda dört maçta toplam 901 doğrudan sağlayıcı geçişine karşı
534 doğrudan tahmin var; bunların 81'i yarım saniye içinde eşleşiyor.
Bu sonuç **kusursuza yakın sınır doğruluğunu desteklemiyor**. Daha hızlı
değişim ayarları geçiş ölçümünü artırırken sahiplik aralıklarını parçalıyor.
Geçiş F1'inde en az 0,03 artış, aralık F1'inin en az %99'unun korunması
ve H/A makro F1 kaybının en fazla 0,005 olması koşullarını hiçbir aday
birlikte geçmedi. Yeni model seçilmedi; ayrı maç kontrolü açılmadı.

Makine tarafından okunabilir sonuç: `possession-boundary-results-v1.json`.
Kare düzeyindeki tahminler ve zaman çizelgeleri yalnız özel çıktı dizininde.
Çizelge dışa aktarımı eklendikten sonra tekrar çalıştırmada ölçümler bire bir
aynı kaldı. 283 test: 281 geçti, iki isteğe bağlı AV testi atlandı.
Yeni testler eşleştirme, yön, boşluk, devre/kare kopması ve aralık uçlarını kapsar.
Dondurulmuş temel model korunur; Barcelona verisi okunmadı.

```powershell
python -m tools.possession_boundary_study --study /private/sequence-study --recheck /private/sequence-recheck --out /private/new-boundary-study
```

Sonraki gereksinim yalnız daha düşük değişim maliyeti değildir: doğrudan
temas/kontrol kanıtının ve geçiş hedeflerinin doğrulanması gerekir. Sağlayıcı
sahiplik etiketi ile fiziksel temas anının aynı tanımda olduğu varsayılmamalı.
Görüntü, oyuncu kimliği ve D sınırları için ayrı dış doğrulama tamamlanmadan
bu takım düzeyi proxy sonuçları o alanların başarısı sayılmayacak.
