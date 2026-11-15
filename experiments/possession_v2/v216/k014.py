"""Write log entry K014 (Turkish) from possession-k014-error-patterns.json and put it at the top of docs/DENEY_KAYDI_TR.md.
Usage: k014.py REPO_DIR"""
import json, sys
from pathlib import Path
REPO = Path(sys.argv[1])
r = json.loads((REPO / 'possession-k014-error-patterns.json').read_text())
tr = lambda x, nd=3, sign=False: (f'{x:+.{nd}f}' if sign else f'{x:.{nd}f}').replace('.', ',').replace('-', '−')
pc = lambda x: f"%{round(100 * x)}"
o, L, K, T = r['overall'], r['loss_by_length'], r['loss_by_kind'], r['tested_on_the_development_copies']
miss, part, spur = K['true possessions not matched at IoU 0.3'], K['matched pairs with partial credit (both sides)'], K['predicted possessions not matched at IoU 0.3']
tv = r['turnovers_found_and_timed']; ub = r['upper_bounds_with_the_labels_as_oracle']
st = T['learned combination of both model families, leave one match out (exploration only)']
sem = T["minimum possession length in labels and prediction (reading of the organisers' rule that a touch without control is no change of possession)"]
cc = T['contact evidence added to the decoder (12 settings)']; cr = T['reception rule that re-times turnovers (24 settings)']
dec = T['decoder constants (difference to the release constants)']
bm = T["weak signals inside predicted possessions (bumps of the other team's probability), by peak"]
short_share = L['under 1 s']['share_of_true_possessions'] + L['1-2 s']['share_of_true_possessions']
short_loss = L['under 1 s']['share_of_loss'] + L['1-2 s']['share_of_loss']
rows_len = '\n'.join(f"| {nm} | {pc(v['share_of_true_possessions'])} | {tr(v['mean_credit'], 2)} | {pc(v['share_of_loss'])} | {pc(v['share_of_predicted_possessions'])} | {tr(v['mean_credit_of_predicted'], 2)} |"
                     for nm, v in zip(('1 sn altı', '1-2 sn', '2-4 sn', '4-8 sn', '8 sn üstü'), L.values()))
rows_m = '\n'.join(f"| {m} | {v['copies']} | {tr(v['spell_f1'], 3)} | {v['true_per_copy']} / {v['predicted_per_copy']} | {pc(v['loss_share_true_under_2s'])} | {pc(v['loss_share_partial_pairs_both_sides'])} | {pc(v['loss_share_spurious_predicted'])} |"
                   for m, v in r['per_match'].items())
def trow(src, k):
    v = tv[src][k]
    return f"{pc(v['found_within_3s'])} / {pc(v['within_0.5s'])}"
text = f"""## K014 — Hata örüntüleri: puanı nerede kaybediyoruz, ortak nedenler ve bunlara dayalı denemeler (sürüm değişmedi), 15 Kasım 2026

**Neden.** Takım lideri 15 Kasım 03:42'de şunu istedi: sistemin yanlış yaptığı yerleri bul, ortak örüntüyü çıkar, buna göre yeni
yöntemler geliştir ve bunları başka maçlarda dene. Bu kayıt o çalışmadır. Yalnız geliştirme ve raporlamadır: plan kaydedilmedi,
doğrulama yapılmadı, hiçbir şey seçilmedi, teslim sistemi **v2.15** olarak kaldı. Sağlanan maç açılmadı. Sayılar:
`possession-k014-error-patterns.json`; betikler: `experiments/possession_v2/v216/`.

**Veri ve yöntem.** Önceki doğrulamalarda puanlanmış 42 geliştirme kopyası (J03WN1 10, J03WR9 10, Metrica 1 10, Metrica 2 10,
Metrica 3 2; 9'u ekibin ikinci bozma benzeticisiyle). Bu kopyalardaki olasılıkları üreten modeller o maçları eğitimde görmedi.
Organizatörün eşleştirmesi birebir yeniden yazıldı (42 kopyada resmî puanla aynı). Bir sahipliğin "kredisi" = beş IoU eşiğinden
kaçında eşleştiği. spellF1 = 2 × toplam kredi / (gerçek + tahmin edilen sahiplik sayısı) olduğu için, kayıp (1 − spellF1) her
gerçek ve her tahmin edilen sahipliğin (1 − kredi) payına tam olarak bölünür. Böylece "kaybın yüzde kaçı nereden" sorusu kesin
yanıtlanır.

**Genel tablo.** {format(o['true_possessions'], ',').replace(',', '.')} gerçek, {format(o['predicted_possessions'], ',').replace(',', '.')} tahmin edilen sahiplik; spellF1 {tr(o['spell_f1_pooled_over_possessions'])}. Kaybın {pc(o['loss_true_side'] / (o['loss_true_side'] + o['loss_predicted_side']))}'i gerçek
sahiplik tarafında (bulamadıklarımız ve yarım eşleşenler), {pc(o['loss_predicted_side'] / (o['loss_true_side'] + o['loss_predicted_side']))}'u tahmin tarafında (fazladan ya da yarım eşleşen tahminler).

| gerçek sahipliğin süresi | gerçeklerin payı | ortalama kredi | kaybın payı | tahminlerin payı | tahminlerin kredisi |
|---|---|---|---|---|---|
{rows_len}

| kaybın türü | kaybın payı |
|---|---|
| hiç eşleşmeyen gerçek sahiplik (gerçeklerin {pc(miss['share_of_true'])}'si) | {pc(miss['share_of_loss'])} |
| — tahmin o sırada öteki takımı gösteriyor | {pc(miss['prediction says the other team'])} |
| — tahmin aynı takımı gösteriyor ama parça birleşmiş ya da kaymış | {pc(miss['prediction says the same team, merged or misaligned'])} |
| — tahmin ölü top diyor | {pc(miss['prediction says dead ball'])} |
| bulunan ama sınırları tutmayan çiftler (iki taraf birlikte) | {pc(part['share_of_loss'])} |
| hiç eşleşmeyen tahmin (tahminlerin {pc(spur['share_of_predicted'])}'si) | {pc(spur['share_of_loss'])} |

**Örüntü 1: kısa sahiplikler.** 2 saniyeden kısa sahiplikler gerçeklerin {pc(short_share)}'u, kaybın {pc(short_loss)}'i. Tipik durum: A takımı
oynarken B bir-iki saniyeliğine topu alır, sonra yine A. Sistem bunu tek bir A sahipliği olarak yazar; hem B'nin kısa sahipliği
hem de A'nın iki parçası kaybolur. Bu kısa sahipliklerde iki model ailesinin doğru takıma verdiği ortalama olasılık yalnız
{tr(miss['mean pooled probability of the right team in those'], 2)}: yani mesele çözücünün yumuşatması değil, modellerin bunu hiç görmemesi.

**Örüntü 2: zamanlama.** Bulunan sahipliklerde kaybın {pc(part['share_of_loss'])}'u sınırların yerinden. İki tarafı da en az 2 sn süren
top değişimlerinde (3 sn içinde bulunan / 0,5 sn içinde zamanlanan):

| | top görünüyor | top görünmüyor |
|---|---|---|
| DFL | {trow('DFL', 'both possessions >= 2 s, ball seen')} | {trow('DFL', 'both possessions >= 2 s, ball unseen')} |
| Metrica | {trow('Metrica', 'both possessions >= 2 s, ball seen')} | {trow('Metrica', 'both possessions >= 2 s, ball unseen')} |

Örneklere tek tek bakıldığında ortak neden görülüyor: top yeni takıma doğru yoldayken model topun kimde biteceğini (ilerideki
karelerden) bildiği için olasılığı erkenden çevirir; etiket ise yeni takımın oyuncusu topa değdiği anda değişir. Top görünmüyorken
zamanlama zaten tahmindir.

**Örüntü 3: etiket kaynağına özgü olanlar.** 8 saniyeden uzun gerçek sahipliğin "ölü top" diye tahmin edilmesi neredeyse yalnız
Metrica vekil etiketlerinde görülüyor (kopya başına 14; DFL'de 0,4): olaylardan türettiğimiz etiketler bazı duraklamaları
bilmiyor. Bu bir model hatası değil, etiket kusurudur.

**Örüntüler maçtan maça aynı** (kaybın payları):

| maç | kopya | spellF1 | gerçek / tahmin (kopya başına) | 2 sn altı gerçekler | yarım eşleşen çiftler | eşleşmeyen tahminler |
|---|---|---|---|---|---|---|
{rows_m}

**Üst sınırlar (etiketler kopya çekilerek; yöntem değil).** Bulunan her değişimin zamanı kusursuz olsaydı {tr(ub['base'])} → {tr(ub['snap_3s'])};
yalnız topun göründüğü yerlerde kusursuz olsaydı {tr(ub['snap_3s_seen'])}; ölü top kareleri kusursuz olsaydı {tr(ub['nodead'])}. Kalan büyük kısım
bulunamayan kısa sahipliklerdir.

**Örüntülere dayalı denemeler (hepsi modellerin eğitimde görmediği maçlarda).**
1. *Zayıf işaretlerden sahiplik eklemek.* Tahmin edilen bir sahipliğin içinde öteki takımın olasılığının yükseldiği yerler
   ("tümsekler") aday yapıldı. Bu puan düzeyinde eklenen bir sahipliğin kendini ödemesi için kabaca 10 adaydan 4'ünün gerçek
   olması gerekir; tepe olasılığı 0,3-0,4 olanlarda oran {pc(bm['0.30-0.40']['true_possession_under_it'])}, 0,5'in üstündekilerde bile {pc(bm['0.50-1.01']['true_possession_under_it'])}. Kullanılabilir işaret yok.
2. *Çözücü sabitleri*, topun görünme oranına göre ayrı ayrı: en iyi değişiklik {tr(max(dec.values()), 4, True)}. Sabitler zaten en iyi yerde.
3. *Temas kanıtı.* Top bir takımın oyuncusuna 1-1,5 m yakın ve öteki takım uzaktayken o takıma ek puan (12 ayar): en iyisi
   {tr(cc['best'][1]['all'], 4, True)}, en kötüsü {tr(cc['worst'][1]['all'], 4, True)}. Modeller bu bilgiyi zaten kullanıyor.
4. *Karşılama kuralı.* Top değişimini, yeni takımın oyuncusunun topa ulaştığı ana kaydırmak (24 ayar): en iyisi {tr(cr['best'][1]['all'], 4, True)}
   (DFL {tr(cr['best'][1]['DFL'], 4, True)}), en kötüsü {tr(cr['worst'][1]['all'], 4, True)}. Gürültülü konumlarda "temas anı" yeterince kesin bulunamıyor.
5. *En kısa sahiplik süresi.* Organizatörün kuralı "kontrolsüz tek dokunuş sahiplik değiştirmez" der. Bizim dış etiketlerimizde ise
   saniyenin altında çok sahiplik var. Etiketlerden τ'dan kısa "araya girmeleri" silip aynı kuralı tahmine m ile uyguladık:
   en iyi m her zaman τ'ya eşit çıkıyor (τ = 1,5 sn ise m = 1,5 sn ile {tr(sem['labels_tau_1.5s']['prediction_m_0.0s'])} → {tr(sem['labels_tau_1.5s']['prediction_m_1.5s'])}; etiketler olduğu gibiyse
   m = 1,5 sn {tr(sem['labels_tau_0.0s']['prediction_m_0.0s'])} → {tr(sem['labels_tau_0.0s']['prediction_m_1.5s'])}). Yani bu, yarışma etiketlerinin kısa dokunuşları sayıp saymadığına dair bir bahistir;
   dış veriyle ölçülemez, yarışma maçının etiketlerine bakarak ayarlamak da yasaktır. Değişiklik yapılmadı.
6. *İki model ailesinin öğrenilmiş birleşimi* (yalnız keşif): dört maçın kopyalarında eğitilen bir sınıflandırıcı beşinci maçta
   denendi, beş kez dönerek. v2.15'e göre ortalama {tr(st['all'], 4, True)} (DFL {tr(st['DFL'], 4, True)}, Metrica {tr(st['Metrica'], 4, True)}; {st['copies_better']}/{st['copies']} kopyada iyi), ama en kötü kopya
   {tr(st['worst_copy'], 4, True)}. Bu, v2.14'ün tablosunun aynısıdır: ortalama kazanç var, tek tek kopyalarda belirgin kayıp var; "hiçbir kopya
   −0,010'dan kötü olmasın" şartını geçmez. Ayrıca v2.15 planı ikinci modelle başka deneme yapılmayacağını yazmıştı. Aday olarak
   kaydedilmedi.

**Sonuç.** (1) En büyük kayıp, modellerin izleme verisinde göremediği kısa sahipliklerdir; bunu düzeltmek yeni bilgi ister (topun
kaybolduğu anlarda görüntüden top bulmak gibi), kural ya da ayar değil. (2) Zamanlama hataları gerçek ama elle yazılan kurallar
modelden daha iyi zamanlamıyor. (3) Denenen yöntemlerin hiçbiri kayıtlı asgari kazanca (+0,008 ve hiçbir kopyada −0,010'dan
kötü olmamak) yaklaşmadı. Organizatörün kendi belgesi de tek maçta 0,04'ün altındaki farkların rastlantı payı içinde kaldığını
söylüyor. Teslim sistemi v2.15 olarak kalır.

**Bağlam notu (seçimde kullanılmadı).** Dış etiketler kendilerine göre 3 / 8 / 25 kare geç kaydırıldığında 0,93-0,96 / 0,84-0,88 /
0,50-0,62 alıyor; organizatör kendi etiketleri için 0,98 / 0,89 / 0,65 yayımlıyor. Bu, yarışma etiketlerinde çok kısa
sahipliklerin bizim dış etiketlerimizdekinden daha az olduğunu düşündürür; öyleyse en büyük hata sınıfımız gerçek puanlamada
buradaki kadar ağır olmayabilir. Bu bir çıkarımdır, ölçüm değildir ve hiçbir ayar buna göre yapılmadı.

**Sınırlar.** Geliştirme kopyalarıdır; aynı maçlar daha önceki bütün seçimlerde kullanıldı. Bozma benzetimi bizimdir. Metrica
etiketleri olaylardan türettiğimiz vekillerdir. Ortam: Python {r['environment']['python']}, numpy {r['environment']['numpy']}, pandas {r['environment']['pandas']}, scikit-learn {r['environment']['scikit-learn']}.

"""
p = REPO / 'docs' / 'DENEY_KAYDI_TR.md'
s = p.read_text(encoding='utf-8')
head = '# Deney kaydı\n\n'
assert s.startswith(head + '## K013 ') and '## K014 ' not in s
p.write_text(head + text + s[len(head):], encoding='utf-8')
print(text[:6000])
