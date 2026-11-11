"""Write log entry K004 (Turkish) from the result files and put it at the top of docs/DENEY_KAYDI_TR.md.
Usage: k004.py TESTS_LINE    (TESTS_LINE = sentence about the test runs, written by hand after running them)"""
import json
import os
import sys
from pathlib import Path

R = Path(os.environ.get('SC_DIR', '/home/claude/sc'))
r10 = json.loads((R / 'possession-v210-results.json').read_text())
r11 = json.loads((R / 'possession-v211-results.json').read_text())
p10 = json.loads((R / 'possession-v210-plan.json').read_text())
p11 = json.loads((R / 'possession-v211-plan.json').read_text())
fu = json.loads((R / 'possession-v211-followup.json').read_text())
rel = json.loads((R / 'possession-v211-release.json').read_text())
ft = json.loads((R / 'possession-final-test-plan.json').read_text())
assert r11['selected'] == 'possession-v2.11'


def tr(x, nd=4):
    return f'{x:.{nd}f}'.replace('.', ',')


def pct(x, nd=1):
    return ('%' + f'{100 * x:.{nd}f}').replace('.', ',')


def sgn(x, nd=4):
    x = round(x, nd)
    return ('+' if x > 0 else '−' if x < 0 else '') + f'{abs(x):.{nd}f}'.replace('.', ',')


def th(n):
    return f'{int(n):,}'.replace(',', '.')


def hm(stamp):
    return stamp[11:16]


S10, S11 = r10['summary'], r11['summary']
K5 = json.loads((R / 'possession-label-order-correction.json').read_text())['corrected']['goalkeeper_diagnostic']
d = K5['rerun_python_3_13_file_order_labels']['spell_f1']                     # re-run against the file-order labels (K005)
d_first = p10['diagnostic_spell_f1']                                          # first run, as quoted in the v2.10 plan
mean3 = lambda k: sum(d[k].values()) / 3
first3 = lambda k: sum(d_first[k].values()) / 3
diag_rows = [('base', 'bozulmuş kopya, olduğu gibi'), ('gk_one', 'ev sahibi kalecisi bütün maç deplasman kimliğiyle'),
             ('gk_both', 'iki kaleci de bütün maç öbür takımın kimliğiyle'), ('gk_part', 'iki kaleci, maçın %30\'unda (30-300 sn\'lik dilimler) öbür kimlikle'),
             ('ref_home', 'oyunu 8-18 m\'den izleyen bir hakem izi, ev sahibi kimliğiyle'), ('ref_mixed', 'aynı iz, 20-120 sn\'de bir değişen kimlikle')]
diag = '\n'.join(f"| {name} | {tr(d[k]['MET1'])} | {tr(d[k]['MET2'])} | {tr(d[k]['MET3'])} | {tr(mean3(k))} | {'' if k == 'base' else sgn(mean3(k) - mean3('base'), 3)} |"
                 for k, name in diag_rows)

names10 = {'none': 'kimlikler bozulduğu gibi (kaleciler doğru)', 'gk_one': 'bir kaleci bütün maç yanlış', 'gk_both': 'iki kaleci bütün maç yanlış',
           'gk_part': 'iki kaleci maçın %30\'unda yanlış'}
t10 = '\n'.join(
    f"| {names10[k]} | {tr(S10[k]['spell_f1']['v2_9'])} | {tr(S10[k]['spell_f1']['v2_10'])} | {sgn(S10[k]['spell_f1']['v2_10'] - S10[k]['spell_f1']['v2_9'])} | "
    f"{'/'.join(map(str, S10[k]['copies_better_same_worse']))} | {pct(S10[k]['goalkeeper_positions_with_wrong_id_before_after'][0])} → {pct(S10[k]['goalkeeper_positions_with_wrong_id_before_after'][1])} |"
    for k in names10)
g10 = r10['gates']

names11 = dict(names10, view42_none='kamera penceresi ±42 m, kimlikler bozulduğu gibi', view35_none='kamera penceresi ±35 m, kimlikler bozulduğu gibi',
               view42_gk_both='kamera penceresi ±42 m, iki kaleci yanlış (eşik değil)')
gate_of = {'none': 'G1', 'gk_both': 'G2', 'gk_one': 'G3', 'gk_part': 'G4', 'view42_none': 'G5', 'view35_none': 'G6', 'view42_gk_both': '—'}
t11 = '\n'.join(
    f"| {gate_of[k]} | {names11[k]} | {tr(S11[k]['spell_f1']['v2_9'])} | {tr(S11[k]['spell_f1']['v2_11'])} | {sgn(S11[k]['spell_f1']['v2_11'] - S11[k]['spell_f1']['v2_9'])} | "
    f"{'/'.join(map(str, S11[k]['copies_better_same_worse']))} | {pct(S11[k]['goalkeeper_positions_with_wrong_id_before_after'][0])} → {pct(S11[k]['goalkeeper_positions_with_wrong_id_before_after'][1])} | "
    f"{th(max(S11[k]['outfield_positions_moved_to_the_wrong_team_per_copy']))} |"
    for k in ('none', 'gk_both', 'gk_one', 'gk_part', 'view42_none', 'view35_none', 'view42_gk_both'))
g11 = r11['gates']
v10w = {k: S11[k]['v2_10_reported_only'] for k in ('view42_none', 'view35_none')}

dev = fu['development_on_training_matches']


def dev_cell(rows, cond, hw, key):
    out = []
    for m in ('J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ'):
        x = [r for r in rows if r['match'] == m and r['condition'] == cond and r['view_half_width'] == hw]
        if x:
            out.append(th(x[0][key]) if key.startswith('outfield') else pct(x[0][key]))
    return ' / '.join(out)


views = ((None, 'bütün saha'), (50.0, '±50 m'), (42.0, '±42 m'), (35.0, '±35 m'))
k2, k1 = dev['keeper2 (v2.11)'], dev['keeper (v2.10)']
tdev = '\n'.join(
    f"| {name} | {dev_cell(k1, 'none', hw, 'outfield_positions_moved_to_wrong_team')} | {dev_cell(k2, 'none', hw, 'outfield_positions_moved_to_wrong_team')} | "
    f"{dev_cell(k2, 'gk_both', hw, 'gk_wrong_after')} | {dev_cell(k2, 'gk_part', hw, 'gk_wrong_after')} |" for hw, name in views)
seen = {hw: ' / '.join(pct(x['goalkeeper_in_view']) for m in ('J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ')
                         for x in [r for r in k2 if r['match'] == m and r['condition'] == 'none' and r['view_half_width'] == hw][:1]) for hw in (50.0, 42.0, 35.0)}

res = fu['reserved_metrica_game_3']['rows']
tres = '\n'.join(
    f"| {names11[r['condition']]} | {tr(r['v2_9'][0])} | {tr(r['v2_11'][0])} | {tr(r['v2_10'][0]) if 'v2_10' in r else ''} | "
    f"{pct(r['v2_11_moved']['goalkeeper_positions_with_wrong_id_before_after'][0])} → {pct(r['v2_11_moved']['goalkeeper_positions_with_wrong_id_before_after'][1])} | "
    f"{th(r['v2_11_moved']['outfield_positions_moved_to_the_wrong_team'])} |" for r in res)

F = fu['full_size_rehearsal']


def reh(k):
    v = F[k]
    g = v.get('goalkeeper_correction')
    moved = f"{th(g['moved_pieces'])} parça / {th(g['moved_frames'])} kare" if g else ('—' if 'steps' not in v else '')
    return f"{tr(v['spell_f1'])} / {tr(v['macro_f1'])} | {moved} | {v['seconds']} sn / {tr(v['peak_memory_gb'], 2)} GB"


chainA, chainG, chainR = F['bundle_A_chain_v2_11'], F['bundle_G1_chain_v2_11'], F['bundle_A_chain_reserve_v2_11g']
bad_steps = lambda c: [f'{k}: {v}' for k, v in c['steps'].items() if not v.startswith(('OK', 'AYNI', 'ATLANDI', 'VAR'))]

none_moved = fu['what_v2_10_moved_with_correct_ids']['copies']
gk_flips = sum(c['moved_pieces_and_frames']['goalkeeper under the wrong id (flipped by the corruption), moved to his team'][0] for c in none_moved)
gk_flip_frames = sum(c['moved_pieces_and_frames']['goalkeeper under the wrong id (flipped by the corruption), moved to his team'][1] for c in none_moved)

text = f'''## K004 — Kaleci takım kimliği: teşhis, v2.10 (eşikleri geçti, yayımlanmadı), v2.11 (yeni sürüm), 11 Kasım 2026

**Özet.** Teslim sistemi artık **`possession-v2.11`** (`python -m possession.run211`): v2.9 + özelliklerden
önce çalışan bir kaleci takım denetimi (`possession/keeper2.py`). Teknik basamakların ikincisi v2.9'dur;
dondurulmuş v2.9 dosyalarının hiçbiri değişmedi. Sağlanan maçın hiçbir dosyası okunmadı; sağlanan takip
verisinde böyle bir hata olup olmadığı bilinmiyor ve bakılmadı. Bu girdideki bütün sayılar dış maçlarda,
bizim benzettiğimiz hatalarla ölçülmüştür; yarışma puanı değildir.

**1. Teşhis (ilk çalıştırma 13:04-13:33; yalnız raporlama, `experiments/possession_v2/stress_roles.py`).** DATA.md: "You
get positions and team membership, nothing more". Bir izin takımını izleyici belirler ve kaleci takımından
farklı forma giyer. Bozma modelimiz (`possession.degrade`) yalnız 1-6 sn'lik takım değişimleri içeriyordu.
Soru: kaleci izleri uzun süre yanlış takımın kimliğini taşısaydı dondurulmuş sürüm ne kaybederdi? Metrica
maçları 1-3, birer bozuk kopya (K003 slot ölçümünün kopyaları), dondurulmuş v2.9 mantığı, spellF1
(dosya sırasındaki vekil etiketlere göre yeniden çalıştırma, K005):

| durum | MET1 | MET2 | MET3 | ortalama | fark |
|---|---|---|---|---|---|
{diag}

*Not (K005):* ilk çalıştırma, Metrica vekil etiketlerinin duran top aralıklarının yaklaşık yarısını
yitirdiği Python 3.10 ortamında yapılmıştı. v2.10 planında (`diagnostic_spell_f1`) duran sayılar onlardır:
ortalama {tr(first3('base'))}; bir kaleci {sgn(first3('gk_one') - first3('base'), 3)}, iki kaleci {sgn(first3('gk_both') - first3('base'), 3)}, %30 {sgn(first3('gk_part') - first3('base'), 3)}, hakem
{sgn(first3('ref_home') - first3('base'), 3)} / {sgn(first3('ref_mixed') - first3('base'), 3)}. Sonuç aynı; düzeyler farklı. Bu teşhis bir eşik değildi; iki doğrulama da doğru etiketlerle
yapıldı.

İki kaleci birden yanlışken çöküşün nedeni: `features.attack_dirs` her takımın hücum yönünü takımın
ortalama x konumundan çıkarıyor; iki kaleci yanlış kimlik altında bu ortalamayı ters çeviriyor. Dondurulmuş
dosya değiştirilemeyeceği için düzeltme, modellere verilen takip verisinin önüne konan ayrı bir adım oldu.
Hakem izi için bir şey eklenmedi (fark {sgn(mean3('ref_home') - mean3('base'), 3)} ve {sgn(mean3('ref_mixed') - mean3('base'), 3)}).

**2. İlk aday, v2.10 (`possession/keeper.py`).** Kural: oyun öbür yarı sahadayken (bütün oyuncuların
medyan x'i kale çizgisinden en az 50 m) kaleye en yakın izlenen oyuncu kalecidir; böyle iz parçaları ve
onların zaman-yer olarak devamı olan parçalar, o kaleyi savunmayan takımın slotundaysa savunan takıma
aktarılır. Kural ve sabitleri dört DFL eğitim maçında, model çalıştırmadan, kaleci konumlarının kaçının
yanlış kimlik taşıdığı sayılarak geliştirildi; bir model denetimi eğitim maçı J03WOH'de yapıldı (örneklem
içi; iki kaleci yanlış 0,3251 → 0,7328, kimlikler doğru 0,7392 → 0,7392). Plan sonuçlardan önce kaydedildi
(`possession-v210-plan.json`, {hm(p10['registered_at'])}); 8 yeni bozuk kopya (J03WN1, J03WR9, MET1, MET2; tohumlar 10100-10131),
izler 46 adsız slota paketli, doğrulama modelleri. Sonuç (`possession-v210-results.json`, {hm(r10['written_at'])}):

| koşul | v2.9 | v2.10 | fark | iyi/aynı/kötü kopya | yanlış kimlikli kaleci konumu, önce → sonra |
|---|---|---|---|---|---|
{t10}

Dört eşik de geçti (G1 fark {sgn(g10['G1 neutral with correct ids']['mean_difference'])}, en kötü kopya {sgn(g10['G1 neutral with correct ids']['worst_copy_difference'])}; G2 {tr(g10['G2 both goalkeepers']['mean_v2_10'])} ≥ {tr(g10['G2 both goalkeepers']['needed'])};
G3 {tr(g10['G3 one goalkeeper']['mean_v2_10'])} ≥ {tr(g10['G3 one goalkeeper']['needed'])} ve fark {sgn(g10['G3 one goalkeeper']['mean_difference'])} ≥ +0,008; G4 {tr(g10['G4 part of the time']['mean_v2_10'])} ≥ {tr(g10['G4 part of the time']['needed'])} ve fark {sgn(g10['G4 part of the time']['mean_difference'])} ≥ 0).
Kayıtlı karar kuralına göre v2.10 sürüm olacaktı.

**3. Karardan sonra bulunan zayıflık; v2.10 neden yayımlanmadı.** Dondurmadan önce, kimlikler doğruyken
v2.10'un neyi taşıdığına bakıldı (`gk_none.py`, `gk_none_detail.py`; yalnız raporlama). 8 kopyada 80 parça:
{gk_flips}'si bozmanın 1-6 sn'liğine yanlış kimliğe koyduğu kalecilerdi ({th(gk_flip_frames)} kare; doğru düzeltme). 3'ü saha
oyuncusuydu: J03WR9'un son 2,5 dakikasında rakip kaleden 13 m uzakta hareketsiz duran bir forvet (iki
kopyada da: 3.496 ve 1.571 kare; kaleci daha ileride duruyordu) ve MET1'de kalecinin izi kayıpken kaleden
26 m uzakta 15 sn bekleyen bir forvet (366 kare). Bu kopyalarda spellF1 değişmemişti. Ama neden önemli:
"oyun uzaktayken kaleye en yakın izlenen oyuncu" kanıtı, kaleci izlenmiyorsa yanlış kişiyi gösterir. Oyunu
izleyen bir kamera uzak kaleciyi hiç göstermeyebilir (DATA.md: puanlanan karelerde ortalama 20,5 izlenen
nesne; taktik homografi için devre arasında "the camera is not pointed at the pitch"). v2.10 planı bu
durumu kapsamıyordu. Eğitim maçlarında bir kamera penceresi benzetildi (`camera_view.py`: bütün
oyuncuların medyan x'inden belli bir uzaklığın ötesindeki oyuncular izlenmez; kalecinin görüntüde olduğu
kare payı ±50 m'de {seen[50.0]}, ±42 m'de {seen[42.0]}, ±35 m'de {seen[35.0]}). Model çalıştırılmadan sayım
(`gk_far_dev.py`; dört eğitim maçı WOH / WOY / WPY / WQQ, birer bozuk kopya; v2.10 yalnız ilk ikisinde):

| görüş | v2.10: kimlikler doğruyken yanlış takıma aktarılan saha oyuncusu konumu | v2.11: aynısı | v2.11: iki kaleci yanlışken (%100) düzeltme sonrası yanlış kaleci konumu | v2.11: %30 yanlışken sonrası |
|---|---|---|---|---|
{tdev}

Bu yüzden v2.10 yayımlanmadı. Kayıtlı karar kuralından sapma temkinli yöndedir ve burada, planında
(`possession-v211-plan.json`, "background") ve teknik belgede yazılıdır; v2.10'un planı, sonuçları ve
`keeper.py` dosyası kayıt olarak depoda duruyor.

**4. İkinci aday, v2.11 (`possession/keeper2.py`).** İki değişiklik:
- *Yalıtım:* bir kare ancak parça kaleye ikinci en yakın izlenen oyuncudan en az 8 m daha yakınsa kanıt
  sayılır (eğitim maçlarında gerçek kaleci için bu, ilgili karelerin %96-99'unda doğru; bekleyen bir
  forvet çoğunlukla stoperlerin birkaç metre yakınındadır).
- *Kendi kanıtı yetmez:* öbür takımın kimliğini taşıyan bir parça yalnız iki durumda aktarılır. (a) O
  kalenin o yarıdaki kanıtının en az yarısı ve en az 2.500 karesi öbür kimlik altındaysa (kaleci bütün
  yarı boyunca yanlış etiketli). (b) Parça zaman ve yer olarak bir kaleci parçasının devamıysa (kaleci bir
  süreliğine yanlış etiketli). Eğitim maçlarında kimlikler doğruyken öbür kimlik altındaki kanıt hiçbir
  görüşte kale ve yarı başına 320 kareyi geçmedi; iki kaleci yanlışken bütün sahada ve ±50 m'de en az
  20.242, ±42 m'de en az 6.903, ±35 m'de 597-2.845 kareydi.

Plan, adayın doğrulama ya da ayrılmış maçlardaki hiçbir sonucundan önce kaydedildi ({hm(p11['registered_at'])}). 8 yeni
kopya (tohumlar 11100-11131), aynı dört doğrulama maçı. Altı eşik: G1-G4 v2.10 planındaki eşiklerin aynısı;
G5 ve G6, kamera penceresi ±42 m ve ±35 m iken kimlikler doğruysa zarar vermeme eşiği (ortalama fark ≥
−0,002, hiçbir kopya −0,005'in altında değil). Sonuç (`possession-v211-results.json`, {hm(r11['written_at'])}; eşikler bir
kez, bütün satırlara uygulandı):

| eşik | koşul | v2.9 | v2.11 | fark | iyi/aynı/kötü | yanlış kimlikli kaleci konumu, önce → sonra | yanlış takıma aktarılan saha oyuncusu konumu (en çok, kopya başına) |
|---|---|---|---|---|---|---|---|
{t11}

Altı eşik de geçti. Kayıtlı karar kuralı: v2.11 sürüm olur, v2.9 bir alt basamak olarak kalır, v2.10
yayımlanmaz. Yanında raporlanan (eşik değil): v2.10 aynı kopyalarda ±42 m'de {tr(v10w['view42_none']['spell_f1'])} (v2.9'a göre
{sgn(v10w['view42_none']['mean_difference'])}), ±35 m'de {tr(v10w['view35_none']['spell_f1'])} ({sgn(v10w['view35_none']['mean_difference'])}; en kötü kopya {sgn(min(v10w['view42_none']['worst_copy_difference'], v10w['view35_none']['worst_copy_difference']))}); kopya başına yanlış aktardığı saha
oyuncusu konumu en çok {th(max(v10w['view42_none']['outfield_positions_moved_to_the_wrong_team_per_copy']))} ve {th(max(v10w['view35_none']['outfield_positions_moved_to_the_wrong_team_per_copy']))}.

*Ayrılmış Metrica maçı 3 (tohum 31103), karardan sonra bir kez, eşik değil:*

| koşul | v2.9 | v2.11 | v2.10 | yanlış kimlikli kaleci konumu, önce → sonra | yanlış aktarılan saha oyuncusu konumu |
|---|---|---|---|---|---|
{tres}

**5. Dondurma ve bağlantılar.**
- `possession-v211-release.json` ({hm(rel['frozen_at'])}): v2.9'un 18 dondurulmuş dosyası aynı özetlerle + `keeper2.py` +
  `run211.py`; iki model paketi aynı. Yedek giriş noktası `possession.run211g` (`possession-v211g-release.json`):
  yayımlanan başlama karesi olmadan.
- `possession-release.json` basamakları: v2.11 → v2.9 → v2.5c → v2.5c yalnız taktik. Yedek yapılandırma:
  v2.11g → v2.9g → v2.5b → v2.5b yalnız taktik. Bir alt basamak yalnız üstteki hata verirse kullanılır,
  bir çıktıya bakılarak değil.
- Son test planı (`possession-final-test-plan.json`) v2.11 için yeniden kaydedildi ({hm(ft['registered_at'])}); ayrılmış maç
  J03WMX'e hâlâ hiç erişilmedi. Tasarım, kopyalar, tohumlar, benzeticiler ve beklentiler aynı; değişen:
  sınanan sürüm ve araç (giriş noktasını plandan okur, her kopyada denetimin ne taşıdığını yazar). İlk
  kayıt dosyada `registration_history` altında duruyor.
- Zincirin PLATFORM adımı artık yedi sentetik varyantı karşılaştırır: v2.9'un beş varyantı (kayıtlı
  değerler değişmedi) ve kaleci izleri öbür kimlikle yazılmış iki pakette `possession.run211`. Linux'ta
  Python 3.10 ve 3.12 (numpy 1.26.4) ile Python 3.13 (numpy 2.5.3) altında aynı baytlar.
- Ek R'ye bir satır eklendi: "Goalkeeper team correction" (bir şey taşındı / taşınmadı; sayı yok).
- {sys.argv[1]}

**6. Tam boy prova (sentetik paketler, K003'teki gibi; bağlantı ve boyut denetimi, doğruluk ölçümü değil).**
Puanlar dosya sırasındaki vekil etiketlere göredir (K005); K003'ün A paketi satırı da yeniden puanlanmıştır
(ilk yazılan {tr(F['bundle_A_v2_9_chain_of_K003']['as_first_recorded_against_the_degraded_labels']['spell_f1'])} / {tr(F['bundle_A_v2_9_chain_of_K003']['as_first_recorded_against_the_degraded_labels']['macro_f1'])}).
G1 = paket A, dört kalecinin (Metrica maçı 3 ve 2 parçaları) izleri taktik dosyada öbür takımın kimliğiyle;
G2 = aynı hata yayın dosyasında da.

| çalıştırma | spellF1 / macroF1 (dış etiketlere göre) | denetimin taşıdığı | süre / en yüksek bellek |
|---|---|---|---|
| paket A, v2.9 zinciri (K003) | {tr(F['bundle_A_v2_9_chain_of_K003']['spell_f1'])} / {tr(F['bundle_A_v2_9_chain_of_K003']['macro_f1'])} | — | 695 sn / 1,54 GB |
| paket A, `run211` | {reh('bundle_A_v2_11')} |
| paket A, v2.11 zinciri (testler dahil) | {reh('bundle_A_chain_v2_11')} |
| paket G1, `run211` | {reh('bundle_G1_v2_11')} |
| paket G1, `run29` (denetimsiz) | {reh('bundle_G1_v2_9')} |
| paket G2, `run211` | {reh('bundle_G2_v2_11')} |
| paket G1, v2.11 zinciri (`--quick`) | {reh('bundle_G1_chain_v2_11')} |
| paket A, yedek yapılandırma zinciri (v2.11g, `--quick`) | {reh('bundle_A_chain_reserve_v2_11g')} |

Zincir sonuç satırları: A "{chainA['result_line']}", G1 "{chainG['result_line']}", yedek "{chainR['result_line']}".
{'Bütün adımlar OK / AYNI / ATLANDI.' if not (bad_steps(chainA) + bad_steps(chainG) + bad_steps(chainR)) else 'OK olmayan adımlar: ' + '; '.join(bad_steps(chainA) + bad_steps(chainG) + bad_steps(chainR))}

**7. Ölçülen / ölçülmeyen.**
- *Ölçülen:* dış maçlarda, bizim benzettiğimiz kaleci kimliği hatalarında ve kamera penceresinde v2.11'in
  v2.9'a göre farkı (yukarıdaki tablolar); kimlikler doğruyken ortalama farkın {sgn(S11['none']['spell_f1']['v2_11'] - S11['none']['spell_f1']['v2_9'])} olduğu.
- *Ölçülmeyen:* sağlanan maçta herhangi bir şey. Sağlanan takip verisinde kaleci kimliği hatası var mı,
  uzak kaleci izleniyor mu, bilinmiyor. Gerçek izleyicinin hataları bu benzetimlerden farklı olabilir.
- *Sınırlar:* uzak kaleci çoğunlukla görüntü dışındaysa (benzetimde ±35 m) yanlış kimlik düzeltilmez
  (yeterli kanıt yok; zarar da verilmez). Bütün maç süren hatalarda kaleciyle birlikte az sayıda saha
  oyuncusu konumu da aktarılabiliyor. Doğrulama maçları bu tasarım için taze değildi (v2.10 çözümlemesi
  aynı maçlarda yapıldı). Denetim yalnız taktik kamerayla doğrulandı; yayın yolu kimlikleri verildiği
  gibi kullanır.
- *Kayıt düzeltmesi yok:* v2.10'un planı ve sonuçları değiştirilmedi; hiçbir eşik gevşetilmedi. v2.11'in
  eşikleri v2.10'unkilerle aynı, artı iki ek eşik.

'''
p = R / 'docs/DENEY_KAYDI_TR.md'
s = p.read_text(encoding='utf-8')
head = '# Deney kaydı\n\n'
assert s.startswith(head) and 'K004' not in s
p.write_text(head + text + s[len(head):], encoding='utf-8')
print(text[:3000])
