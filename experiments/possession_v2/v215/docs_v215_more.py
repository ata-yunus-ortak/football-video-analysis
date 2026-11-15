"""More documents for a SELECTED possession-v2.15 (after docs_v215_en.py): TECHNICAL_DOCUMENT_V2.md (header, fourth
addendum, reproduction), docs/SAHIPLIK_V2_TR.md, TEAM_START_TR.md, experiments/possession_v2/README.md.
Usage: docs_v215_more.py REPO_DIR"""
import json, sys
from pathlib import Path

REPO = Path(sys.argv[1])
res = json.loads((REPO / 'possession-v215-results.json').read_text())
r214 = json.loads((REPO / 'possession-v214-results.json').read_text())
plan = json.loads((REPO / 'possession-v215-plan.json').read_text())
assert res['selected'] and all(res['gates'].values())
S, S4 = res['summary'], r214['summary']
W = plan['fusion_rule_fixed_before_any_score']['weight']
f4 = lambda x: f'{x:.4f}'
sg = lambda x: f'{x:+.4f}'
tr = lambda x, nd=4, sign=False: (f'{x:+.{nd}f}' if sign else f'{x:.{nd}f}').replace('.', ',').replace('-', '−')


def edit(name, pairs):
    p = REPO / name
    s = p.read_text(encoding='utf-8')
    for a, b in pairs:
        assert s.count(a) == 1, (name, s.count(a), a[:70])
        s = s.replace(a, b)
    p.write_text(s, encoding='utf-8')


def worst(rows, cond, names=None):
    return min(r['diff_spell_f1'] for r in rows if r['condition'] == cond and (names is None or r['copy'].split('|')[0] in names))


def en_row(label, s, w):
    return (f"   | {label} | {s['n']} | {f4(s['v2_11']['spell_f1'])} | {f4(s['fused']['spell_f1'])} | {sg(s['diff_spell_f1_mean'])} | "
            f"{s['copies_better']} / {s['copies_worse']} | {sg(w)} | {f4(s['tcn_alone']['spell_f1'])} |")


DFL, MET = ('J03WN1', 'J03WR9'), ('MET1', 'MET2')
T4, T5 = S4['tactical'], S['tactical']
NT = T4['n'] + T5['n']
NB = T4['copies_better'] + T5['copies_better']
NW = T4['copies_worse'] + T5['copies_worse']
NE = NT - NB - NW
assert (NT, NB, NW, NE) == (32, 29, 1, 2), (NT, NB, NW, NE)


def en_table(R, SS):
    rows = R['rows']
    return '\n'.join([
        '   | condition | copies | v2.11 | pooled | difference | better / worse | worst copy | network alone |',
        '   |---|---|---|---|---|---|---|---|',
        en_row('tactical camera only, all (G1, G4, G5)', SS['tactical'], worst(rows, 'tactical')),
        en_row('tactical camera only, DFL (G2)', SS['tactical_DFL'], worst(rows, 'tactical', DFL)),
        en_row('tactical camera only, Metrica (G3)', SS['tactical_Metrica'], worst(rows, 'tactical', MET)),
        en_row('simulated accurate broadcast, fill (G6)', SS['fill_good'], worst(rows, 'fill_good')),
        en_row('simulated medium broadcast, fill (G6)', SS['fill_medium'], worst(rows, 'fill_medium')),
        en_row('camera window 42 m (reported)', SS['view42'], worst(rows, 'view42')),
        en_row("copies made with the network author's simulator (G7)", SS['tactical_sim2'], worst(rows, 'tactical_sim2'))])


T, T4 = S['tactical'], S4['tactical']
addendum = f"""> **Fourth addendum, 15 November 2026 (v2.15): a second model family.** The submitted entry point is now
> `python -m possession.run215` (release manifest `possession-v215-release.json`). `possession.run211k` is
> unchanged and is the next step of the technical fall-back ladder. Log entries K012 and K013 have the
> full record.
>
> 1. **What changed.** On the core model path (measured noise at most 0.30 m) the second-stage
>    probabilities of the tree models are averaged with those of a temporal convolution network
>    (weight {W} for the network) and the average goes through the unchanged decoder
>    (`possession/pooling.py`). The network is the one of the third addendum, item 4: 37 team-level
>    features per frame, 12.5 Hz, about 25 s of context on either side, NumPy float64 inference
>    (`possession/tcn/`, byte copies of commit `167dc7b` of branch `mtah-possession`, written by a team
>    member). Its weights (`models/possession-tcn-v215.npz`, three members) were trained by us for this
>    release. On the v2.3 path nothing is averaged and the output is that of `possession.run211k`.
>    Everything before the decoder and the kick-off rule after it are unchanged.
> 2. **Why the first attempt (v2.13) failed.** A diagnosis on the copies already scored for v2.13
>    (development data from then on) found: (a) the committed weights were trained with one corruption
>    simulator and broke on the false ball detections of the other (alone, on one Metrica game 3
>    copy: 0.686 with our corruption, 0.733 with its false detections switched off, 0.742 on clean
>    tracking); (b) his single-cost decoder dropped the dead-ball entry and exit costs of our decoder:
>    with his committed weights, the same probabilities through our decoder with weight 0.2 gave
>    +0.0137 on 22 development copies where his rule gave +0.0108 with a worst copy of -0.0295;
>    (c) the DFL rows had used single-seed weights.
> 3. **Re-training.** PyTorch could not be installed in the development environment, so his training
>    script was re-implemented in JAX (`experiments/possession_v2/v214/tcn_jax.py`; same architecture,
>    optimiser and schedule; constant Adam momentum; the network was compared with his NumPy inference
>    on random input, largest difference of the probabilities 7.9e-7). Training data: the six DFL
>    matches of the tree bundles, twelve corrupted copies of every half, six made with his simulator
>    and six with ours, half of them with the teams exchanged. Three seeds on four matches (used for
>    the DFL validation rows, like our four-match validation models) and three on six matches (the
>    Metrica rows and the release).
> 4. **Second attempt (v2.14), not selected.** Arithmetic pool with weight 0.5 (chosen on the 22
>    development copies by a rule written down beforehand), our decoder. Plan
>    `possession-v214-plan.json` (14 November 23:33), 16 new copies, the six gates of v2.12 / v2.13
>    plus a seventh on copies made with his simulator. Results (`possession-v214-results.json`):
>
{en_table(r214, S4)}
>
>    Six gates passed; G4 (no copy below -0.010) failed on one Metrica copy ({sg(T4['diff_spell_f1_min'])}), so v2.14 was
>    not released.
> 5. **Third and last attempt (v2.15), selected.** The conditions were written down while the second
>    validation was running: only if its mean gates passed; the same weights, pool and decoder; only
>    a smaller weight, chosen from 0.1, 0.2, 0.3 on the 42 development copies (the 22 earlier ones and
>    20 copies of the v2.14 validation, after its decision) as the largest mean without a copy below
>    -0.007; unchanged gates; new copies; no further attempt. The rule gave {W}. Plan
>    `possession-v215-plan.json` (15 November 01:17), results `possession-v215-results.json`:
>
{en_table(res, S)}
>
>    All seven gates passed. Recall of possessions under 2 s: {S['tactical']['v2_11']['recall_under_2s_iou03']:.3f} -> {S['tactical']['fused']['recall_under_2s_iou03']:.3f}; predicted
>    possessions per copy {S['tactical']['v2_11']['pred_spells_per_copy']:.0f} -> {S['tactical']['fused']['pred_spells_per_copy']:.0f} (labels: {S['tactical']['gt_spells_per_copy']:.0f}).
> 6. **How to read it.** The same gates were applied three times to three designs, each time on new
>    copies. A gate on single copies is passed more easily by a design that is tried again with a
>    more cautious setting, so this pass is weaker evidence than a pass at the first attempt. What
>    the two validations with re-trained weights and our decoder agree on: of their {NT} new
>    tactical-camera copies the average was better than the trees alone on {NB}, equal on {NE} (copies
>    on the v2.3 path, where nothing is averaged) and worse on {NW}, and with the small weight no
>    copy was worse. The validation matches had been used before, the network saw both of the
>    team's corruption simulators and nothing else, and its weights were trained by the process
>    that validated them.
> 7. **Integration.** `possession.run215` is `possession.run211` with the graded windows, the
>    pooling and the kick-off rule; with the pooling switched off it writes the bytes of
>    `possession.run211k` (test). The cross-platform check has nine synthetic variants (two with the
>    network); the 4-decimal network probabilities and the output were identical under Python 3.10 /
>    numpy 1.26.4 and Python 3.13 / numpy 2.5.3, the unrounded network outputs were not.
> 8. **Final test.** The plan of the final test on J03WMX stays registered for `possession.run211k`,
>    the release without the second model. For the network's design that match is not untouched
>    (its author used it during development), so a run of v2.15 on it could not be reported as a
>    fresh test; the released weights were trained without it.

"""
edit('TECHNICAL_DOCUMENT_V2.md', [
 ('# Possession v2 — technical document (full record; current release: v2.11k)', '# Possession v2 — technical document (full record; current release: v2.15)'),
 ('Submission file regenerated with `python -m possession.run211k` (see the three addenda and Reproduction).',
  'Submission file regenerated with `python -m possession.run215` (see the four addenda and Reproduction).'),
 ('## 1. Summary\n', addendum + '## 1. Summary\n'),
 ('python -m possession.run211k --data-dir <bundle root containing tactical/ and broadcast/> --out <new folder> \\',
  'python -m possession.run215 --data-dir <bundle root containing tactical/ and broadcast/> --out <new folder> \\'),
 ('''goalkeeper check moved anything and whether a kick-off tag was used. Without broadcast files, or when
the accuracy gate is closed, and when the goalkeeper check moves nothing, the release
(`possession.run211k`) writes the file that `python -m possession.run25` writes from the tactical
camera alone, except for the frames that the kick-off rule sets to `D` (third addendum).''',
  '''goalkeeper check moved anything, whether a kick-off tag was used and whether the second model was
pooled. Without broadcast files, or when the accuracy gate is closed, and when the goalkeeper check
moves nothing, `possession.run211k` (the release without the second model, and the release itself on
the v2.3 path) writes the file that `python -m possession.run25` writes from the tactical camera
alone, except for the frames that the kick-off rule sets to `D` (third addendum).'''),
 ('''`possession.run211k` (like `possession.run211`, `possession.run29` and `possession.run25`) reads `tactical/BAR-ATH_tactical_atd.xml` and `_atd.txt`,''',
  '''`possession.run215` (like `possession.run211k`, `possession.run211`, `possession.run29` and `possession.run25`) reads `tactical/BAR-ATH_tactical_atd.xml` and `_atd.txt`,'''),
 ('''given, the two clock-observation files; `run211k` also reads the "Kick Off (Start)" tags of
`tactical/BAR-ATH_tactical_smart_tagging.xml`. It checks every source file and both bundles against the release
manifests (`possession-v211k-release.json` and, through it, `possession-v211g-release.json` and `possession-v211-release.json`,
which lists every inference source and both bundles) and the bundle cards, and''',
  '''given, the two clock-observation files; `run215` and `run211k` also read the "Kick Off (Start)" tags of
`tactical/BAR-ATH_tactical_smart_tagging.xml`. It checks every source file, both tree bundles and the network weights
against the release manifest (`possession-v215-release.json`, which lists every inference source and the three model
files; the lower steps have `possession-v211k-release.json`, `possession-v211g-release.json` and
`possession-v211-release.json`) and the bundle cards, and'''),
])
print('TECHNICAL_DOCUMENT_V2.md edited')

# ------------------------------------------------------------------------------------------ Turkish guide
tr_section = f"""
## Güncelleme, 15 Kasım 2026: v2.15 — ikinci model eklendi (üçüncü denemede)

Teslim sistemi artık **possession-v2.15** (`python -m possession.run215`). Çalıştırma aynı: `TESLIM-HAZIRLA.cmd`
(seçenek gerekmez). Bir alt basamak v2.11k'dır (aynı sistem, ikinci model olmadan). Ayrıntılı kayıt:
`docs/DENEY_KAYDI_TR.md` K012 ve K013.

**Ne değişti.** Bizim ağaç modellerimiz her kare için "ölü top / ev sahibi / deplasman" olasılığı veriyor. Takım
arkadaşımızın tasarladığı sinir ağı (TCN) da aynı şeyi veriyor. v2.15 bu iki olasılığın ağırlıklı ortalamasını alır
(ağ {tr(W, 1)}, ağaçlar {tr(1 - W, 1)}) ve sahiplikleri **bizim çözücümüzle** bu ortalamadan çıkarır. Ağın payı küçük olduğu için
ağaçların emin olduğu yerde sonucu değiştiremez; ağaçların kararsız kaldığı yerde söz sahibi olur.

**Buraya nasıl gelindi (üç deneme).**
1. *v2.13 (13 Kasım, geçmedi):* arkadaşımızın kendi ağırlıkları ve kendi çözücüsü. Ortalama kazanç küçüktü, DFL'de eksiydi.
2. *Teşhis:* ağ yalnız kendi "bozma" yöntemiyle eğitilmişti ve bizim kopyalarımızdaki sahte top algılamalarına
   dayanamıyordu; ayrıca onun çözücüsü bizimkinin ölü top maliyetlerini kullanmıyordu. Ağı burada, iki bozma yöntemiyle
   birlikte yeniden eğittik (altı model).
3. *v2.14 (14-15 Kasım, geçmedi):* yeni ağırlıklar, bizim çözücü, eşit ağırlık. 16 yeni kopyanın {T4['copies_better']} tanesinde daha iyi
   (ortalama {tr(T4['diff_spell_f1_mean'], sign=True)}), ama bir kopyada {tr(T4['diff_spell_f1_min'], sign=True)}. "Hiçbir kopya −0,010'dan kötü olmasın" şartı geçmedi; şartı
   gevşetmedik, aday seçilmedi.
4. *v2.15 (15 Kasım, geçti):* aynı sistem, ağın payı {tr(W, 1)}. Bu ağırlık, ikinci ölçüm sürerken yazılan bir kuralla seçildi.
   Yine yeni 16 kopya, aynı yedi şart: ortalama {tr(T['diff_spell_f1_mean'], sign=True)} ({tr(T['v2_11']['spell_f1'])} → {tr(T['fused']['spell_f1'])}), {T['n']} kopyanın {T['copies_better']} tanesinde daha iyi,
   en kötü kopya {tr(res['gate_values_unrounded']['tactical']['diff_spell_f1_min'], sign=True)}; yedi şartın yedisi geçti.

**Dürüst sınırlar.** Aynı şartlar üç kez denendi; üçüncüde geçmek, ilkinde geçmekten daha zayıf bir kanıttır. Ölçümler
başka maçların bozulmuş kopyalarında yapıldı; sağlanan maç için bir ölçüm yoktur. Ağ yalnız bizim iki bozma yöntemimizi
gördü. Ağırlıkları doğrulamayı yapan süreç eğitti. Gürültülü veri yolunda (v2.3) ikinci model kullanılmaz.

**Zincirde ne değişti.** `PLATFORM` artık dokuz sentetik varyantı karşılaştırır (ikisi ağla). Belge ekinde (Ek R)
"Second model" satırı vardır: kullanıldı / kullanılmadı. Depoya yeni bir model dosyası girdi
(`models/possession-tcn-v215.npz`, yaklaşık 10 MB; yalnız açık DFL verisiyle eğitildi).

*Öğrenilecek şey:* bir fikir ilk ölçümde başarısız olunca iki yol vardır: bırakmak ya da **neden** başarısız olduğunu
bulmak. Nedeni bulunca (yanlış eğitim verisi, yanlış çözücü) düzeltilmiş hâli yeniden ölçülebilir; ama her yeni ölçüm
yeni veride ve şartlar önceden yazılarak yapılmalı, kaç kez denendiği de açıkça yazılmalıdır.
"""
edit('docs/SAHIPLIK_V2_TR.md', [
 ('''  (yaklaşık 420 MB, kamuya açık veri, CC BY 4.0; bir takım üyesi bu maçı sürüme girmeyen ayrı bir
  model için kullandı). Maçın dört bozuk kopyası, sağlanan dosyaların düzeninde dosyalara yazılır ve
  dondurulmuş sürümün giriş noktası (`possession.run211k`) bu dosyalarda çalıştırılır''',
  '''  (yaklaşık 420 MB, kamuya açık veri, CC BY 4.0; bir takım üyesi bu maçı, 15 Kasım'da sürüme giren
  ikinci modelin tasarımını geliştirirken kullandı; sürümdeki ağırlıklar bu maç olmadan eğitildi).
  Maçın dört bozuk kopyası, sağlanan dosyaların düzeninde dosyalara yazılır ve ikinci modelsiz
  sürümün (v2.11k) giriş noktası (`possession.run211k`) bu dosyalarda çalıştırılır'''),
 ('''- **Neden:** sürümün doğrulama maçları seçim sırasında defalarca kullanıldı. Bu, sürümün hiçbir
  kararında rol oynamamış bir maçtaki tek ölçüm olur ve teknik belgeye "ayrılmış maç, dondurmadan
  sonra bir kez" diye yazılır.''',
  '''- **Neden:** sürümün doğrulama maçları seçim sırasında defalarca kullanıldı. Bu, ağaç modellerinin
  (v2.11k) hiçbir kararında rol oynamamış bir maçtaki tek ölçüm olur ve teknik belgeye "ayrılmış maç,
  dondurmadan sonra bir kez, ikinci model olmadan" diye yazılır.
- **15 Kasım notu:** bu test v2.15 için yeniden kaydedilmedi. İkinci modelin tasarımı bu maçı
  gördüğü için v2.15'in bu maçtaki sonucu "taze test" olmazdı. Sonuç, v2.11k'nın (ikinci modelsiz
  sistemin) sonucu olarak yazılır.'''),
 ('''> **Güncel durum (13 Kasım 2026):** teslim sistemi **v2.11k**'dir (`python -m possession.run211k`).
> Aşağıda anlatılan v2.5 sisteminin üstüne gelen ekler belgenin sonundaki "Güncelleme" bölümlerindedir
> (v2.9, v2.11 ve 13 Kasım: başlama vuruşu kuralı). Bir alt teknik basamak v2.11g'dir.''',
  '''> **Güncel durum (15 Kasım 2026):** teslim sistemi **v2.15**'tir (`python -m possession.run215`).
> Aşağıda anlatılan v2.5 sisteminin üstüne gelen ekler belgenin sonundaki "Güncelleme" bölümlerindedir
> (v2.9, v2.11, 13 Kasım: başlama vuruşu kuralı, 15 Kasım: ikinci model). Bir alt teknik basamak v2.11k'dır.'''),
 ('`possession-v2.11k` → `possession-v2.11g` → `possession-v2.9g` → v2.5b → v2.5b yalnız taktik kamera.',
  '`possession-v2.15` → `possession-v2.11k` → `possession-v2.11g` → `possession-v2.9g` → v2.5b → v2.5b yalnız taktik kamera\n(15 Kasım\'dan beri; v2.15 için belgenin sonundaki güncellemeye bakın).'),
 ('.\\.venv-possession\\Scripts\\python.exe -m possession.run211k --data-dir <veri kökü> --out <yeni klasör> --tactical-clock <saat>\\tactical --broadcast-clock <saat>\\broadcast',
  '.\\.venv-possession\\Scripts\\python.exe -m possession.run215 --data-dir <veri kökü> --out <yeni klasör> --tactical-clock <saat>\\tactical --broadcast-clock <saat>\\broadcast'),
])
p = REPO / 'docs/SAHIPLIK_V2_TR.md'
p.write_text(p.read_text(encoding='utf-8').rstrip('\n') + '\n' + tr_section, encoding='utf-8')
edit('TEAM_START_TR.md', [
 ('> **Güncel teslim sistemi (13 Kasım 2026): `possession/` paketi, sürüm possession-v2.11k.**',
  '> **Güncel teslim sistemi (15 Kasım 2026): `possession/` paketi, sürüm possession-v2.15.**'),
])
print('Turkish guide edited')
