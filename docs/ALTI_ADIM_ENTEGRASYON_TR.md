# Altı adımın sıralı entegrasyonu

Bu geliştirme dondurulmuş `clean_model/` ve `model.json` yerine ayrı deneysel
bir görüntü sahipliği hattıdır. Barcelona çıktısı/görüntüsü geliştirme girdisi
değildir. Kod entegrasyonu ile dış doğruluk onayı ayrı kaydedilir.

1. Temas, oyuncu kontrolü, takım sahipliği, uçuş, mücadele, belirsiz ve D
   durumlarının ayrı veri sözleşmesi ve durum makinesi.
2. İzinli dış maçlarda kaynak hash'i, maç ayrımı ve belirsiz geçiş aralığı
   taşıyan bağımsız referans protokolü; eksik referans başarı sayılmaz.
3. Görüntüdeki ölçülmüş top/oyuncu hareketi, yaklaşma, birlikte hareket ve
   yön değişimini birleştiren kanıt çıkarımı; tahminler kontrol üretmez.
4. Kararın doğrulandığı zamanı ilk desteklenen kontrol anından ayıran
   çevrimdışı çözümleme; boşluk ve kamera değişiminde kanıt sıfırlama.
5. Kaynak maç 2 eğitim, 3 doğrulama, 5 ayrılmış son kontrol. Görüntü erişimi
   öncesi kayıt; test referansları aday dondurulmadan değerlendirilmez.
6. Mevcut doğrulanmış kamera eşleme kapılarına bağlantı; otomatik tag yalnız
   duruş arama aralığı. Ölçülmüş durma/başlama kanıtı ayrıca gerekir.
   Her bileşen ayrı aç/kapat çalıştırılır, sonuçlar ayrı değerlendirilir.

Her adım kendi testiyle tamamlanacak. İnsan temas referansı, eşzamanlı iki
kamera veya doğrulanmış kimlik girdisi olmayan dış veri için başarı değeri
uydurulmayacak; ilgili dış doğrulama açık kalacak.

## Uygulanan bağlantılar

| Adım | Kod | Durum |
|---|---|---|
| 1 | `control_states.py`, `control_decoder.py` | Temas ayrı olay; oyuncu kontrolü, takım sahipliği, uçuş, mücadele, bilinmeyen ve D ayrı. Uçuşta oyuncu sahibi yok. |
| 2 | `transition_benchmark.py`, `control_review_pack.py` | Dış kaynak/hash, maç ayrımı, zaman aralığı, değerlendirme kapsamı ve referans doğrulaması. Boş referans reddedilir. |
| 3 | `control_evidence.py` | Görüntü yakınlığı, yaklaşma, göreli hareket ve yön değişimi. Tracking topu/sağlayıcı sahipliği girdi değil. |
| 4 | `control_decoder.py` | Karar zamanı ile başlangıç ayrı. İlk desteklenen kareye geriye yerleştirme; kayıt/kayıp uçlarında sansür işareti. |
| 5 | `control_external_acquisition.py`, `control-external-acquisition-plan.json` | Maç 2/3'ten 250'şer ardışık kare; maç 5 görüntüleri ayrılmış durumda. |
| 6 | `control_tag_gate.py`, `control_experiment.py`, `control_ablation.py` | Mevcut kamera doğrulamasına bağlantı, tag + ayrı görüntü stop kanıtı, restart ve beş kapatma deneyi. |

`control-development-plan.json` ayarları sentetik mühendislik değerleridir;
dış maçta seçilmiş optimum değerler değildir. Yeni hat ayrı ve
`selected_release=false`; dondurulmuş ana model değişmez.

Ortak görüntü ötelemesi oyuncu hareketlerinin medyanıyla azaltılır; bu genel
pan/zoom veya top yüksekliği çözümü değildir. Kimlik/zaman/geometri doğrulanmazsa
kontrol üretilmez. Yön değişimi tek başına temas sayılmaz. Kamera, iz, devre
ve kare kopmaları kanıtı sıfırlar. Tahmin konumu gerçek top ölçümü yapılamaz.

D katmanı, tag aralığı yanında kaynağa/kareye bağlı doğrulanmış otomatik
görüntü duruş sinyali (`ball_exit` / `referee_stop`) ve hareketsizlik ister.
Sinyal yoksa D üretmez. Bu sözleşme, yeni bir hakem/çizgi geçişi dedektörünün
doğrulandığı iddiası değildir. Başlama, ölçülen hareketle ayrıca doğrulanır.
D kanıtı taktik kaynak saatinde tutulur; yayın saatine kontrolsüz kopyalanmaz.

## Çalıştırma

```powershell
python -m tools.control_experiment --tactical-manifest /external/tactical-camera-manifest.json --plan control-development-plan.json --out /private/control-run
python -m tools.control_ablation --tactical-manifest /external/tactical-camera-manifest.json --plan control-development-plan.json --out /private/control-ablations
```

Yayın için `--broadcast-manifest` ve `--pair-alignment` birlikte verilir.
`--tags-manifest`: aynı fixture/otomatik origin, tags/signals mutlak yolları
ve SHA-256 alanları. Tag kaydı: `source_id`, `epoch`, `start_s`, `end_s`,
`code`, `tags`, `origin`. Sinyal kaydı: kaynak, kare, epoch, kind,
`origin=automatic_image_measurement`, `measurement=true`, `verified=true`.

Çıktılar kare başına durum/takım/oyuncu/kanıt ve ayrı temas-pas-top kaybı,
kontrol başlangıç/bitiş adaylarıdır. `confirmed_at_frame` kararın ne zaman
doğrulandığını taşır; kayıt sonunda kontrol bitişi doğrulanmış sayılmaz.

Aç/kapat aracı tam hat; yeni hareket kanıtı yerine önceki kontrol yolu;
geriye yerleştirme kapalı; uçuş sürekliliği kapalı; yayın kapalı ve tag kapalı
olmak üzere altı ayrı çalıştırma üretir. `--reference` geçerli bağımsız dış
referans verildiğinde olay F1/kaçırılan/fazla olay hesabını açar. Tahminler
puanlamadan önce dondurulur. Geliştirme komutu recheck referanslarını açmaz.
Sansürlü uçlar kesin olay sayılmaz; kapsam dışı tahminler ayrı raporlanır.

## Gerçekleştirilen kontroller ve açık doğrulama

SNGS-021 (maç 2) ve SNGS-040 (maç 3): 10'ar saniye, 500 JPEG üyesi.
CRC/SHA doğrulandı; tam ZIP hash'i doğrulanmadı. Kayıpsız videolar yeniden
çözülerek bütün RGB kare hash'leri doğrulandı. Kare saati açıkça 25 fps;
gerçek yayın PTS iddiası yok. Seyrek kayıtlar video adaptöründe reddedilir.
Referans şablonları **boş ve değerlendirilemez**; kutular temas gerçeğine
dönüştürülmedi. Maç 5 görüntüleri indirilmedi.

Sentetik iki kamera senaryosunda altı çalıştırma tamamlandı. Tam hat son dört
karede A kontrolü, yayın kapalı hat taktik kameranın H kontrolünü verdi.
Geriye yerleştirme kapalıyken doğrulama bekleme kareleri X kaldı. Bunlar
bağlantı testleri, futbol doğruluk skorları değildir. Stop/restart, tagin
tek başına D yapmaması, uçuş, belirsizlik, kaynak kopması ve temas/kontrol
ayrımı test edildi. Özet: `control-integration-results-v1.json`.

**Altı adımın kodu bağlı; gerçek maç doğruluğu henüz doğrulanmış değil.**
Bağımsız temas/kontrol referansı, doğrulanmış dış otomatik oyuncu kimliği
ve eşzamanlı iki kamera verisi hâlâ gerekiyor. Bu eksikler sentetik başarı
veya sağlayıcı proxy'siyle kapatılmadı. Ana modele terfi yapılmadı.
