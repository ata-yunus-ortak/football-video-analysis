"""Apply the v2.11 changes to the Turkish team guide, README.md, AGENTS.md and CLAUDE.md. Numbers come from the
result files. Usage: docs_patch_tr.py "TEST COUNTS SENTENCE (English, for CLAUDE.md)" """
import json
import os
import sys
from pathlib import Path

R = Path(os.environ.get('SC_DIR', '/home/claude/sc'))
r11 = json.loads((R / 'possession-v211-results.json').read_text())
fu = json.loads((R / 'possession-v211-followup.json').read_text())
assert r11['selected'] == 'possession-v2.11'
S = r11['summary']
F = fu['full_size_rehearsal']
K5 = json.loads((R / 'possession-label-order-correction.json').read_text())['corrected']
k3 = K5['full_size_rehearsal_of_K003']
k3s = lambda b: k3[f'bundle {b}']['delivered file of the K003 chain (possession-v2.9)']['against_file_order_labels']['spell_f1_mean']
sl = K5['slot_and_duplicate_diagnostic']['rerun_python_3_13_file_order_labels']
slot_single = max(abs(x) for v in sl['difference_to_base_per_match'].values() for x in v.values())
slot_mean = max(abs(x) for x in sl['difference_to_base'].values())
rd = K5['goalkeeper_diagnostic']['rerun_python_3_13_file_order_labels']['difference_to_base']
tr = lambda x, nd=3: f'{x:.{nd}f}'.replace('.', ',')
en = lambda x, nd=3: f'{x:.{nd}f}'
sp = lambda k, s: S[k]['spell_f1'][s]


def patch(path, pairs):
    p = R / path
    s = p.read_text(encoding='utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:80], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, encoding='utf-8')


# ------------------------------------------------------------------ docs/SAHIPLIK_V2_TR.md
patch('docs/SAHIPLIK_V2_TR.md', [
    ('''> **Güncel durum (11 Kasım 2026):** teslim sistemi **v2.9**'dur (`python -m possession.run29`).
> v2.9, aşağıda anlatılan v2.5 sisteminin üstüne iki ek getirir; bunlar belgenin sonundaki
> "Güncelleme: v2.9" bölümündedir.''',
     '''> **Güncel durum (11 Kasım 2026, öğleden sonra):** teslim sistemi **v2.11**'dir
> (`python -m possession.run211`). v2.11, aşağıda anlatılan v2.5 sisteminin üstüne üç ek getirir;
> bunlar belgenin sonundaki "Güncelleme: v2.9" ve "Güncelleme: v2.11" bölümlerindedir. v2.9 bir alt
> teknik basamak olarak duruyor.'''),
    ('''Bu yapılandırmanın basamakları `possession-v2.9g` → v2.5b → v2.5b yalnız taktik kameradır.''',
     '''Bu yapılandırmanın basamakları `possession-v2.11g` → `possession-v2.9g` → v2.5b → v2.5b yalnız taktik
kameradır.'''),
    ('''  dosyalara yazılır ve dondurulmuş sürümün giriş noktası (`possession.run29`) bu dosyalarda''',
     '''  dosyalara yazılır ve dondurulmuş sürümün giriş noktası (`possession.run211`) bu dosyalarda'''),
    ('''- **Neden:** v2.9'un doğrulama maçları seçim sırasında defalarca kullanıldı.''',
     '''- **Neden:** sürümün doğrulama maçları seçim sırasında defalarca kullanıldı.'''),
    ('''.\\.venv-possession\\Scripts\\python.exe -m possession.run29 --data-dir <veri kökü> --out <yeni klasör> --tactical-clock <saat>\\tactical --broadcast-clock <saat>\\broadcast''',
     '''.\\.venv-possession\\Scripts\\python.exe -m possession.run211 --data-dir <veri kökü> --out <yeni klasör> --tactical-clock <saat>\\tactical --broadcast-clock <saat>\\broadcast'''),
    ('''başlatıcılar (`SAHIPLIK-V2-KURULUM.cmd`, `SAAT-OKU.cmd`, `SAHIPLIK-V29-URET.cmd`) duruyor, ama''',
     '''başlatıcılar (`SAHIPLIK-V2-KURULUM.cmd`, `SAAT-OKU.cmd`, `SAHIPLIK-V211-URET.cmd`) duruyor, ama'''),
    ('''| PLATFORM | bu bilgisayar, sentetik bir pakette Linux'ta kaydedilen baytların aynısını üretiyor mu | FARKLI olsa da dosya üretilir; fark belgeye yazılır |''',
     '''| PLATFORM | bu bilgisayar, sentetik paketlerde Linux'ta kaydedilen baytların aynısını üretiyor mu (yedi varyant: beşi v2.9 yolu, ikisi kaleci denetimi) | FARKLI olsa da dosya üretilir; fark belgeye yazılır. Yanında farklı çıkan varyantın adı yazar; iletin |'''),
])
p = R / 'docs/SAHIPLIK_V2_TR.md'
s = p.read_text(encoding='utf-8').rstrip('\n')
s += f'''

## Güncelleme, 11 Kasım 2026 (öğleden sonra): v2.11 — kaleci takım denetimi

Çalıştırma değişmedi: `TESLIM-HAZIRLA.cmd` (içeride artık `python -m possession.run211`). v2.11 teknik
bir hata verirse zincir kendiliğinden bir alt basamağı, v2.9'u çalıştırır ve bunu `URETIM` satırında
yazar. Ayrıntılı kayıt: `docs/DENEY_KAYDI_TR.md` K004.

**Sorun neydi?** Takip dosyası her iz için yalnız konum ve takım veriyor. Takımı izleyici belirliyor;
kaleci ise takım arkadaşlarından farklı forma giyer. Kalecinin izi yanlış takımın kimliğini taşırsa
modellerimiz kalede bir rakip görür. İki kaleci birden yanlışsa daha kötüsü olur: özellikler hangi
takımın hangi kaleye saldırdığını her takımın *ortalama* konumundan çıkarıyor ve iki kaleci bu
ortalamayı ters çevirmeye yetiyor. Dış maçlarda ölçtük: spellF1 {tr(sp('none', 'v2_9'))} yerine {tr(sp('gk_both', 'v2_9'))}.
Bozma benzetimimiz bu hatayı içermiyordu (yalnız 1-6 saniyelik takım değişimleri vardı).

**Denetim ne yapıyor?** Özellikler hesaplanmadan önce kaleci izlerini yalnız konumdan bulur: oyun öbür
yarı sahadayken kaleye en yakın olan *ve* herkesin en az 8 m gerisinde duran iz kalecidir. Böyle bir iz
o kaleyi savunmayan takımın kimliğini taşıyorsa savunan takıma aktarılır, ama yalnız iki durumda:

1. o kalenin o yarıdaki kaleci kanıtının çoğu yanlış kimlik altındaysa (kaleci bütün yarı boyunca yanlış
   etiketlenmiş), ya da
2. iz, zaman ve yer olarak bir kaleci izinin devamıysa (kaleci bir süreliğine yanlış etiketlenmiş).

Kimlikler doğruysa hiçbir şey değişmez ve çıktı v2.9'un çıktısıdır. Gürültü kapısı, yayın eşlemesi ve
0,50 m kapısı kimlikleri verildiği gibi kullanmaya devam eder; düzeltilmiş kimlikleri yalnız modeller
görür.

**Neden iki sürüm (v2.10 ve v2.11)?** İlk kural (v2.10) önceden kaydedilen dört eşiği geçti. Dondurmadan
önce neyi taşıdığına baktık: 80 parçanın 77'si gerçekten kaleciydi, 3'ü forvetti (biri, rakip kaleden
13 m uzakta maçın son 2,5 dakikasında hareketsiz duran bir oyuncu). Puan değişmemişti, ama neden
önemliydi: "kaleye en yakın oyuncu" kanıtı, kaleci izlenmiyorken yanlış kişiyi gösterir. Oyunu izleyen
bir kamera uzak kaleciyi hiç göstermeyebilir. Bu durumu benzettiğimizde v2.10 eğitim maçlarında maç
başına 1.700-8.400 saha oyuncusu konumunu yanlış takıma aktardı. Bu yüzden v2.10 yayımlanmadı; kural
yukarıdaki iki koşulla sıkılaştırıldı (v2.11) ve bu durum doğrulamaya iki ek eşik olarak eklendi.
*Öğrenilecek şey:* eşiklerin geçmesi, eşiklerin sormadığı sorulara yanıt değildir; bir düzeltmenin neyi
değiştirdiğine tek tek bakmak, ortalama puanın göstermediğini gösterir.

**Sonuç** (8 yeni bozuk kopya, dış maçlar; yarışma puanı değildir; altı eşik de geçti):

| durum | denetimsiz (v2.9) | denetimli (v2.11) |
|---|---|---|
| kimlikler doğru | {tr(sp('none', 'v2_9'))} | {tr(sp('none', 'v2_11'))} |
| iki kaleci bütün maç yanlış kimlikle | {tr(sp('gk_both', 'v2_9'))} | {tr(sp('gk_both', 'v2_11'))} |
| bir kaleci bütün maç yanlış kimlikle | {tr(sp('gk_one', 'v2_9'))} | {tr(sp('gk_one', 'v2_11'))} |
| iki kaleci maçın %30'unda yanlış kimlikle | {tr(sp('gk_part', 'v2_9'))} | {tr(sp('gk_part', 'v2_11'))} |
| uzak kaleciyi çoğu zaman göstermeyen kamera (±42 m), kimlikler doğru | {tr(sp('view42_none', 'v2_9'))} | {tr(sp('view42_none', 'v2_11'))} |
| daha dar kamera (±35 m), kimlikler doğru | {tr(sp('view35_none', 'v2_9'))} | {tr(sp('view35_none', 'v2_11'))} |
| ±42 m kamera, iki kaleci yanlış (eşik değil) | {tr(sp('view42_gk_both', 'v2_9'))} | {tr(sp('view42_gk_both', 'v2_11'))} |

Tam boy provada (sentetik paket, kaleci izleri öbür takımın kimliğiyle yazılmış) teslim dosyası denetimle
{tr(F['bundle_G1_v2_11']['spell_f1'])}, denetimsiz {tr(F['bundle_G1_v2_9']['spell_f1'])} aldı; kimlikleri doğru olan pakette {tr(F['bundle_A_chain_v2_11']['spell_f1'])} (v2.9 ile {tr(F['bundle_A_v2_9_chain_of_K003']['spell_f1'])}).
Bu prova puanları K005'te düzeltilen etiketlere göredir: K003'te A paketi için yazılan 0,715, duran top
aralıklarının yarısını yitirmiş etiketlerle hesaplanmıştı (`docs/DENEY_KAYDI_TR.md` K005).

**Bilmediğimiz.** Sağlanan takip verisinde böyle bir hata var mı, bakmadık ve bakmayacağız. Hatalar ve
kamera, bizim yaptığımız benzetimlerdir. Uzak kaleci çoğunlukla görüntü dışındaysa (benzetimde ±35 m)
denetim hiçbir şeyi düzeltmez; zarar da vermez. Denetimin sağlanan maçta bir şey taşıyıp taşımadığı
yalnız sizde kalan belge kopyasının Ek R bölümünde ve `run.json` içinde yazar; bunları asistana
iletmeyin.
'''
p.write_text(s + '\n', encoding='utf-8')

# ------------------------------------------------------------------ README.md
patch('README.md', [
    ('## Submission system: possession v2.9', '## Submission system: possession v2.11'),
    ('''Release `possession-v2.9`, entry point `python -m possession.run29`, manifest
`possession-v29-release.json`. The release and its technical fall-backs are named in
`possession-release.json`.''', '''Release `possession-v2.11`, entry point `python -m possession.run211`, manifest
`possession-v211-release.json`. The release and its technical fall-backs (the next one is
`possession-v2.9`) are named in `possession-release.json`.'''),
    ('python -m possession.run29 --data-dir <bundle root> --out <new folder> --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast',
     'python -m possession.run211 --data-dir <bundle root> --out <new folder> --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast'),
    ('''Reserve: `possession-release-graded-windows.json` names `possession.run29g`, the same system without''',
     '''Reserve: `possession-release-graded-windows.json` names `possession.run211g`, the same system without'''),
    ('''- **Registration (v2.9):** before that gate the broadcast ball is corrected by the calibration error
  measured on players both cameras see (`possession/register.py`).''',
     '''- **Registration (v2.9):** before that gate the broadcast ball is corrected by the calibration error
  measured on players both cameras see (`possession/register.py`).
- **Goalkeeper team check (v2.11):** goalkeeper track pieces that carry the other team's id are moved
  to the team that defends their goal before the features are computed (`possession/keeper2.py`);
  with correct ids nothing changes.'''),
    ('''broadcast 0.653 -> 0.681 and with an accurate one 0.686 -> 0.684. Tested and not selected under
gates written down beforehand: Smart Tagging evidence (v3), ungated broadcast fill (v4), wider noise
training (v2.2), v2.3 alone, switch hazard (v2.6), gap features (v2.7), Metrica training (v2.8).''',
     f'''broadcast 0.653 -> 0.681 and with an accurate one 0.686 -> 0.684; goalkeeper check {en(sp('none', 'v2_9'))} -> {en(sp('none', 'v2_11'))}
with correct team ids, {en(sp('gk_both', 'v2_9'))} -> {en(sp('gk_both', 'v2_11'))} with both goalkeepers under the other team's id (simulated). Tested
and not selected under gates written down beforehand: Smart Tagging evidence (v3), ungated
broadcast fill (v4), wider noise training (v2.2), v2.3 alone, switch hazard (v2.6), gap features
(v2.7), Metrica training (v2.8). The first goalkeeper check (v2.10) passed its gates and was replaced
before release (log entry K004).'''),
])

# ------------------------------------------------------------------ AGENTS.md
patch('AGENTS.md', [
    ('''- Possession (`possession/`): the submission system is `possession-v2.9`, entry point
  `python -m possession.run29`, release manifest `possession-v29-release.json`; the release and its
  technical fall-backs are named in `possession-release.json`. v2.9 = frozen v2.1 core + noise gate
  with the v2.3 path (v2.4) + gated broadcast ball fill with clock-anchored alignment (v2.5b) +
  second-half kick-off frame published in the organisers' FAQ (v2.5c) + broadcast ball registered
  through players seen by both cameras (`register.py`). It follows the rules above: external-only
  training/selection (`possession-v2-plan.json` ... `possession-v29-amendment-plan.json`), frozen''',
     '''- Possession (`possession/`): the submission system is `possession-v2.11`, entry point
  `python -m possession.run211`, release manifest `possession-v211-release.json`; the release and its
  technical fall-backs (the next one is `possession-v2.9`, `possession.run29`) are named in
  `possession-release.json`. v2.11 = frozen v2.1 core + noise gate with the v2.3 path (v2.4) + gated
  broadcast ball fill with clock-anchored alignment (v2.5b) + second-half kick-off frame published in
  the organisers' FAQ (v2.5c) + broadcast ball registered through players seen by both cameras
  (`register.py`, v2.9) + goalkeeper team check before the features (`keeper2.py`). It follows the
  rules above: external-only
  training/selection (`possession-v2-plan.json` ... `possession-v211-plan.json`), frozen'''),
    ('''- `possession.run29g` (`possession-release-graded-windows.json`) is a reserve entry point without''',
     '''- `possession/keeper.py` is the first version of the goalkeeper check (v2.10). It passed its
  registered gates and was not released (it moved outfield players when the far goalkeeper was not
  tracked; log entry K004). Keep the file, its plan and its results as they are; do not use it.
  Whether the provided tracking has goalkeeper id errors is not to be looked at; `run.json` and
  Appendix R on the team's computer record whether the check moved anything.
- Metrica proxy labels (`experiments/possession_v2/metrica_labels.py`) must be computed with the stable
  sort that file now uses (log entry K005: with the default sort the labels depended on the pandas /
  numpy build, and three reporting-only records had to be recomputed). Any record that scores against
  external labels states the Python, pandas and numpy versions it ran under.
- `possession.run211g` (`possession-release-graded-windows.json`) is a reserve entry point without'''),
])

# ------------------------------------------------------------------ CLAUDE.md
patch('CLAUDE.md', [
    ('''  SHA-256 in `possession-v29-release.json` (and `-v25-`, `-v25c-`, reserve `-v29g-`);''',
     '''  SHA-256 in `possession-v211-release.json` (and `-v29-`, `-v25-`, `-v25c-`, reserves `-v211g-`, `-v29g-`);'''),
    ('''python -m possession.run29 --data-dir <bundle> --out <new dir> [--tactical-clock <dir> --broadcast-clock <dir>]   # USER ONLY, local''',
     '''python -m possession.run211 --data-dir <bundle> --out <new dir> [--tactical-clock <dir> --broadcast-clock <dir>]   # USER ONLY, local'''),
    ('''## Status snapshot (11 Nov 2026 midday — verify before relying on it)
''', f'''## Status snapshot (11 Nov 2026 afternoon — verify before relying on it)

- **Submission system: `possession-v2.11`** (`python -m possession.run211`, manifest
  `possession-v211-release.json`) = v2.9 + goalkeeper team check (`possession/keeper2.py`) applied to the
  tracking the models see. Ladder in `possession-release.json`: v2.11 -> v2.9 -> v2.5c -> v2.5c tactical only.
  Reserve without the published kick-off frame: `possession.run211g` (`possession-v211g-release.json`;
  ladder v2.11g -> v2.9g -> v2.5b -> v2.5b tactical). No frozen v2.9 file changed. Log entry K004.
- **Why:** team ids come from the tracker and goalkeepers wear another kit. Diagnostic
  (`experiments/possession_v2/stress_roles.py`, reporting only; re-run numbers of K005): one goalkeeper
  under the other id for the whole match {rd['gk_one']:+.3f} spellF1, both {rd['gk_both']:+.3f} (the mean-based
  `features.attack_dirs` inverts), 30% of the time {rd['gk_part']:+.3f}, a referee under a team id {min(rd['ref_home'], rd['ref_mixed']):+.3f} at
  worst (not handled).
- **v2.10 (`possession/keeper.py`) passed its four registered gates and was NOT released**
  (`possession-v210-plan.json`, `-results.json`). A reporting analysis of what it moved found 3 outfield
  pieces among 80; with a simulated camera window that hides the far goalkeeper it moved 1,700-8,400
  outfield positions per training match. Keep the file and records; do not use it.
- **v2.11 rule (`keeper2.py`):** evidence = far frames in which a piece is nearest to a goal by at least
  8 m; a piece under the other id is moved only if that goal's evidence in the half is mostly (>= 50%,
  >= 2,500 frames) under the other id, or if it continues a goalkeeper piece. Validation
  (`possession-v211-plan.json`, `-results.json`; 8 new copies, six gates, all passed): ids as corrupted
  {en(sp('none', 'v2_9'), 4)} -> {en(sp('none', 'v2_11'), 4)}; both goalkeepers wrong {en(sp('gk_both', 'v2_9'), 4)} -> {en(sp('gk_both', 'v2_11'), 4)}; one {en(sp('gk_one', 'v2_9'), 4)} -> {en(sp('gk_one', 'v2_11'), 4)}; 30% of the time
  {en(sp('gk_part', 'v2_9'), 4)} -> {en(sp('gk_part', 'v2_11'), 4)}; camera window 42 m / 35 m with correct ids {en(sp('view42_none', 'v2_9'), 4)} -> {en(sp('view42_none', 'v2_11'), 4)} / {en(sp('view35_none', 'v2_9'), 4)} -> {en(sp('view35_none', 'v2_11'), 4)};
  window 42 m with both wrong {en(sp('view42_gk_both', 'v2_9'), 4)} -> {en(sp('view42_gk_both', 'v2_11'), 4)} (reported, not a gate). Simulated errors and camera; whether
  the provided tracking has any of this is unknown and must not be looked at. Limit: with the far
  goalkeeper mostly out of view (35 m window) nothing is corrected.
- **Follow-up** (`possession-v211-followup.json`): reserved Metrica game 3 rows, development counts,
  full-size rehearsals: chain on bundle A with v2.11 {en(F['bundle_A_chain_v2_11']['spell_f1'])} (v2.9: {en(F['bundle_A_v2_9_chain_of_K003']['spell_f1'])}); bundle with the
  goalkeepers' tracks under the other id: {en(F['bundle_G1_v2_11']['spell_f1'])} with the check, {en(F['bundle_G1_v2_9']['spell_f1'])} without; one v2.11 generation
  {F['bundle_A_v2_11']['seconds']} s, peak {F['bundle_A_v2_11']['peak_memory_gb']} GB.
- **Records correction K005** (`possession-label-order-correction.json`): `metrica_labels.labels_from_events`
  sorted tied events unstably. In the Python 3.10 environment the Metrica proxy labels lost about half of
  their dead-ball intervals; in the experiment environment (Python 3.13 / pandas 3.0.5) they were in file
  order. All selections, gates, validations and reserved tests ran in the experiment environment (stored
  possession counts match the file-order labels only). Affected and recomputed: K003 rehearsal scores
  (bundle A {en(k3s('A'))}, B {en(k3s('B'))}; first reported 0.715 / 0.686), K003 slot / duplicate diagnostic (now at most
  {slot_single:.4f} on a copy, {slot_mean:.4f} on average), the goalkeeper diagnostic. The script now uses a stable
  sort. **Rule: score against Metrica proxy labels only with the current script, and record the Python /
  pandas / numpy versions of any such run.** `possession-rehearsal-results.json` and
  `possession-v210-plan.json` keep the first numbers.
- **Chain changes:** PLATFORM compares seven synthetic variants (five v2.9 runs with unchanged recorded
  hashes + two `run211` runs on bundles with exchanged goalkeeper ids; a differing goalkeeper-bundle
  input gives `BELIRSIZ (kaleci varyantlari...)`); Appendix R has a "Goalkeeper team correction" row
  (moved / not moved, no counts). `tools/possession_final_test.py` now calls the entry point named in
  the plan; **the final-test plan was re-registered for v2.11** (history kept in the file; J03WMX still
  untouched). After any further edit of the tool or of `epts_export.py`, re-register again with
  `experiments/possession_v2/register_final_test_v211.py`-style script and say so in the log.
- {sys.argv[1]}
- Still pending (user): optional workflow line -> `GIT-YUKLE-V2.cmd` -> Actions -> `TESLIM-HAZIRLA.cmd`
  -> paste the `[..]` lines and `SONUC` -> Google Form. Optional, any day before 17 Nov: `SON-TEST.cmd`.
  Windows has never run any of this. No answer from the organisers to the kick-off question as of the
  last check (see the log).

## Earlier status (11 Nov 2026 midday; its rehearsal scores and slot-diagnostic numbers were recomputed in K005)
'''),
])
print('Turkish guide, README, AGENTS and CLAUDE patched')
