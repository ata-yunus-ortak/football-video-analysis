"""Write log entry K012 (Turkish) from the registered plan, the development summary and the results of the v2.14
validation. Usage: /usr/bin/python3 k012.py REPO_DIR   (prints; body in v214/k012_body.md; v215/log_k012_k013.py puts
the bodies of K012 and K013 into docs/DENEY_KAYDI_TR.md)"""
import json, sys
from pathlib import Path

REPO = Path(sys.argv[1])
V = Path('/home/claude/work/v214')
plan = json.loads((REPO / 'possession-v214-plan.json').read_text())
res = json.loads((REPO / 'possession-v214-results.json').read_text())
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


T = dev['table_retrained_weights']; TH = dev['table_committed_weights']; D = dev['diagnostic_metrica3_seed7772']
grid = ['ari20', 'ari30', 'ari40', 'ari50', 'ari60', 'geo30', 'geo40', 'geo50', 'geo60']
name_tr = lambda n: ('aritmetik ' if n.startswith('ari') else 'geometrik ') + '0,' + n[3:4]
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
title = ('teslim sistemi v2.14' if sel else 'kayıtlı kapılardan geçmedi')
out = []
out.append(f"## K012 — v2.14 adayı: ikinci model iki benzeticiyle yeniden eğitildi ve bizim çözücümüzle birleştirildi; {title}, 14-15 Kasım 2026\n")
out.append("""**Neden ikinci bir deneme.** v2.13 (K010) üç kapıdan geçmedi ve seçilmedi; o kayıt ve kapıları değişmedi. Takım lideri
14 Kasım 18:23'te teslimden önce son bir deneme istedi. Yeni bir aday ancak yeni bir planla ve plan sonuçlardan önce
kaydedilerek ölçülebilir; bu kayıt o denemedir. Sağlanan maçın hiçbir dosyası okunmadı, çalıştırılmadı, puanlanmadı.
""")
out.append(f"""**Teşhis (geliştirme; yalnız daha önce puanlanmış kopyalarda).** v2.13 doğrulamasının 20 kopyası (tohum 13100-13133 ve
63100-63103) ile karardan sonra puanlanan iki Metrica 3 kopyası (33103, 63108) artık geliştirme verisidir; teşhis için bir
Metrica 3 kopyası daha üretildi (tohum 7772). Bunların hiçbiri doğrulama değildir. Bulunanlar:
- *Sahte top algılamaları.* Yazarın ağırlıkları (`tcn_dfl6.npz`) tek başına, 7772 kopyasında, bizim benzeticinin bir bileşeni
  kapatılarak (spellF1): hepsi açık {tr(D['ours'], 3)}; yanlış takımlı izler kapalı {tr(D['no_flips'], 3)}; konum gürültüsü düşük
  {tr(D['low_noise'], 3)}; oyuncu kayıpları kapalı {tr(D['no_player_miss'], 3)}; **sahte top algılamaları kapalı {tr(D['no_fp'], 3)}**; bozulmamış
  veri {tr(D['clean'], 3)}; yazarın kendi benzeticisi {tr(D['sim2'], 3)}. Onun benzeticisinde sahte algılamalar daha seyrektir ve hep bir
  oyuncunun üstündedir; bizimkinde dört kata kadar sıktır ve yarısı sahada rastgele bir yerdedir. Ağ bunları eğitimde görmemişti.
- *Ezber.* Aynı ağırlıklar bir eğitim maçında (J03WOH, bizim bozmamızla) 0,817 aldı. Eğitim maçları bu yüzden teşhiste kullanılmadı.
- *Çözücü ve ağırlık.* Yazarın ağırlıklarıyla, 22 geliştirme kopyasında, v2.11'e göre ortalama fark: v2.13 kuralı (ağırlık 0,5, her
  değişime tek maliyet) {tr(TH['all 22']['v213rule']['mean'], sign=True)} (DFL'de {tr(TH['DFL 10']['v213rule']['mean'], sign=True)}, en kötü kopya {tr(TH['all 22']['v213rule']['min'], sign=True)}); aynı
  olasılıklar ağırlık 0,2 ile ve bizim çözücümüzden geçirilince {tr(TH['all 22']['ari20']['mean'], sign=True)} (DFL'de {tr(TH['DFL 10']['ari20']['mean'], sign=True)}, en kötü kopya
  {tr(TH['all 22']['ari20']['min'], sign=True)}, 22 kopyanın {TH['all 22']['ari20']['better']} tanesinde iyi). Tek maliyetli çözücü, bizim çözücünün ölü topa giriş ve çıkış
  maliyetlerini (60) kullanmıyordu.
- *Tek tohum.* v2.13'te DFL satırları tek tohumlu ağırlıklarla, Metrica satırları üç tohumla ölçülmüştü.
""")
out.append(f"""**Yeniden eğitim.** PyTorch bu ortama kurulamadı; yazarın eğitim betiği JAX ile yeniden yazıldı
(`experiments/possession_v2/v214/tcn_jax.py`). Mimari, 37 özellik ve NumPy çıkarımı onundur (dal `mtah-possession`, commit
`167dc7b`); çıkarım modülleri bayt bayt kopyadır. Onun betiğinden farklar: Adam momenti sabit 0,9 (PyTorch'un OneCycleLR'ı onu da
değiştirir); başlangıç değerleri ve rastgele akışlar JAX / NumPy'nin; her devre için 12 bozuk kopya ve 6 tur (onunki 6 kopya ve
12 tur; eğitim maçı başına adım sayısı aynı); hazır verimizde top yüksekliği olmadığı için onun benzeticisinin yükseklik terimi
çalışmaz. JAX ağı ile onun NumPy çıkarımı rastgele girdi ve ağırlıklarda karşılaştırıldı: en büyük olasılık farkı 7,9e-7.
- *Veri:* yalnız açık DFL maçları (CC BY 4.0), sağlayıcının kare etiketleri. 12 kopyanın 6'sı onun benzeticisiyle
  (`tcn/degrade.py`), 6'sı bizimkiyle (`possession/degrade.py`, v2 profili) bozuldu; tek numaralı kopyalarda takımlar yer değiştirdi.
- *Modeller (üçer tohum):* `dfl4_both_s0-2`: J03WOH, J03WOY, J03WPY, J03WQQ (bizim doğrulama modellerimizin dört maçı; DFL
  doğrulama satırları için). `dfl6_both_s0-2`: altı maç (Metrica satırları için; seçilirse yayımlanacak ağırlıklar). Bir model
  2 işlemcide 26-40 dakika sürdü.
- *İlk deneme modeli* (J03WN1'siz beş maç, tek tohum): beş J03WN1 geliştirme kopyasında tek başına v2.11'e göre +0,0016
  (yazarın beş maçlık ağırlıkları −0,0326); beş kopyanın beşinde, onun kendi benzeticisinin kopyası dahil, yazarın
  ağırlıklarından iyi.
- *Üçer üyeli yeni ağırlıklar tek başına*, 22 geliştirme kopyasında: v2.11'e göre {tr(T['all 22']['tcn_alone']['mean'], sign=True)} (DFL {tr(T['DFL 10']['tcn_alone']['mean'], sign=True)},
  Metrica {tr(T['Metrica 12']['tcn_alone']['mean'], sign=True)}); yazarın ağırlıkları aynı kopyalarda {tr(TH['all 22']['tcn_alone']['mean'], sign=True)}. Tek tek kopyalarda hâlâ oynak
  (en kötü {tr(T['all 22']['tcn_alone']['min'], sign=True)}).
""")
out.append("""**Havuzlama kuralının seçimi (geliştirme).** İki modelin üç sınıflı olasılıkları ağırlıklı ortalamayla birleştirilir, sonuç
yeniden P(ölü) ve P(ev | canlı) yapılır ve **değişmemiş v2 çözücüsünden** geçer (`fuse2.py`). Denenen ayarlar: aritmetik ortalama,
ağırlık 0,2-0,6; geometrik ortalama, ağırlık 0,3-0,6. Seçim kuralı 14 Kasım 21:23'te, yeni ağırlıkların DFL satırları görüldükten
sonra ve Metrica satırları henüz yokken yazıldı: (1) herhangi bir geliştirme kopyasında −0,010'dan kötü olan ayar elenir; (2)
kalanlardan ortalaması en büyük olan alınır; (3) ona 0,001'den yakın olanlar eşit sayılır ve en küçük ağırlık kazanır (aynı
ağırlıkta iki havuz varsa ortalaması büyük olan). 22 geliştirme kopyasında (ortalama fark | en kötü kopya | iyi olan kopya):
""")
out.append('| ayar | hepsi (22) | DFL (10) | Metrica (12) | yazarın benzeticisi (5) |\n|---|---|---|---|---|')
for n in grid:
    cell = lambda g: f"{tr(T[g][n]['mean'], sign=True)} \\| {tr(T[g][n]['min'], sign=True)} \\| {T[g][n]['better']}"
    out.append(f"| {name_tr(n)} | {cell('all 22')} | {cell('DFL 10')} | {cell('Metrica 12')} | {cell('his simulator 5')} |")
out.append(f"""
Kural **aritmetik ortalama, ağırlık 0,5** verdi (ortalama {tr(dev['unrounded_means']['ari50'], 6, sign=True)}; geometrik 0,5 {tr(dev['unrounded_means']['geo50'], 6, sign=True)} ile aynı
ağırlıkta ve ortalaması daha küçük; geometrik 0,4 {tr(dev['unrounded_means']['geo40'], 6, sign=True)} ile 0,001'den uzak). Bu, yazarın kendi karışım oranıdır; v2.13'e göre
değişen üç şey ağırlık dosyaları, üye sayısı ve çözücüdür. Çözücü sabitleri (takım değişimi 2-5, ölü topa giriş/çıkış 50-70, ölü
top eğilimi −0,1…−0,5) 10 DFL geliştirme kopyasında denendi: teslim sabitlerinden en çok 0,001 iyi ya da daha kötü; değiştirilmedi.
Gürültülü yol (v2.3; ölçülen gürültü 0,30 m'nin üstünde) için hiçbir ölçüm yapılmadı; aday o yolda havuzlama yapmaz, çıktı
v2.11k'nın çıktısıdır.
""")
out.append(f"""**Plan.** `possession-v214-plan.json`, 14 Kasım 23:33:40'ta kaydedildi; o anda adayın, yeni ağırlıkların ya da herhangi bir
havuzun yeni tohumlu bir kopyadaki hiçbir puanı yoktu (kayıttan önce görülenlerin tamamı planın
`seen_on_external_data_before_registration` bölümünde). Tasarım v2.13'ünkiyle aynıdır (`v213/exp_v213.py` değiştirilmeden içe
aktarılır), yalnız:
- yeni tohumlar: kopya 16100 + 10·maç + j, yayın 46100 / 46200, saat 56100 / 56200, yazarın benzeticisi 66100 + maç. Önce
  düşünülen 141xx dizisi eski dosyalardaki rastlantısal sayılarla (kare sayıları) çakıştığı için kayıttan önce değiştirildi;
  kaydedilen tohumların hiçbiri depodaki ya da çalışma alanındaki hiçbir dosyada geçmiyor (betik arar).
- DFL maçlarında ağ tarafı `dfl4_both` (üç üye; bizim doğrulama modelleriyle aynı dört maç), Metrica'da `dfl6_both` (üç üye) ve
  yayımlanan v2 paketleri.
- birleşik kol: `fuse2.pool` (aritmetik, 0,5) + `possession.decode` (yol sabitleri). v2.3 yoluna düşen bir kopyada fark tam 0'dır.
- kapılar: G1-G6, v2.12 ve v2.13'ün kapıları ve eşikleri, değişmeden; G7 eklendi: yazarın benzeticisiyle üretilen 4 kopyada
  ortalama fark ≥ 0 (v2.13'te yalnız rapor ediliyordu).
- v2.12 ve v2.13 planları sürüm değişikliği için son anı 14 Kasım 23:59 olarak yazmıştı. Bu plan, takım liderinin isteğiyle, daha
  geç bir an koyar (16 Kasım 23:59); bedeli, ekibin bilgisayarındaki denetimlere daha az zaman kalmasıdır (planın `limits` bölümü).
- Doğrulama betiği, kayıttan önce, bir geliştirme kopyasında (J03WN1 13100) saklanan olasılıklardan hesaplanan sayıları aynen
  verdi; eğitim maçı J03WOH'ta bağlantı denemesi yapıldı (puan hesaplamaz).
Ortam: Python 3.13.18, numpy 2.5.3, pandas 3.0.5, scikit-learn 1.9.1; eğitim için ayrıca jax 0.12.0.1, optax 0.2.9.
""")
out.append(f"**Sonuç** (`possession-v214-results.json`, kapılar 00:33'te uygulandı; spellF1, organizatörün ölçütü; yarışma puanı değil):\n")
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
when = '2026-11-15 00:33'            # the decision; the results file was written again later with the after-decision rows
if sel:
    out.append(f"""**Karar ({when}).** Yedi kapının yedisi geçti; kayıtlı kurala göre aday seçildi ve possession-v2.14 olarak
bütünleştirilir (ayrıntı aşağıda). Kapılar bir kez uygulandı; başka tohum, ağırlık, havuz ya da çözücü sabiti denenmedi.
""")
else:
    out.append(f"""**Karar ({when}).** {len(failed)} kapı geçmedi ({', '.join(failed)}); kayıtlı kurala göre aday teslim sistemine
girmedi, teslim sistemi **v2.11k** olarak kalır. Kapılar bir kez, bütün satırlara uygulandı; başka tohum, ağırlık, havuz ya da çözücü
sabiti denenmedi. İlk iki satır geldiğinde (14 Kasım 23:37) G4'ün geçemeyeceği belliydi; doğrulama yine de planlandığı gibi
tamamlandı.
""")
    if bad:
        out.append("−0,010'dan kötü kopyalar: " + '; '.join(
            f"{r['copy'].replace('|', ' ')} ({tr(r['diff_spell_f1'], sign=True)}; v2.11 {tr(r['v2_11']['spell_f1'])}, ağ tek başına {tr(r['tcn_alone']['spell_f1'])}, "
            f"oyun içinde topun göründüğü karelerin payı {tr(r['ball_visible_in_play'], 3)})" for r in bad) + '.\n')
b0 = bad[0] if bad else None
same_fill = [r for r in res['rows'] if b0 and r['copy'] == b0['copy'] and r['condition'] == 'fill_good']
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
- Ortalama kazanç tutarlı: yalnız taktik kamerada 16 kopyanın {tac['copies_better']} tanesi, DFL kopyalarının {S['tactical_DFL']['copies_better']} tanesi iyi; doldurma
  koşullarında, kamera penceresinde ve yazarın benzeticisinin kopyalarında da artı. v2.13'te DFL'de eksi olan fark (−0,0045) burada
  {tr(S['tactical_DFL']['diff_spell_f1_mean'], sign=True)}. Teşhisin gösterdiği üç değişiklik (iki benzeticiyle eğitim, üç üye, bizim çözücü) birlikte işe yaradı;
  hangisinin ne kadar katkı yaptığı bu doğrulamada ayrı ayrı ölçülmedi.
- Yeni ağırlıklarla ağ tek başına bu 16 kopyada v2.11 düzeyinde ({tr(tac['tcn_alone']['spell_f1'])} / {tr(tac['v2_11']['spell_f1'])}); yazarın ağırlıklarıyla v2.13
  doğrulamasında 0,6257 / 0,6598 idi. Tek tek kopyalarda hâlâ oynak.""")
if b0 is not None:
    out.append(f"""- Geçmeyen kapı tek kopyadan: {b0['copy'].replace('|', ', tohum ')}. O kopyada oyun içindeki karelerde topun görünme payı {tr(b0['ball_visible_in_play'], 3)};
  ağ tek başına {tr(b0['tcn_alone']['spell_f1'], 3)}, v2.11 {tr(b0['v2_11']['spell_f1'], 3)}, birleşik {tr(b0['fused']['spell_f1'], 3)}."""
               + (f" Aynı kopya iyi yayınla doldurulunca fark {tr(same_fill[0]['diff_spell_f1'], sign=True)}." if same_fill else '') + """
  Geliştirme kopyalarında top görünürlüğü benzer (0,36-0,38) üç kopya vardı ve üçünde de birleşik sistem iyiydi; görünürlük tek
  başına açıklamıyor. Ortalaması +0,02 olan bir farkın 16 kopyadan birinde −0,010'un altına düşmesi şaşırtıcı değil; kapı tam da bunu
  eliyor ve değiştirilmedi.""")
out.append("""
**Sınırlar.** Doğrulama maçları daha önceki bütün seçimlerde ve bu adayın geliştirilmesinde kullanıldı; yalnız kopyalar yeniydi.
Ağırlıkları doğrulamayı yapan süreç eğitti; eğitim betiğini başka kimse denetlemedi ve yeniden çalıştırma aynı bitleri vermez.
Bozma, slot paketleme, kamera penceresi ve yayın kamerası bizim benzetimimizdir; ağ yalnız ekibin iki benzeticisini gördü. DFL
etiketleri sağlayıcının kare etiketleri, Metrica etiketleri olaylardan türettiğimiz vekil etiketlerdir. Betikler:
`experiments/possession_v2/v214/`.
""")
open(V / 'k012_body.md', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
