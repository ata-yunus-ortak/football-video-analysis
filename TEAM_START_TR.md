# Ekip için başlangıç

Bu dal, More Than a Hack 2027 için temiz tracking/sahiplik geliştirmesidir.
Varsayılan daldaki eski portföy projesinden ayrı bir Git geçmişiyle korunur.

## Kurulum

```bash
git clone --branch develop/dead-ball-data-audit --single-branch https://github.com/ata-yunus-ortak/football-video-analysis.git
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

Deneysel katmanlar uygulanmıştır; bütün eşikleri gerçek dış maçlarda seçilmiş
ve doğrulanmış yeni bir teslim modeli henüz değildir. Sentetik test ayarlarını
doğrulanmış futbol parametresi diye kullanma. Ayrıntılar ilgili `docs/` belgelerinde.

## Birlikte geliştirme

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
