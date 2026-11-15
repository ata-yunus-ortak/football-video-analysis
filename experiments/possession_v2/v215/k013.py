"""Write log entry K013 (Turkish) from the registered plan, the development summary and the results of the v2.15
validation; with the test counts and possession-v215-rehearsal.json present, also the integration paragraph.
Usage: /usr/bin/python3 k013.py REPO_DIR [TESTS_310 SKIPPED_310 TESTS_313 SKIPPED_313]   (prints; body in v215/k013_body.md)"""
import json, sys
from pathlib import Path

REPO = Path(sys.argv[1])
V = Path('/home/claude/work/v215')
plan = json.loads((REPO / 'possession-v215-plan.json').read_text())
res = json.loads((REPO / 'possession-v215-results.json').read_text())
dev = json.loads((V / 'development_summary.json').read_text())
S, G, GV = res['summary'], res['gates'], res['gate_values_unrounded']
sel = bool(res['selected'])


def tr(x, nd=4, sign=False):
    s = f'{x:+.{nd}f}' if sign else f'{x:.{nd}f}'
    return s.replace('.', ',').replace('-', '−')


def row(label, key):
    s = S[key]
    worst = min(r['diff_spell_f1'] for r in res['rows'] if r['condition'] == key.split('_DFL')[0].split('_Metrica')[0]
                and (('_DFL' not in key and '_Metrica' not in key) or (r['copy'].startswith('J03') == ('_DFL' in key))))
    return (f"| {label} | {s['n']} | {tr(s['v2_11']['spell_f1'])} | {tr(s['fused']['spell_f1'])} | {tr(s['diff_spell_f1_mean'], sign=True)} | "
            f"{s['copies_better']} / {s['copies_worse']} | {tr(worst, sign=True)} | {tr(s['tcn_alone']['spell_f1'])} | {tr(s['diff_macro_f1_mean'], sign=True)} |")


def per_copy(name):
    rs = sorted((r for r in res['rows'] if r['condition'] == 'tactical' and r['copy'].startswith(name)), key=lambda r: r['copy'])
    return ', '.join(tr(r['diff_spell_f1'], sign=True) for r in rs)


T = dev['table']
r214 = json.loads((REPO / 'possession-v214-results.json').read_text())
W = plan['fusion_rule_fixed_before_any_score']['weight']
gate_rows = [
 ('G1 ortalama kazanç ≥ +0,008', tr(GV['tactical']['diff_spell_f1_mean'], sign=True), G['G1 gain']),
 ('G2 DFL\'de kazanç ≥ +0,008', tr(GV['tactical_DFL']['diff_spell_f1_mean'], sign=True), G['G2 gain on provider flags']),
 ('G3 Metrica\'da ≥ −0,002', tr(GV['tactical_Metrica']['diff_spell_f1_mean'], sign=True), G['G3 no harm on event proxies']),
 ('G4 en kötü kopya ≥ −0,010', tr(GV['tactical']['diff_spell_f1_min'], sign=True), G['G4 no bad copy']),
 ('G5 macroF1 ≥ −0,003', tr(GV['tactical']['diff_macro_f1_mean'], sign=True), G['G5 macroF1']),
 ('G6 doldurma koşulları ≥ 0', tr(GV['fill_good']['diff_spell_f1_mean'], sign=True) + ' ve ' + tr(GV['fill_medium']['diff_spell_f1_mean'], sign=True), G['G6 broadcast fill']),
 ('G7 öteki benzeticinin kopyaları ≥ 0', tr(GV['tactical_sim2']['diff_spell_f1_mean'], sign=True), G['G7 other simulator']),
]
failed = [g.split(' ')[0] for g, _, ok in gate_rows if not ok]
tac = S['tactical']
title = ('yedi kapı geçti, teslim sistemi v2.15' if sel else 'kayıtlı kapılardan geçmedi, teslim sistemi v2.11k kaldı')
out = []
out.append(f"## K013 — v2.15 adayı: aynı birleşik sistem, ikinci modelin ağırlığı 0,5 yerine {tr(W, 1)}; {title}, 15 Kasım 2026\n")
out.append(f"""**Neden üçüncü bir deneme.** v2.14 (K012) 16 yeni kopyanın 15'inde daha iyiydi (ortalama {tr(r214['summary']['tactical']['diff_spell_f1_mean'], sign=True)}) ama bir kopyada
{tr(r214['summary']['tactical']['diff_spell_f1_min'], sign=True)} çıktı; "hiçbir kopya −0,010'dan kötü olmasın" kapısı (G4) geçmedi ve aday seçilmedi. O kayıt ve
kapıları değişmedi. Bir denemenin daha hangi koşulda yapılacağı 14 Kasım 23:39'da, o doğrulamanın yalnız üç satırı
bilinirken yazıldı (`experiments/possession_v2/v214/NOTES.md`; o üç satırdan biri, G4'ün geçemeyeceğini zaten gösteren
−0,0160 satırıydı, yani kural v2.14'ün seçilmeyeceği bilinerek yazıldı): yalnız v2.14'ün ortalama kapıları (G1, G2, G3, G5) geçerse; aynı
ağırlık dosyaları, aynı aritmetik havuz, aynı çözücü; yalnız ağın ağırlığı düşürülür; kapılar aynı; kopyalar yeni; **bundan
sonra başka deneme yok**. İkinci modeli eklemek için kayıtlı üçüncü denemedir (v2.13, v2.14, v2.15).
""")
out.append("""**Ağırlığın seçimi (geliştirme).** v2.14 doğrulamasının 16 taktik ve 4 öteki-benzetici kopyası, kararı kaydedildikten sonra
geliştirme verisi oldu (olasılıkları o andan sonra saklandı); önceki 22 kopyayla birlikte 42 geliştirme kopyası. Kural (23:39):
0,1 / 0,2 / 0,3 ağırlıklarından, herhangi bir geliştirme kopyasında −0,007'den kötü olan elenir (G4'e 0,003 pay); kalanlardan
ortalaması en büyük olan alınır; DFL geliştirme kopyalarındaki ortalaması +0,010'dan küçükse deneme yapılmaz. (Notta DFL kopyaları
için 18 yazılmıştı; doğrusu 20'dir: 16 taktik, 4 öteki benzetici. Koşul 20'sine de, 16 taktik kopyaya da uygulandı.)
42 kopyada aritmetik havuz, v2.11'e göre (ortalama fark | en kötü kopya | iyi olan kopya):
""")
out.append('| ağırlık | hepsi (42) | DFL (20) | Metrica (22) | v2.14 doğrulamasının kopyaları (20) | öteki benzetici (9) |\n|---|---|---|---|---|---|')
for n in ('ari10', 'ari20', 'ari30', 'ari40', 'ari50'):
    cell = lambda g: f"{tr(T[g][n]['mean'], sign=True)} \\| {tr(T[g][n]['min'], sign=True)} \\| {T[g][n]['better']}"
    out.append(f"| 0,{n[3:4]} | {cell('all 42')} | {cell('DFL 20')} | {cell('Metrica 22')} | {cell('copies of the v2.14 validation 20')} | {cell('his simulator 9')} |")
out.append(f"""
0,3 bir eski DFL kopyasında −0,0118 olduğu için elendi; 0,1 ve 0,2 kaldı, ortalaması büyük olan **0,2** seçildi (DFL'in 20
kopyasında {tr(T['DFL 20']['ari20']['mean'], sign=True)}, 16 taktik kopyasında {tr(T['DFL tactical 16']['ari20']['mean'], sign=True)}). v2.14'ü düşüren kopyada (Metrica 1, 16120) farklar ağırlığa
göre düzgün değişmiyor: 0,1 −0,0049; 0,2 −0,0031; 0,3 +0,0022; 0,4 +0,0036; 0,5 −0,0160. Yani o −0,016 sistemli bir bozulmadan çok,
çözücünün birkaç sahipliği farklı bölmesinin sonucu; küçük ağırlık bu oynaklığı da küçültüyor.
""")
out.append(f"""**Plan.** `possession-v215-plan.json`, 15 Kasım 01:17:34'te kaydedildi; o anda hiçbir havuzun üçüncü tohum dizisindeki bir kopyada
puanı yoktu. Her şey v2.14 doğrulamasıyla aynı (aynı altı ağırlık dosyası, SHA-256 değerleri aynı; `exp_v213.py` değiştirilmeden),
yalnız ağırlık {tr(W, 1)} ve tohumlar yeni: kopya 19100 + 10·maç + j, yayın 49100 / 49200, saat 59100 / 59200, öteki benzetici 69100 + maç
(hiçbiri eski bir dosyada geçmiyor). Kapılar G1-G7, değişmeden. Plan şunu da yazar: aynı kapılarla üçüncü deneme olduğu için burada
bir geçiş, ilk denemede geçmiş olmaktan daha zayıf bir kanıttır; ve bir kapı geçmezse teslimden önce ikinci modelle başka aday
kaydedilmez.
""")
out.append(f"**Sonuç** (`possession-v215-results.json`, kapılar 02:13'te uygulandı; spellF1, organizatörün ölçütü; yarışma puanı değil):\n")
out.append('| koşul | kopya | v2.11 | birleşik | fark | iyi / kötü | en kötü kopya | ağ tek başına | macroF1 farkı |\n|---|---|---|---|---|---|---|---|---|')
out.append(row('yalnız taktik kamera, hepsi', 'tactical'))
out.append(row('yalnız taktik kamera, DFL', 'tactical_DFL'))
out.append(row('yalnız taktik kamera, Metrica', 'tactical_Metrica'))
out.append(row('iyi yayınla doldurma', 'fill_good'))
out.append(row('orta yayınla doldurma', 'fill_medium'))
out.append(row('42 m kamera penceresi (rapor)', 'view42'))
out.append(row('yazarın benzeticisi (G7)', 'tactical_sim2'))
out.append(f"""
Yalnız taktik kamerada kopya kopya farklar: J03WN1 {per_copy('J03WN1')}; J03WR9 {per_copy('J03WR9')}; Metrica 1 {per_copy('MET1')};
Metrica 2 {per_copy('MET2')}.
""")
np_rows = sorted(r['copy'].replace('|', ' ') for r in res['rows'] if r['condition'] == 'tactical' and not r['fused_on_this_path'])
if np_rows:
    out.append(f"""{len(np_rows)} kopya ({', '.join(np_rows)}) gürültü kapısında v2.3 yoluna düştü; aday o yolda havuzlama yapmadığı için bu kopyalarda çıktı
v2.11'in çıktısıdır ve fark tam 0'dır (ortalamalara 0 olarak girerler).
""")
out.append('| kapı | değer | sonuç |\n|---|---|---|')
for g, v, ok in gate_rows:
    out.append(f"| {g} | {v} | {'geçti' if ok else '**geçmedi**'} |")
f2, t2 = S['tactical'], S['tactical']
out.append(f"""
**Yanında raporlananlar (yalnız taktik kamera, 16 kopya).** 2 saniyeden kısa sahipliklerin yakalanma oranı: v2.11
{tr(f2['v2_11']['recall_under_2s_iou03'], 3)}, birleşik {tr(f2['fused']['recall_under_2s_iou03'], 3)}, ağ {tr(f2['tcn_alone']['recall_under_2s_iou03'], 3)}; 1 saniyeden kısalar: {tr(f2['v2_11']['recall_under_1s_iou03'], 3)} /
{tr(f2['fused']['recall_under_1s_iou03'], 3)} / {tr(f2['tcn_alone']['recall_under_1s_iou03'], 3)}. Geçiş F1 (12 kare): {tr(f2['v2_11']['trans_f1_12'], 3)} / {tr(f2['fused']['trans_f1_12'], 3)} / {tr(f2['tcn_alone']['trans_f1_12'], 3)}. Kopya başına
sahiplik sayısı: etiketlerde {f2['gt_spells_per_copy']:.0f}, v2.11 {f2['v2_11']['pred_spells_per_copy']:.0f}, birleşik {f2['fused']['pred_spells_per_copy']:.0f}, ağ {f2['tcn_alone']['pred_spells_per_copy']:.0f}. Birleşik
sistem kopya başına ortalama {f"{f2['frames_changed_per_copy']:,.0f}".replace(',', '.')} karenin etiketini değiştirdi. Gürültü kapısı: v2.1 yolu {f2['paths']['v2.1']}, v2.3 yolu
{f2['paths']['v2.3']} kopya. Doldurma kapısı iyi yayında {S['fill_good']['gate_opened']}/8, orta yayında {S['fill_medium']['gate_opened']}/8 kopyada açıldı.
""")
bad = sorted((r for r in res['rows'] if r['condition'] == 'tactical' and r['diff_spell_f1'] < -0.010), key=lambda r: r['diff_spell_f1'])
when = '2026-11-15 02:13'            # the decision; the results file was written again later with the after-decision rows
if sel:
    out.append(f"""**Karar ({when}).** Yedi kapının yedisi geçti; kayıtlı kurala göre aday seçildi ve possession-v2.15 olarak
bütünleştirilir. Kapılar bir kez, bütün satırlara uygulandı; başka tohum, ağırlık, havuz ya da çözücü sabiti denenmedi.
""")
else:
    out.append(f"""**Karar ({when}).** {len(failed)} kapı geçmedi ({', '.join(failed)}); kayıtlı kurala göre aday teslim sistemine
girmedi, teslim sistemi **v2.11k** olarak kalır. Kapılar bir kez, bütün satırlara uygulandı; başka tohum, ağırlık, havuz ya da çözücü
sabiti denenmedi. Planın yazdığı gibi, teslimden önce ikinci modelle başka aday kaydedilmeyecek.
""")
    if bad:
        out.append("−0,010'dan kötü kopyalar: " + '; '.join(
            f"{r['copy'].replace('|', ' ')} ({tr(r['diff_spell_f1'], sign=True)}; v2.11 {tr(r['v2_11']['spell_f1'])}, ağ tek başına {tr(r['tcn_alone']['spell_f1'])}, "
            f"oyun içinde topun göründüğü karelerin payı {tr(r['ball_visible_in_play'], 3)})" for r in bad) + '.\n')
m3 = res.get('metrica_game3_after_decision', {}).get('rows', [])
pff = res.get('pff_game_3839_after_decision')
if m3 or pff:
    parts = []
    lab = {'tactical': 'yalnız taktik kamera', 'fill_good': 'iyi yayınla doldurma', 'fill_medium': 'orta yayınla doldurma', 'view42': '42 m penceresi',
           'tactical_sim2': 'yazarın benzeticisi'}
    if m3:
        parts.append('Metrica 3, bir yeni kopya (v2.11 → birleşik): ' + '; '.join(
            f"{lab[r['condition']]} {tr(r['v2_11']['spell_f1'])} → {tr(r['fused']['spell_f1'])}" for r in m3) + '.')
    if pff:
        parts.append(f"PFF maçı (K009; gerçek yayın takibi, top oyun içindeki karelerin {tr(pff['ball_visible_in_play'], 2)}'inde görünüyor; lisansı yayımlanmamış, "
                     f"seçimde kullanılmaz): v2.11 {tr(pff['v2_11']['spell_f1'])}, birleşik {tr(pff['fused']['spell_f1'])}, ağ tek başına {tr(pff['tcn_alone']['spell_f1'])} "
                     f"(macroF1 {tr(pff['v2_11']['macro_f1'], 3)} / {tr(pff['fused']['macro_f1'], 3)} / {tr(pff['tcn_alone']['macro_f1'], 3)}).")
    out.append('**Karardan sonra, bir kez (kapı değil).** ' + ' '.join(parts) + '\n')
out.append(f"""**Yorum (çıkarım, ölçüm değil).**
- Ağırlık 0,2 ile ağ yalnız bizim modelin kararsız olduğu yerlerde söz sahibi olur: bir sınıfın olasılığını en çok 0,2 kaydırabilir.
  Kazanç v2.14'ünkinden küçüktür ({tr(tac['diff_spell_f1_mean'], sign=True)}; v2.14: {tr(r214['summary']['tactical']['diff_spell_f1_mean'], sign=True)}), kopyalar arası oynaklık da.
- Ağ tek başına bu 16 kopyada {tr(tac['tcn_alone']['spell_f1'])}, v2.11 {tr(tac['v2_11']['spell_f1'])}.
- Üç denemenin üçü de yeni kopyalarda ölçüldü; ama aynı kapılar üç kez denendi. Tek tek kopyalara bakan G4'ü, daha temkinli
  ayarla yeniden denenen bir tasarım daha kolay geçer. Bu yüzden sonuç "birleşik sistem dış kopyalarda ortalamada daha iyi ve bu
  ağırlıkla hiçbir kopyada belirgin kötü değil" diye okunmalı; sağlanan maç için bir ölçüm değildir.""")
out.append("""
**Sınırlar.** K012'deki sınırların hepsi geçerli (kullanılmış doğrulama maçları; ağırlıkları doğrulayan sürecin eğitmesi; ağın
yalnız ekibin iki benzeticisini görmesi; benzetilmiş bozma, kamera ve yayın; vekil Metrica etiketleri). Ek olarak: ağırlık, v2.14
doğrulamasının kopyaları da kullanılarak seçildi; gürültülü yolda (v2.3) havuzlama yapılmaz ve o yol için hiçbir ölçüm yoktur.
Betikler: `experiments/possession_v2/v215/` (ağırlık dosyaları ve eğitim: `v214/`).
""")
reh_file = REPO / 'possession-v215-rehearsal.json'
if sel and reh_file.exists() and len(sys.argv) >= 6:
    n310, s310, n313, s313 = (int(x) for x in sys.argv[2:6])
    reh = json.loads(reh_file.read_text())
    rel = json.loads((REPO / 'possession-v215-release.json').read_text())
    new, old = reh['delivered_file_against_the_bundle_labels'], reh['for_comparison_the_v2.11k_chain_file_13_Nov']
    dif = reh['against_the_v2.11k_file']
    out.append(f"""**Bütünleştirme (15 Kasım, karardan sonra).** Kayıtlı karar kuralı, v2.15'in teslimde v2.11k'nın yerini alması için beş
denetim (16 Kasım 23:59'a kadar) ve bir koşul yazar. Durum:
- *Kod ve ağırlıklar.* `possession/tcn/` (commit `167dc7b`'nin çıkarım modüllerinin bayt kopyaları), `possession/pooling.py` (doğrulanan
  dosya), `possession/run215.py` (dondurulmuş `run211.py`'den türetildi: yalnız puanlanan bloklar, havuzlama, başlama vuruşu
  kuralı), `models/possession-tcn-v215.npz` (üç `dfl6_both` üyesi; SHA-256 değerleri plandakilerle aynı). Manifest
  `possession-v215-release.json` ({rel['frozen_at'][11:16]}): {len(rel['source_sha256'])} kaynak dosya, iki ağaç paketi ve ağ ağırlıkları. Havuzlama kapatılınca
  `run215`, `run211k`'nın dosyasını bayt bayt yazar (test eder). Merdiven: v2.15 → v2.11k → v2.11g → v2.9g → v2.5b → v2.5b yalnız
  taktik kamera. Kuralsız yedek (`possession-release-graded-windows.json`) değişmedi; orada ikinci model de yoktur.
- *Python 3.10 / numpy 1.26.4.* Ağ bu ortamda çalışıyor. Dokuz sentetik paketin (ikisi ağla) çıktısı 3.10 / 1.26.4 ve 3.13 / 2.5.3
  altında bayt bayt aynı (`tests/test_possession_crossplatform.py`). Ağın yuvarlanmamış olasılıkları iki ortamda farklı, 4 basamağa
  yuvarlanmışları aynı; başka bir işlemcide farklı çıkması olası değil ama dışlanamaz, zincirin `PLATFORM` adımı bunu
  dosyanın üretildiği bilgisayarda denetler.
- *Testler.* 3.10'da {n310} test ({s310} atlandı), 3.13'te {n313} test ({s313} atlandı); hepsi geçti. `tests/test_possession_final_test.py`
  güncellendi: son test planının teslim edilen ilk basamak için değil, ikinci modelsiz sürüm (v2.11k, ikinci basamak) için kayıtlı
  olduğunu denetler.
- *Tam boy prova* (`possession-v215-rehearsal.json`): K003'ün sentetik paketi ve K011'in uydurma Smart Tagging dosyası, varsayılan
  zincir, Python 3.10. Bütün adımlar OK; {reh['seconds']} sn (v2.11k zinciri {reh['seconds_of_the_v2.11k_chain_13_Nov']} sn; ağla bir üretim bu ortamda yaklaşık beş dakika daha uzun sürdü), en çok {tr(reh['peak_child_rss_gb'], 2)} GB. Teslim dosyası
  v2.11k zincirinin dosyasından {format(dif['frames_that_differ'], ',').replace(',', '.')} karede farklı (puanlanan karelerin %{tr(100 * dif['share_of_graded_frames'], 1)}'sı), hepsi başlama vuruşlarından sonra.
  O paketin vekil etiketlerine göre spellF1 {tr(new['graded windows']['spell_f1_mean'])} (v2.11k zinciri {tr(old['graded windows']['spell_f1_mean'])}), macroF1 {tr(new['graded windows']['macro_f1'])} ({tr(old['graded windows']['macro_f1'])}).
  Bu bir bağlantı ve boyut denetimidir: paket Metrica 2 ve 3'ün bozuk kopyalarıdır, karardan sonra bir kez çalıştırıldı, hiçbir
  seçimde kullanılmadı ve doğruluk iddiası değildir.
- *Belgeler.* `TECHNICAL_DOCUMENT.md` (adım 9, üç deneme, eğitim verisi, sınırlar), `TECHNICAL_DOCUMENT_V2.md` (dördüncü ek),
  `README.md`, `DATA_SOURCES.md`, `AGENTS.md`, Türkçe rehber ve `CLAUDE.md` güncellendi.
- *Son test planı yeniden kaydedilmedi.* `possession-final-test-plan.json` v2.11k için kayıtlı kalır. Ağın tasarımcısı J03WMX'i
  geliştirme sırasında kullandığı için v2.15'in o maçtaki sonucu "taze test" olmazdı; yayımlanan ağırlıklar o maç olmadan eğitildi
  ve sürümü kuran süreç maçı indirmedi. `SON-TEST.cmd` çalıştırılırsa sonuç v2.11k'nın sonucu olarak yazılır.
- **Açık koşul.** Karar kuralının son şartı: teslim zincirinin ekibin bilgisayarında OK bitmesi (`URETIM` ve `TESLIM` satırlarında
  possession-v2.15). Bu kayıt yazılırken zincir orada henüz çalıştırılmadı. Zincir daha alt bir basamağa düşerse teslim edilen o
  basamaktır ve belgelerin ilk satırları buna göre düzeltilir.
""")
open(V / 'k013_body.md', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
