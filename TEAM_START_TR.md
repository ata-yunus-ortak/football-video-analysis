# Ekip için başlangıç

Bu dal, More Than a Hack 2027 için temiz tracking/sahiplik geliştirmesidir.
Varsayılan daldaki eski portföy projesinden ayrı bir Git geçmişiyle korunur.

Güncel çalışma ve kural önceliği: [OTONOM_GELISTIRME_TR.md](docs/OTONOM_GELISTIRME_TR.md).
Sağlanan maçın çıktısını videoyla karşılaştırmayın; önceki çizimli yerel
gösterimler doğrulama yöntemi değildir. Yeni dış maç çalışmasının kodu ve
özet sonuçları bu daldadır; donmuş temel model korunur.

7 Kasım D deneylerinin ikisi de final sürüme alınmadı: ilkinde sağlayıcıya
özgü sabit top örüntüsü riski, oyuncu-temelli ikincisinde yetersiz sınır
doğruluğu bulundu. [Ölçümler ve tekrarlama](docs/D_OGRENME_DENEYI_TR.md).
`dead-ball-promotion-decisions.json` nihai kararı belirtir. Deney raporundaki
sayısal kabul alanı tek başına teslim modeli seçildiği anlamına gelmez.

8 Kasım görüntü çalışması: [top adayı filtresi, konum denetimi ve dış veri
eğitim hattı](docs/TOP_ADAYI_DENEYI_TR.md). Filtre henüz varsayılan modele
alınmadı; yeni dedektör eğitimi ayrı deneydir. Ham görüntüler ve ağırlıklar
bu depoda dağıtılmaz.

## Kurulum

```bash
git clone --branch feature/external-possession-selection --single-branch https://github.com/ata-yunus-ortak/football-video-analysis.git
cd football-video-analysis
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m tools.tracking_viewer --demo --port 8766 --open
```

Linux/macOS'ta aktivasyon: `source .venv/bin/activate`. Sentetik örnek ve
testler için maç verisi veya model ağırlığı gerekmez. Windows'ta ortam
etkinken `TRACKING-DEMO.cmd` de kullanılabilir.

## Maç verisi ve yerel oynatıcı

Her ekip üyesi erişim hakkı bulunan maç paketini organizatörün indirme
kanalından edinir. Veri, video, Smart Tagging XML, homography, tahmin veya
kare düzeyindeki türetilmiş dosyalar GitHub'a konulmaz.

Windows'ta `viewer-local.example.cmd` dosyasını `viewer-local.cmd` olarak
kopyala; kendi veri/video yollarını yaz ve `TRACKING-IZLE.cmd` çalıştır.
Yerel ayar dosyası Git tarafından yok sayılır. Video farklı yerdeyse `MTAH_VIDEO`
ile belirtilebilir; bulunmazsa arayüzde “Video seç” kullanılabilir.

Diğer sistemlerde:

```bash
python -m tools.tracking_viewer --meta /private/bundle/tactical/BAR-ATH_tactical_atd.xml --tracking /private/bundle/tactical/BAR-ATH_tactical_atd.txt --video /private/BAR-ATH_tactical.mp4 --smart-tagging /private/bundle/tactical/BAR-ATH_tactical_smart_tagging.xml --open
```

Tracking: `http://127.0.0.1:8765`. Smart Tagging:
`http://127.0.0.1:8765/#smart-tagging`. Yerel oynatıcı modelleri çalıştırmaz,
elle doğruluk etiketi/düzeltme toplamaz ve veriyi harici servise yüklemez.

## Kod nerede?

| Konum | Görev |
| --- | --- |
| `clean_model/`, `model.json` | Hash ile korunan dondurulmuş H/A/X karşılaştırma modeli |
| `development/motion_possession.py` | Deneysel sahiplik birleştirme katmanı |
| `development/player_motion.py` | Oyuncu/top birlikte hareketi ve takım hızları |
| `development/team_transitions.py` | Takım hareketi değişimi bağlamı |
| `development/set_piece_dead_ball.py` | SET PIECES ve ölçülmüş bekleme/başlangıç |
| `development/long_ball.py` | LONG BALL aralığında uzun/hızlı hareket ve yakınlık engeli |
| `tools/tracking_viewer.py`, `viewer/` | Yerel tracking/video/Smart Tagging arayüzü |
| `tools/motion_experiment.py` | Kayıtlı dış verilerde deney çalıştırıcısı |
| `tests/` | Sentetik ve bütünlük testleri |
| `docs/DENEY_KAYDI_TR.md` | Deneylerin veri, seçim ve doğrulama durumu |
| `development/visual_possession.py` | Görüntüden kontrol/sahiplik adayı ve kamera tercihi |
| `tools/visual_identity_context.py` | Tracking/XML'den yalnız oyuncu kimliği bağlamı |
| `tools/visual_possession_experiment.py` | Dış/sentetik veride görüntü temelli H/A/X çalıştırıcısı |
| `tools/visual_long_review.py`, `tools/visual_review_server.py` | Yerel ilk beş dakika gösterimi ve seçilen oyuncu vurgusu |

Deneysel katmanlar uygulanmıştır; bütün eşikleri gerçek dış maçlarda seçilmiş
ve doğrulanmış yeni bir teslim modeli henüz değildir. Sentetik test ayarlarını
doğrulanmış futbol parametresi diye kullanma. Ayrıntılar ilgili `docs/` belgelerinde.

## Yeni görüntü/sahiplik akışını çalıştırma

Görüntü için ayrı Python 3.10+ ortamı kullan:

```powershell
python -m venv .venv-vision
.\.venv-vision\Scripts\Activate.ps1
python -m pip install -r requirements-vision.txt
python -m tools.vision_weights --size nano --out D:/football-private/nano-weights
```

CPU kurulumu ve tam bağımlılık sürümleri için `docs/UYGULAMA_PLANI_TR.md` ve
`requirements-vision-lock.txt` dosyalarını kullan. GPU paketini kendi kart/sürücü
uyumluluğuna göre ayrı ortamda kur; bir arkadaşın ortamını veya sürücüsünü
otomatik değiştirme. Örnek kaynak kaydı ve dış veri edinme adımları
`docs/GORUNTU_ISLEME_TR.md`, `docs/SOCCERNET_ASAMALARI_TR.md` içindedir.

İşlem sırası: kayıtlı dış video tespiti → `tools.match_analysis` ile zamansal
top takibi → `tools.visual_identity_context` ile oyuncu/takım bağlamı →
`tools.visual_possession_experiment`. Ayrıntılı sözleşme ve komutlar
`docs/GORUNTU_TEMELLI_SAHIPLIK_TR.md` içindedir. Tracking topu ve eski sahiplik
etiketleri bu yeni karar yoluna girmez. Eşleme/geometri/canlılık kanıtı yoksa X
kalması beklenir; doğrulama bayraklarını sırf sonuç almak için true yapma.

Kullanıcının yalnız yerel inceleme talebine özel ilk beş dakika aracı:

```powershell
python -m tools.visual_long_review --alignment D:/football-private/alignment.json --external-run D:/football-private/completed-native-external-run --clock D:/football-private/automatic-clock/observations.jsonl --ball-plan ball-tracking-plan.json --owner-plan visual-possession-plan.json --out D:/football-private/new-first-five-review --device cpu --local-review
python -m tools.visual_review_server --root D:/football-private/new-first-five-review --broadcast-video D:/football-private/BAR-ATH_broadcast.mp4 --port 8777
```

Sunucu ikinci terminalde çalışabilir; hazır parçalar `http://127.0.0.1:8777/`
adresinde görünür. Kaynak yollarını kendi yetkili dosyalarına göre değiştir.
Tamamlanmış dış koşunun kayıt/hash dosyaları da kendi kurulumundan üretilmelidir;
depoda maç verisi veya arkadaşının özel manifesti bulunmaz. Bu inceleme komutu
eğitim/seçim aracı değildir; varsayım görünümü doğrulanmış sahiplik değildir.
Detaylar: `docs/ILK_BES_DAKIKA_YEREL_TR.md`.

## Birlikte geliştirme

Görüntüden otomatik tespit eklemek için adaylar, kod/ağırlık lisansları ve
önerilen dış maç deneyleri:
[açık kaynak görüntü araştırması](docs/ACIK_KAYNAK_GORUNTU_ARASTIRMASI_TR.md).
Bu liste yeni bir modelin kurulmuş veya seçilmiş olduğu anlamına gelmez.

Erişim süresi entegrasyonu ve yerel görüntü/iki video çalışmasının adımları:
[uygulama planı](docs/UYGULAMA_PLANI_TR.md). Deneysel kodlar
`feature/reachability-vision` dalındadır; donmuş teslim modeli korunur.

```bash
git switch -c feature/kisa-aciklama
python -m unittest discover -s tests -v
git add <degistirilen-kaynak-dosyalari>
git commit -m "Describe the change"
git push -u origin feature/kisa-aciklama
```

Bu geliştirme dalı hedefli pull request aç. Push erişimin yoksa fork üzerinden
PR açabilirsin; doğrudan ekip erişimini repo sahibi GitHub'dan verebilir.
Geçmişi zorla değiştirme veya eski portföy dalını bu temiz dala birleştirme.
Karşılaştırma kaynağı `baseline/remediated-external-v1` etiketi ve başlangıç
commit'i `8962134`'tür. Dondurulmuş kaynak hash'lerini kontrolleri aşmak için
güncelleme.

Önce `AGENTS.md` ve `docs/GELISTIRME_TR.md` oku. Eşik/model seçimlerini
izinli başka maçlarda yap; yarışma maçının elle işaretlemelerini, public
skorlarını veya belirli karelere özel kuralları seçim girdisi yapma.
Her deneyde kaynak/sürüm, maç ayrımı, ayarlar ve seçim gerekçesini kaydet.
Sağlayıcı temizliğinin tamamlandığı doğrulanmış değildir; REMEDIATION.md
ve TECHNICAL_REPORT.md içindeki geçmiş/durum açıklamaları geçerlidir.
