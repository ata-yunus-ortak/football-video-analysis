"""Apply the v2.5 changes to docs/SAHIPLIK_V2_TR.md. Usage: doc_v25_tr.py USE_CLOCK(0/1)"""
import sys, json
from pathlib import Path
S = Path('/home/claude/sc')
use_clock = sys.argv[1] == '1'
b = json.loads(Path('/home/claude/work/exp_v25b.json').read_text())['summary']['good']
p = S / 'docs' / 'SAHIPLIK_V2_TR.md'
t = p.read_text()


def rep(old, new):
    global t
    assert t.count(old) == 1, old[:70]
    t = t.replace(old, new)


GIT_FILES_OLD = 'possession-v24-plan.json possession-v24-results.json requirements-possession.txt requirements-possession-train.txt SAHIPLIK-V2-URET.cmd SAHIPLIK-V24-URET.cmd'
GIT_FILES_NEW = ('possession-v24-plan.json possession-v24-results.json possession-v25-plan.json possession-v25-results.json '
                 'possession-v25b-plan.json possession-v25b-results.json possession-v26-plan.json possession-v26-results.json '
                 'possession-v25-release.json tests/test_possession_v25.py tests/test_possession_v26.py '
                 + ('tools/possession_clock.py SAAT-OKU.cmd ' if use_clock else '') +
                 'requirements-possession.txt requirements-possession-train.txt SAHIPLIK-V2-URET.cmd SAHIPLIK-V24-URET.cmd SAHIPLIK-V25-URET.cmd')
rep('''# Sahiplik v2.4 — dış veride seçilmiş H/A/D sistemi''', '''# Sahiplik v2.5 — dış veride seçilmiş H/A/D sistemi''')
rep('''doküman `TECHNICAL_DOCUMENT_V2.md` dosyasındadır. Teslim sistemi **v2.4**'tür. Çekirdeği v2.1
modelidir. v2.4 önce tracking'in konum titreşimini ölçer. Titreşim 0,30 m'yi aşmıyorsa v2.1'i
birebir çalıştırır, aşıyorsa yumuşatılmış konumlarla v2.3 yolunu çalıştırır (aşağıda
"v2.4: gürültü kapısı").''', '''doküman `TECHNICAL_DOCUMENT_V2.md` dosyasındadır. Teslim sistemi **v2.5**'tir. Çekirdeği v2.1
modelidir. v2.5 iki şey ekler:
- Tracking'in konum titreşimini ölçer. Titreşim 0,30 m'yi aşmıyorsa v2.1'i birebir
  çalıştırır, aşıyorsa yumuşatılmış konumlarla v2.3 yolunu çalıştırır (aşağıda "v2.4: gürültü
  kapısı").
- Yayın tracking'ini taktik zamana eşler''' + (''' (iki videodaki maç saatini okuyarak)''' if use_clock else '') + ''' ve taktik topun eksik olduğu
  kareleri yayın topuyla doldurur. Bunu yalnız iki kamera, ikisinin de topu gördüğü yerlerde
  çok yakın konum veriyorsa yapar (aşağıda "v2.5: yayın topuyla doldurma").''')
rep('''python -m possession.run24 --data-dir C:\\yol\\mtah2027-data --out C:\\yol\\yeni-cikti''',
    '''python -m possession.run25 --data-dir C:\\yol\\mtah2027-data --out C:\\yol\\yeni-cikti''')
sec = '''## v2.5: yayın topuyla doldurma (teslim sistemi, 10 Kasım)

**Neden?** Yalnız rapor amaçlı iki ölçüm hatanın yerini gösterdi:
- Temiz tracking'de puan 0,748, otomatik tracking benzeri bozulmada 0,610. Aynı bozulmada top
  hiç kaybolmasa 0,700 olurdu. Yani kaybın yaklaşık üçte ikisi topun kaybolmasından geliyor.
- "Top ölü mü" kararını doğru cevapla değiştirmek puanı yalnız 0,631'den 0,647'ye çıkarıyor.
  "Hangi takımda" kararını değiştirmek 0,912'ye çıkarıyor. Asıl hata oyun içindeki takım
  kararlarında; bunu da en çok eksik top bozuyor.

**Nasıl?**
1. Yayın karelerini taktik karelere eşle''' + (''': önce iki videodaki maç saati otomatik okunur
   (OCR, 5 saniyede bir). Saatten her yarı için kaba zaman farkı çıkar (±1 s). Sonra 60 s'lik
   pencerelerde top ve oyuncu konumlarıyla kare düzeyine inilir. Saat okunamazsa iki top
   yörüngesinin benzerliğinden aranır.''' if use_clock else ''': iki top yörüngesinin benzerliğinden
   her yarı için zaman farkı bulunur, 60 s'lik pencerelerde top ve oyuncu konumlarıyla
   kare düzeyine inilir.''') + '''
2. Bir yayın karesi, en az 3 oyuncusu taktikteki aynı takım oyuncularına 2 m içinde (ortanca)
   düşüyorsa kabul edilir. Tekrarlar ve yakın çekimler böylece elenir: tekrarda saat canlı
   akar ama görüntü eskidir, oyuncular tutmaz.
3. **Güven kapısı:** iki kameranın da topu gördüğü karelerde aradaki ortanca uzaklık
   0,50 m'den küçükse ve en az 120 s örtüşme varsa doldurma yapılır. Bu uzaklık taktik
   hatayı da içerdiği için yayın hatasına bir üst sınırdır.
4. Yalnız taktik topun eksik olduğu kareler doldurulur. Taktik top asla değiştirilmez.

**Doğrulama** (sentetik yayın akışları, 16 yeni kopya, yarışma puanı değil):

| Yayın tracking kalitesi | v2.4 | v2.5 | Kapı açıldı |
|---|---|---|---|
| İyi (sapma ≤ 0,2 m, gürültü ≤ 0,25 m) | 0,651 | 0,675 | 15/16 |
| Orta | 0,651 | 0,655 | 1/16 |
| Kötü | 0,651 | 0,651 | 0/16 |

İyi akışlarda puanlanan karelerde top görünürlüğü %53'ten %63'e çıktı. Bir kopyada yörünge
araması yanlış eksen çevirmesine ve sahte bir zaman farkına kilitlendi: eşleme olmadı, kazanç
kayboldu ama zarar da olmadı.''' + (f''' Saatle çapalanan sürüm (v2.5b), saat okumaları sentetik
olarak üretilmiş 16 yeni kopyada denendi: okunabilirlik %50-95, hatalı okuma %1-3, uzatma
dakikalarında saat tekrarı var. İyi akışlarda v2.4 {b['v2_4']:.3f}, v2.5 {b['v2_5']:.3f},
v2.5b {b['v2_5b']:.3f}; başarısız eşleme sayısı {b['alignment_failures']['v2_5']} → {b['alignment_failures']['v2_5b']}. Kayıtlı koşulları
geçtiği için saat çapası teslim sistemine girdi.''' if use_clock else ''' Saatle çapalanan sürüm (v2.5b) kayıtlı
koşullarını geçemedi; teslim sistemi saat okumasını kullanmıyor.''') + '''

**Dürüst sınırlar.**
- Yayın akışları sentetik. Gerçek yayın tracking'inin doğruluğunu bilmiyoruz; çalışma anında
  kapı karar veriyor. Kapının sonucunu (`run.json` içindeki `fusion`) asistana iletmeyin.
- Gerçek yayının simülatörde olmayan kusurları (yakınlaştırmaya bağlı hata, geçerli
  işaretlenmiş tekrar, kısmi görüşte takım karışması) sonucu değiştirebilir.
- Denenen v2.6 (öğrenilmiş "takım değişimi olasılığı" ile değişken geçiş maliyeti) yeni
  kopyalarda yalnız +0,002 getirdi ve seçilmedi.

'''
rep('''## Teslim adımları (ekip bilgisayarında)''', sec + '''## Teslim adımları (ekip bilgisayarında)''')
rep('''Kısayol: `SAHIPLIK-V2-KURULUM.cmd` (1. adım), `SAHIPLIK-V24-URET.cmd` (2-3. adımlar) ve''',
    '''Kısayol: `SAHIPLIK-V2-KURULUM.cmd` (1. adım), ''' + ('''`SAAT-OKU.cmd` (saat okuma, bir kez), ''' if use_clock else '') + '''`SAHIPLIK-V25-URET.cmd` (2-3. adımlar) ve''')
rep('''2. Dosyayı üret: `SAHIPLIK-V24-URET.cmd` (veri yolu `MTAH_DATA_DIR` ile) veya
   `python -m possession.run24 --data-dir <veri kökü> --out <yeni klasör>`. Veri kökü,''',
    '''2. Dosyayı üret: ''' + ('''önce bir kez `SAAT-OKU.cmd` çalıştırın. Ayrı bir OCR ortamı (`.venv-sync`)
   kurar ve iki videonun saatini okur; sonuç `%USERPROFILE%\\FootballPrivate\\possession-clock`
   altına yazılır, görüntü kaydedilmez, bu dosyalar asistana gönderilmez. Sonra ''' if use_clock else '') + '''`SAHIPLIK-V25-URET.cmd` (veri yolu `MTAH_DATA_DIR` ile) veya
   `python -m possession.run25 --data-dir <veri kökü> --out <yeni klasör>''' + (''' --tactical-clock <saat>\\tactical --broadcast-clock <saat>\\broadcast''' if use_clock else '') + '''`. Veri kökü,''')
rep(GIT_FILES_OLD, GIT_FILES_NEW)
rep('''   git commit -m "Add possession v2.4: noise-gated v2.1 / v2.3 H/A/D system"''',
    '''   git commit -m "Add possession v2.5: noise-gated v2.1 / v2.3 H/A/D system with gated broadcast ball fill"''')
p.write_text(t)
print('ok')
