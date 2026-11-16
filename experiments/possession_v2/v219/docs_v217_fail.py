"""Documents for the case that the v2.17 candidate FAILED its registered gates: possession-v2.16 stays the release; the
attempt is recorded as tried and not used. Every replacement must match exactly once.
Usage: python3 docs_v217_fail.py REPO_DIR"""
import json, shutil, sys, hashlib
from pathlib import Path
import numpy as np

REPO = Path(sys.argv[1]).resolve()
V = Path('/home/claude/work/v219')
res = json.loads((REPO / 'possession-v217-results.json').read_text())
plan = json.loads((REPO / 'possession-v217-plan.json').read_text())
assert not res['selected']
S = res['summary']; G = res['gates']; SEEN = plan['seen_on_external_data_before_registration']
T, FG, FM, S2 = S['tactical'], S['fill_good'], S['fill_medium'], S['tactical_sim2']
sg = lambda v: f'{v:+.4f}'
f4 = lambda v: f'{v:.4f}'
tr = lambda v, n=4: f'{v:.{n}f}'.replace('.', ',')
ts = lambda v, n=4: ('+' if v >= 0 else '−') + f'{abs(v):.{n}f}'.replace('.', ',')
VAL = {'G1 gain': lambda g: sg(g['value']), 'G2 gain on provider flags': lambda g: sg(g['value']), 'G3 no harm on event proxies': lambda g: sg(g['value']),
       'G4 no bad copy': lambda g: sg(g['value']) + ' on ' + g['copy'], 'G5 macroF1': lambda g: sg(g['value']),
       'G6 broadcast fill': lambda g: sg(g['fill_good']) + ' / ' + sg(g['fill_medium']), 'G7 other simulator': lambda g: sg(g['value'])}
NAME_EN = {'G1 gain': 'the mean gain (at least +0.008)', 'G2 gain on provider flags': 'the mean gain on the DFL copies (at least +0.008)',
           'G3 no harm on event proxies': 'no harm on the Metrica copies (at least -0.002)', 'G4 no bad copy': 'no copy below -0.010',
           'G5 macroF1': 'macroF1 (at least -0.003)', 'G6 broadcast fill': 'no loss with the simulated second camera, accurate / medium stream (each at least 0)',
           'G7 other simulator': 'no loss on the copies of the other simulator (at least 0)'}
NAME_TR = {'G1 gain': 'ortalama kazanç (en az +0,008)', 'G2 gain on provider flags': 'DFL kopyalarında ortalama kazanç (en az +0,008)',
           'G3 no harm on event proxies': 'Metrica kopyalarında zarar yok (en az −0,002)', 'G4 no bad copy': 'hiçbir kopya −0,010\'dan kötü olmasın',
           'G5 macroF1': 'macroF1 (en az −0,003)', 'G6 broadcast fill': 'benzetilmiş ikinci kamerayla kayıp yok, iyi / orta akış (her biri en az 0)',
           'G7 other simulator': 'öteki benzeticinin kopyalarında kayıp yok (en az 0)'}
failed = [k for k, g in G.items() if not g['passed']]
passed = [k for k, g in G.items() if g['passed']]
assert failed
fail_en = '; '.join(f"{NAME_EN[k]}: {VAL[k](G[k])}" for k in failed)
fail_tr = '; '.join(f"{NAME_TR[k]}: {VAL[k](G[k]).replace('.', ',').replace('-', '−').replace(' on ', ' — kopya ')}" for k in failed)
WORD = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 7: 'All seven'}[len(failed)]
WORD_TR = {1: 'biri', 2: 'ikisi', 3: 'üçü', 4: 'dördü', 5: 'beşi', 6: 'altısı', 7: 'yedisi'}[len(failed)]
assert failed == ['G4 no bad copy'], 'the texts below are written for a failure of G4 alone'
bad = next(r for r in res['rows'] if r['condition'] == 'tactical' and r['copy'] == G['G4 no bad copy']['copy'])
bad_rel = bad['v2_16']['spell_f1'] - bad['v2_11']['spell_f1']; bad_cand = bad['candidate']['spell_f1'] - bad['v2_11']['spell_f1']
allg_en = ', '.join(f"{k.split()[0]} {VAL[k](G[k])}{'' if G[k]['passed'] else ' (FAILED)'}" for k in G)


def edit(rel, pairs, crlf=False):
    p = REPO / rel
    s = p.read_bytes().decode('utf-8')
    if crlf:
        s = s.replace('\r\n', '\n')
    for old, new in pairs:
        assert s.count(old) == 1, (rel, s.count(old), old[:100])
        s = s.replace(old, new)
    if crlf:
        s = s.replace('\n', '\r\n')
    p.write_bytes(s.encode('utf-8'))


# ---------------------------------------------------------------- archive
A = REPO / 'experiments' / 'possession_v2' / 'v219'
(A / 'port').mkdir(parents=True, exist_ok=True)
for f in ('exp_v217.py', 'assemble_v217.py', 'register_v217.py', 'freeze_v217.py', 'xenv2.py', 'docs_v217_fail.py', 'k019_body.md'):
    shutil.copyfile(V / f, A / f)
for f in ('make_run217.py', 'apply_v217.py', 'quick217.py', 'test_possession_v217.py'):
    shutil.copyfile(V / 'port' / f, A / 'port' / (f if f != 'test_possession_v217.py' else 'test_possession_v217.py.txt'))
if (A / 'author_74bedbf').exists():
    shutil.rmtree(A / 'author_74bedbf')
shutil.copytree(V / 'author_74bedbf', A / 'author_74bedbf')
lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(A / 'author_74bedbf').as_posix()}" for p in sorted((A / 'author_74bedbf').rglob('*')) if p.is_file()]
(A / 'author_74bedbf' / 'SHA256SUMS.txt').write_text(
    '# Byte copies of files of repository branch mtah-possession, commit 74bedbf (author: the team member who wrote the network).\n'
    '# The sixteen weight files of the candidate are on that branch only; they are not loaded by any release.\n' + '\n'.join(lines) + '\n', encoding='utf-8')

# ---------------------------------------------------------------- TECHNICAL_DOCUMENT.md
edit('TECHNICAL_DOCUMENT.md', [
    ("""`possession-v214-results.json`). The third and last attempt lowered the network's weight to 0.2 by a
rule written down while the second was still running, was registered before any new result, passed
the same seven gates on 16 further new copies and is step 9 (`possession-v215-plan.json`,
`possession-v215-results.json`). Giving the broadcast
""",
     f"""`possession-v214-results.json`). The third attempt lowered the network's weight to 0.2 by a
rule written down while the second was still running, was registered before any new result, passed
the same seven gates on 16 further new copies and is step 9 (`possession-v215-plan.json`,
`possession-v215-results.json`). Its plan and our documents called it the last attempt and said
that no further candidate with the second model would be registered before the deadline. We went
back on that statement once. On 16 November the team member who wrote the network pushed eight
newly trained copies of it (four of them reading 71 quantities instead of 37) together with his
own development numbers and the weight he proposed for them, 0.4. The team lead decided to have
them validated, and a fourth validation was registered before any of its results
(`possession-v217-plan.json`): the same seven gates and thresholds, now against the released
system instead of the trees alone, on 16 new copies, run by the process that had not built the
candidate. With the tactical camera the eight
copies scored {f4(T['candidate_mean'])} against {f4(T['v2_16_mean'])} for the release ({sg(T['mean_diff'])}; better on {T['better']} copies, worse on {T['worse']}),
and with the simulated second camera they were {sg(FG['mean_diff'])} (accurate stream) and {sg(FM['mean_diff'])} (medium stream)
higher. Six gates passed. The gate that allows no copy more than 0.010 below the release failed:
one copy was {abs(G['G4 no bad copy']['value']):.4f} lower. That is the gate the second attempt had failed, so the eight copies
were not released either (`possession-v217-results.json`) and step 9 is unchanged. Giving the broadcast
"""),
    ("""  the second camera on four development copies before it was validated on new ones, and it was
  the fourth idea examined on these matches on the same day.
""",
     """  the second camera on four development copies before it was validated on new ones, and it was
  the fourth idea examined on these matches on the same day. On the team's computer the release
  with this step wrote the same bytes as the release without it (status line of the delivery
  tool, 16 November): on the provided match the step changed no label. Either it was not applied
  (the accuracy gate was closed), or it found no player to add, or the players it added changed
  no decision; the row "Players added from the broadcast camera" of Appendix R says which.
"""),
])

# ---------------------------------------------------------------- TECHNICAL_DOCUMENT_V2.md
addendum = f"""
> **Sixth addendum, 16 November 2026: a fourth attempt with the second model, not released.** The submitted entry point
> stays `python -m possession.run216`; nothing of the release changed.
>
> 1. **What happened.** The fourth addendum calls v2.15 the third and last attempt with the second model, and the
>    fifth repeats that no further candidate with it is registered. On 16 November, between 00:49 and 05:58, the team
>    member who wrote the network pushed to his branch (`mtah-possession`, commit `74bedbf`) eight newly trained
>    members, an inference that gives each member its own features, and his own numbers: a development grid on the
>    40 copies of the v2.14 and v2.15 validations and one check on other seeds. This process had not asked for them
>    and saw them at about 06:10 while checking the repository. It told the team lead that a further registration
>    goes back on the written statement and that the choice was his, and wrote that in its view the attempt was
>    worth making if winning was the priority. The team lead chose at 12:24 to make one more attempt. This was a
>    departure from what we had written, made after the candidate's development numbers were known; the earlier
>    records are unchanged.
> 2. **The candidate** (fixed by its author before his own check; nothing chosen here). Members `d6_a_s0-3` (the 37
>    features of the released members) and `d6_f_s0-3` (71 features: the 37, the three players of each team closest
>    to the ball with distance, relative position, speed and closing speed, and four ball-kinematics columns);
>    arithmetic pool with weight 0.4 for the network; everything else as v2.16. Training, as he states it: six DFL
>    matches, per match 16 copies of the team's simulator and 8 of his own, packed and goalkeeper-corrected with the
>    team's code; PyTorch; external matches only. The process that validated the files did not observe the training.
> 3. **Validation** (`possession-v217-plan.json`, registered {plan['registered_at'][11:16]} before the first validation row;
>    `possession-v217-results.json`). Run by this process with the candidate's NumPy inference. Arms: v2.16 (three
>    members, weight 0.2) and the candidate, on the same copy, model input, tree probabilities, pool and decoder.
>    Before the registration the script reproduced three rows of earlier validations exactly and the author's values
>    of the candidate on two of them. 16 new copies, tactical camera: {f4(T['v2_16_mean'])} -> {f4(T['candidate_mean'])} ({sg(T['mean_diff'])}; DFL {sg(T['dfl'])},
>    Metrica {sg(T['metrica'])}; {T['better']} better, {T['worse']} worse, {T['equal']} equal, single copies {sg(T['min'])} to {sg(T['max'])}; macroF1 {sg(T['mean_diff_macro_f1'])}).
>    With the simulated second camera and the added players of v2.16 (8 copies each): accurate stream {sg(FG['mean_diff'])}
>    (single copies {sg(FG['min'])} to {sg(FG['max'])}), medium stream {sg(FM['mean_diff'])} ({sg(FM['min'])} to {sg(FM['max'])}; DFL {sg(FM['dfl'])}, Metrica {sg(FM['metrica'])}).
>    Copies of the other simulator (4): {sg(S2['mean_diff'])}. Against the trees alone the candidate is at {sg(T['candidate_minus_v2_11'])} and v2.16 at
>    {sg(T['v2_16_minus_v2_11'])} on the 16 tactical copies. Gates, unchanged, against the release: G1 {sg(G['G1 gain']['value'])} (at least +0.008),
>    G2 {sg(G['G2 gain on provider flags']['value'])} (+0.008), G3 {sg(G['G3 no harm on event proxies']['value'])} (-0.002), G4 worst copy {sg(G['G4 no bad copy']['value'])} (-0.010; FAILED), G5 {sg(G['G5 macroF1']['value'])} (-0.003),
>    G6 {sg(G['G6 broadcast fill']['fill_good'])} and {sg(G['G6 broadcast fill']['fill_medium'])} (0), G7 {sg(G['G7 other simulator']['value'])} (0).
> 4. **Decision.** One gate failed, the one on single copies (G4): on copy {bad['copy'].replace('|', ', seed ')} the release is
>    {sg(bad_rel)} against the trees and the candidate {sg(bad_cand)}. It is the picture of v2.14 (fourth addendum, item 4): a gain
>    on average and on {T['better']} of 16 copies, and one copy clearly lower. The candidate is recorded as tried and not used, and
>    v2.16 stays the release. The plan says that, whatever the outcome, no further candidate with the second model is
>    registered before the deadline. The validation scripts, the generated entry point that was not released and byte
>    copies of the author's account and scripts are under `experiments/possession_v2/v219/`; his weight files are on
>    his branch only.
"""
edit('TECHNICAL_DOCUMENT_V2.md', [
    ("Submission file regenerated with `python -m possession.run216` (see the five addenda and Reproduction).",
     "Submission file regenerated with `python -m possession.run216` (see the six addenda and Reproduction)."),
    (""">    matches. It does not touch the statement of the fourth addendum that no further candidate with the second model
>    is registered: the second model is the same in both arms.
""",
     """>    matches. It does not touch the statement of the fourth addendum that no further candidate with the second model
>    is registered: the second model is the same in both arms.
""" + addendum.rstrip('\n') + '\n'),
])

# ---------------------------------------------------------------- AGENTS.md, DATA_SOURCES.md, README.md
edit('AGENTS.md', [
    ("""failed). Keep the files and records. v2.15 (log entry K013), the release, is the third and last
  attempt; it changes none of the earlier records, and its plan says that no further candidate with
  the second model is registered before the deadline.
""",
     f"""failed). Keep the files and records. v2.15 (log entry K013), the second model of the release, was
  the third attempt; its plan and these documents called it the last and said that no further
  candidate with the second model would be registered before the deadline. That statement was set
  aside once, by a decision of the team lead on 16 Nov after a team member had pushed eight new
  network members with his development numbers: a fourth registered attempt (the v2.17 candidate,
  log entry K020; `possession-v217-plan.json`, `-results.json`; scripts under
  `experiments/possession_v2/v219/`) failed the gate on single copies (better on {T['better']} of 16 new copies,
  one copy {abs(G['G4 no bad copy']['value']):.3f} lower) and is not part of any release.
  Its plan says that whatever the outcome no further candidate with the second model is registered
  before the deadline. Do not register one. None of the earlier records was changed.
"""),
])
edit('DATA_SOURCES.md', [
    ("""**Second model of the release (v2.15 and v2.16).** Design, features and NumPy inference: the same team member
""",
     """**A team member's eight network members (16 Nov), validated and not selected.** Trained by the team member who wrote
the network, on his own computer, on the six DFL training matches below and, by his statement, on nothing else (his
account and scripts: byte copies under `experiments/possession_v2/v219/author_74bedbf/`). They were pooled with the
release's probabilities in a registered validation and that combination was not selected (log entry K020,
`possession-v217-plan.json`, `possession-v217-results.json`). Those weights are not loaded by the release and are
not in this branch.

**Second model of the release (v2.15 and v2.16).** Design, features and NumPy inference: the same team member
"""),
])
edit('README.md', [
    ("""better on 15 of 16 copies but one copy clearly worse; the third way, with a smaller weight, is part of
the release). Explored""",
     f"""better on 15 of 16 copies but one copy clearly worse; the third way, with a smaller weight, is part of
the release) and, as a fourth attempt made although the third had been called the last, a team
member's eight newly trained network members with weight 0.4 (log entry K020: {sg(T['mean_diff'])} and better on
{T['better']} of 16 copies, but one copy clearly worse, the same gate as v2.14). Explored"""),
])

# ---------------------------------------------------------------- docs/DENEY_KAYDI_TR.md
def line(cond, label):
    s = S[cond]
    return (f"| {label} | {s['copies']} | {tr(s['v2_16_mean'])} | {tr(s['candidate_mean'])} | {ts(s['mean_diff'])} | {ts(s['dfl'])} / {ts(s['metrica'])} | "
            f"{s['better']} / {s['worse']} / {s['equal']} | {ts(s['min'])} |")
k019 = (V / 'k019_body.md').read_text(encoding='utf-8').rstrip('\n')
gate_tr = ', '.join(f"{k.split()[0]} {VAL[k](G[k]).replace('.', ',').replace('-', '−').replace(' on ', ' — ')}{'' if G[k]['passed'] else ' (**geçmedi**)'}" for k in G)
k020 = f"""## K020 — ikinci modelle dördüncü deneme: takım arkadaşının sekiz ağı, ağırlık 0,4 (v2.17 adayı): kayıtlı kapılar geçmedi, sürüm değişmedi, 16 Kasım 2026

**Ne.** Aday: v2.16, ikinci model değişmiş hâliyle: üç ağ ve 0,2 ağırlık yerine sekiz ağ ve 0,4 ağırlık. Dört ağ sürümdeki 37
özelliği okur; dördü 71 özelliği (aynı 37, sonra her takımın topa en yakın üç oyuncusu ve topun kendi hareketinden dört sütun).
Ağlar ve çıkarım, ağı yazan takım arkadaşının `mtah-possession` dalındaki commit `74bedbf` dosyalarıdır.

**Yazdığımız sözden bir kez döndük.** K013 v2.15 için "üçüncü ve son deneme" demişti; planı ve belgeler "ikinci modelle başka aday
kaydedilmez" diye yazıyordu. 16 Kasım 00:49-05:58 arasında takım arkadaşı kendi dalına sekiz yeni üye, kendi geliştirme sayıları
ve başka tohumlarda yaptığı bir denetimi yükledi. Bu süreç onları istememişti; 06:10 civarında depo denetlenirken gördü. İki
tarafın da puanladığı 20 kopyada adayın (onun) değerleri v2.15'in kayıtlı değerlerinden ortalama +0,0162 yüksekti; bu kopyalar
adayın geliştirme verisiydi. Takım liderine, yeni bir kaydın yazılı sözden dönmek olduğu ve kararın onun olduğu söylendi; bu
süreç ayrıca, öncelik kazanmaksa denemeye değer bulduğunu yazdı. Takım lideri 12:24'te bir deneme daha yapılmasını seçti.
Kapılar gevşetilmedi: aynı yedi kapı ve eşik; karşılaştırma kolu ağaçlar değil, yürürlükteki sürüm. Eski kayıtların hiçbiri
değiştirilmedi.

**Aday kimin.** Üyeleri takım arkadaşı kendi bilgisayarında eğitti, üye kümesini ve 0,4 ağırlığını o seçti. Bu süreç hiçbir şey
eğitmedi ve seçmedi; eğitimi görmedi. "Yalnız dış maçlar kullanıldı, sağlanan maç açılmadı" cümlesi onun beyanıdır
(`experiments/possession_v2/v219/author_74bedbf/experiments/v216u/README.md`).

**Kayıttan önceki denetimler (yeni kopya yok).** 16 ağırlık dosyasının SHA-256 değerleri yazarın listesiyle aynı; sentetik bir
girdide sekiz üyenin yuvarlanmış olasılıkları burada (Linux; Python 3.13 ve 3.10) ve yazarın bilgisayarında (macOS) aynı özeti
veriyor; doğrulama betiği eski üç kopyada kayıtlı satırları aynen, yazarın aday değerlerini altı ondalığa kadar üretti.

**Plan.** `possession-v217-plan.json`, 16 Kasım {plan['registered_at'][11:19]}'de kaydedildi; o anda hiçbir doğrulama satırı yoktu. Kollar: `v2_16`
(üç üye, 0,2) ve `candidate` (sekiz üye, 0,4); kopya, model girdisi, ağaç olasılıkları, havuz ve çözücü ortak. Kopyalar yeni:
tohum 29100 + 10·maç + j; yayın 54100 / 54200, saat 84100 / 84200, öteki benzetici 94100 + maç. Yayın akışlı koşullarda model
girdisi v2.16'nınkidir (doldurulmuş top ve eklenen oyuncular). Doğrulamayı, adayı kurmamış olan bu süreç çalıştırdı; kapılar bir
kez, bütün satırlara uygulandı.

**Sonuç** (`possession-v217-results.json`; dış sağlayıcıların etiketleriyle uyum, yarışma puanı değil):

| koşul | kopya | v2.16 | aday | fark | DFL / Metrica | iyi / kötü / eşit | en kötü kopya |
|---|---|---|---|---|---|---|---|
{line('tactical', 'taktik kamera')}
{line('fill_good', 'iyi yayın akışı (v2.16 girdisi)')}
{line('fill_medium', 'orta yayın akışı (v2.16 girdisi)')}
{line('tactical_sim2', 'öteki benzetici')}

Kapılar: {gate_tr}.

Ağaçlara (v2.11) göre aday {ts(T['candidate_minus_v2_11'])}, v2.16 {ts(T['v2_16_minus_v2_11'])}.

**Karar.** Yedi kapıdan {WORD_TR} geçmedi: G4, "hiçbir kopya sürümden 0,010'dan fazla kötü olmasın". {bad['copy'].replace('|', ', tohum ')} kopyasında
üç ağlı sürüm ağaçlara {ts(bad_rel)} eklerken sekiz ağlı aday {ts(bad_cand)} verdi. Bu, v2.14'ün (K012) tablosunun aynısıdır:
ortalamada ve {T['better']}/16 kopyada kazanç, tek bir kopyada belirgin kayıp. Aday "denendi, kullanılmadı" olarak kaydedildi;
**sürüm v2.16 olarak kaldı**, hiçbir sürüm dosyası değişmedi. Plan, sonuç ne olursa olsun teslimden önce ikinci modelle başka
aday kaydedilmeyeceğini yazar. Betikler, sürüme girmeyen giriş noktasının üreteci ve yazarın anlatımı ile betiklerinin bayt
kopyaları `experiments/possession_v2/v219/` altındadır; ağırlık dosyaları yalnız onun dalındadır.

**Öğrenilen.** Geliştirme kopyalarında ve yazarın kendi denetiminde görülen kazanç yeni kopyalarda da görüldü (ortalama
{ts(T['mean_diff'])}); ama kapılar yalnız ortalamaya bakmaz. Yarışma tek bir maçla puanlanır; "hiçbir kopya belirgin kötü olmasın"
şartı, ortalamada iyi olup tek bir maçta kötüleşebilen bir sistemi elemek için vardır. İki tarafın da puanladığı 20 geliştirme
kopyasında aday hiçbir kopyada sürümün belirgin altında kalmamıştı (en kötü {ts(SEEN['candidate_against_the_release_on_copies_both_sides_scored']['worst'])}); yazarın yeni tohumlardaki denetimi ise adayı
sürümle değil ağaçlarla karşılaştırıyordu (en kötü {ts(SEEN['author_check_on_other_seeds']['tactical DFL']['worst'])}). Buradaki 16 yeni kopyanın birinde aday sürümün {tr(abs(G['G4 no bad copy']['value']))}
altında kaldı. Sözden bir kez dönüldü, şartlar gevşetilmedi ve sonuç ne çıktıysa o yazıldı.
"""
edit('docs/DENEY_KAYDI_TR.md', [("# Deney kaydı\n\n", "# Deney kaydı\n\n" + k020 + "\n" + k019 + "\n\n")])

# ---------------------------------------------------------------- docs/SAHIPLIK_V2_TR.md
tr_update = f"""## Güncelleme, 16 Kasım 2026: v2.16 bu maçta dosyayı değiştirmedi; ikinci modelle dördüncü deneme geçmedi

Teslim sistemi **possession-v2.16** olarak kaldı. Ayrıntılı kayıt: `docs/DENEY_KAYDI_TR.md` K019 ve K020.

**K019.** Zincir 16 Kasım gecesi ekibin bilgisayarında v2.16 ile sorunsuz çalıştı; ama çıkan dosya v2.15'in dosyasıyla bayt bayt
aynıydı. Yani v2.16'nın eklediği adım bu maçta hiçbir etiketi değiştirmedi. Dış kopyalarda ölçülen kazanç benzetilmiş ikinci
kamerayla ölçülmüştü; bu maç için bir söz değildi.

**K020.** Takım arkadaşımız ikinci model için sekiz yeni ağ eğitti. v2.15 için "son deneme" yazmıştık; takım lideri bir deneme
daha yapılmasına karar verdi ve bunu açıkça yazdık. Şartları gevşetmedik. 16 yeni kopyada taktik kamerayla {ts(T['mean_diff'])}
(16 kopyanın {T['better']}'ünde daha iyi), ama bir kopyada {tr(abs(G['G4 no bad copy']['value']))} daha kötü çıktı ve "hiçbir kopya 0,010'dan fazla kötü olmasın" şartı
geçmedi (v2.14'ü durduran şart). Öteki altı şart geçti. Aday sürüme girmedi.

*Öğrenilecek şey:* umut verici bir sonuç görünce "bir kez daha deneyelim" demek insani bir şeydir. Onu savunulabilir kılan,
şartları önceden yazmak, gevşetmemek ve sonucu, hoşa gitmese de, olduğu gibi kaydetmektir.
"""
_p = REPO / 'docs' / 'SAHIPLIK_V2_TR.md'
_s = _p.read_text(encoding='utf-8')
assert _s.endswith("yeni veride ve şartlar önceden yazılarak yapılmalı, kaç kez denendiği de açıkça yazılmalıdır.\n") and tr_update[:40] not in _s
_p.write_text(_s + "\n" + tr_update, encoding='utf-8')

# ---------------------------------------------------------------- experiments README, CLAUDE.md
edit('experiments/possession_v2/README.md', [
    ("`/home/claude/work/v217`, `/home/claude/work/v218` | the folders `v213/`, `v214/`, `v215/`, `v216/`, `v217/`, `v218/` below; `v214/tcn_cache/`",
     "`/home/claude/work/v217`, `/home/claude/work/v218`, `/home/claude/work/v219` | the folders `v213/`, `v214/`, `v215/`, `v216/`, `v217/`, `v218/`, `v219/` below "
     "(`v219/weights/` = the team member's sixteen weight files of commit `74bedbf`, `v219/tcn2/` = byte copies of his inference modules; neither is kept here); `v214/tcn_cache/`"),
    ("clone of the team repository at commit `167dc7b` of branch `mtah-possession` |",
     "clone of the team repository at commit `167dc7b` of branch `mtah-possession` (for K020: commit `74bedbf`) |"),
    ("| superseded, not run | `test_final_wmx.py`",
     "| K019 / K020 the v2.17 candidate: a team member's eight network members against the release; fourth registered attempt with a second model "
     "(`possession-v217-plan.json`, `-results.json`): gates failed, not released | in `v219/`: `register_v217.py` (plan, before any validation row), `exp_v217.py` "
     "(parts 0-3; `wiring_*` reproduce rows of earlier validations), `assemble_v217.py` (gates, written before the rows), `xenv2.py`, `freeze_v217.py` (not run), "
     "`port/make_run217.py`, `port/apply_v217.py`, `port/quick217.py`, `port/test_possession_v217.py.txt` (the integration that was prepared and not released), "
     "`docs_v217_fail.py`, `k019_body.md`; `author_74bedbf/` = byte copies of the author's files of branch `mtah-possession`, commit `74bedbf` |\n"
     "| superseded, not run | `test_final_wmx.py`"),
])
snap = f"""## Status snapshot (16 Nov 2026, afternoon — verify before relying on it)

- **Submission system: still `possession-v2.16`** (`python -m possession.run216`). Nothing of the release changed today.
- **K020, a fourth attempt with the second model, against a written statement: FAILED its gates.** The v2.15 plan and the
  documents said that no further candidate with the second model would be registered. On 16 Nov the team member who
  wrote the network pushed eight new members (branch `mtah-possession`, commit `74bedbf`) with his development numbers;
  the team lead decided at 12:24 to have them validated. Plan `possession-v217-plan.json` (registered {plan['registered_at'][11:19]}, before any
  row; the same seven gates and thresholds, against the release). Results `possession-v217-results.json`: tactical
  {f4(T['v2_16_mean'])} -> {f4(T['candidate_mean'])} ({sg(T['mean_diff'])}; {T['better']} better, {T['worse']} worse); fills {sg(FG['mean_diff'])} / {sg(FM['mean_diff'])}; other simulator {sg(S2['mean_diff'])}; six gates
  passed, G4 failed (one copy at {sg(G['G4 no bad copy']['value'])}; limit -0.010; the gate v2.14 had failed). Not released. The plan says:
  **whatever the outcome, no further candidate with the second model is registered before the deadline.** Scripts and
  the prepared, unreleased integration: `experiments/possession_v2/v219/`. If the team lead asks to deliver the
  candidate anyway: the gates are not relaxed after the fact (AGENTS.md), and a system that failed its registered
  validation is not presented as selected.
- **K019 (16 Nov 00:13-01:04): the chain ran OK on the team's computer with v2.16** (commit 1c31412; GitHub Actions
  succeeded; `PLATFORM AYNI` on eleven variants; `TEMIZ KLON AYNI`), and its status line
  `TESLIM ... onceki teslim dosyasi ile AYNI` says that **the v2.16 file is byte-identical to the v2.15 file** of 15 Nov:
  on the provided match the added-players step changed no label (not applied, or nothing to add, or what was added
  changed no decision; Appendix R says which and is not read here). A hash comparison, not an accuracy measurement and
  not a selection input.
- **Form:** the team lead submitted the Google Form on 15 Nov at about 18:45 with the v2.15 files (the same bytes as the
  v2.16 file). The Form can be sent again through the same link (not recorded in the repository: it was mailed to
  participants only); the last response before the deadline counts (SUBMISSION.md). Only the team lead fills it in.
  The technical document changed today (Section 3 tells of the fourth attempt): one more chain run regenerates
  `LittleSickle.md`, and the Form should then be sent again with it.
- **Deadline:** Tue 17 Nov 23:59 CET = Wed 18 Nov 01:59 Istanbul.

## Earlier status (15 Nov 2026, evening)
"""
edit('CLAUDE.md', [("## Status snapshot (15 Nov 2026, evening — verify before relying on it)\n", snap)])

# ---------------------------------------------------------------- GIT-YUKLE-V2.cmd
msg = [
    "Records K019-K020: v2.16 chain OK on the team computer; a fourth attempt with the second model failed its gates",
    "",
    "K020: a team member pushed eight newly trained network members on 16 Nov. The v2.15 plan and the documents had",
    "said that no further candidate with the second model would be registered; the team lead decided to make one more",
    "attempt, and the plan and the documents say so. Registered before any validation row, possession-v217-plan.json:",
    "the same seven gates and thresholds, against the release. On 16 new copies with the tactical camera spellF1",
    f"{f4(T['v2_16_mean'])} to {f4(T['candidate_mean'])}, with a simulated second camera {sg(FG['mean_diff'])} and {sg(FM['mean_diff'])}, copies of the other simulator {sg(S2['mean_diff'])}.",
    f"Six gates passed; the gate on single copies failed, one copy {abs(G['G4 no bad copy']['value']):.4f} lower, possession-v217-results.json.",
    "Not released: possession-v2.16 stays the release and no",
    "release file changed. Scripts and the prepared, unreleased integration are under experiments/possession_v2/v219.",
    "",
    "K019: on 16 Nov the delivery chain ran end to end on the team lead computer with v2.16, every step OK. Its status",
    "line says that the v2.16 file has the same bytes as the v2.15 file of the day before: on the provided match the",
    "added-players step changed no label. The Form had been submitted on 15 Nov with those bytes.",
    "",
    "No provided match data and no frame-level output are in the repository. External numbers are",
    "agreement with other providers labels, not competition scores.",
]
for l in msg:
    assert all(c not in l for c in '%^&<>|"()!') and len(l) <= 118, l
old_start = '> "%POSSESSION_MSG1%" echo Release possession-v2.16: lost players added from the broadcast tracking; records K015-K018\n'
old_end = '>> "%POSSESSION_MSG1%" echo Co-Authored-By: Claude Fable 5.2 ^<noreply@anthropic.com^>\n'
p = REPO / 'GIT-YUKLE-V2.cmd'
s = p.read_bytes().decode('utf-8').replace('\r\n', '\n')
a, b = s.index(old_start), s.index(old_end)
assert s.count(old_start) == 1 and s.count(old_end) == 1 and a < b
new_block = '> "%POSSESSION_MSG1%" echo ' + msg[0] + '\n' + ''.join('>> "%POSSESSION_MSG1%" echo' + ('.' if not l else ' ' + l) + '\n' for l in msg[1:]) + '>> "%POSSESSION_MSG1%" echo.\n'
p.write_bytes((s[:a] + new_block + s[b:]).replace('\n', '\r\n').encode('utf-8'))
print('fail-case documents written in', REPO, '| failed gates:', failed)
