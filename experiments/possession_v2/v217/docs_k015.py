"""Records of K015 (15 Nov): log entry, archive of the scripts, one sentence each in the documents, the status snapshot and the
upload launcher. Reporting only; the release is unchanged. Run once, after k015_assemble.py. Usage: docs_k015.py REPO_DIR"""
import json, sys, shutil
from pathlib import Path
REPO = Path(sys.argv[1]); V = Path('/home/claude/work/v217')
d = json.loads((REPO / 'possession-k015-tag-rescue.json').read_text())
h, c, r = d['how_often'], d['ceilings_with_the_labels_as_oracle'], d['rule_tried']['spell_f1_change_by_regime_and_variant']
tr = lambda x, nd=4: f'{x:+.{nd}f}'.replace('.', ',')
pc = lambda x, nd=0: f'%{100 * x:.{nd}f}'.replace('.', ',')
en = lambda x: f'{x:+.4f}'
SCRIPTS = ('rest1.py', 'rest2.py', 'orc1.py', 'taglib.py', 'rule1.py', 'team1.py', 'k015_assemble.py', 'docs_k015.py')
dst = REPO / 'experiments' / 'possession_v2' / 'v217'
dst.mkdir(parents=True, exist_ok=True)
for n in SCRIPTS:
    shutil.copyfile(V / n, dst / n)


def edit(name, pairs, binary=False):
    p = REPO / name
    s = p.read_bytes().decode('ascii') if binary else p.read_text(encoding='utf-8')
    for a, b in pairs:
        assert s.count(a) == 1, (name, s.count(a), a[:70])
        s = s.replace(a, b)
    if binary:
        assert s.count('\n') == s.count('\r\n')
        p.write_bytes(s.encode('ascii'))
    else:
        p.write_text(s, encoding='utf-8')
    return s


bt = h['by_type']
rows = '\n'.join(f"| {tr_name} | {str(bt[k]['per_copy']).replace('.', ',')} | {pc(bt[k]['no_D_of_ours_on_the_stretch'], 1)} | {bt[k]['published_tags_of_this_type_in_the_provided_file']} |"
                 for k, tr_name in (('throw-in', 'taç'), ('free kick', 'serbest vuruş (Metrica maçlarında kale vuruşları da burada)'), ('goal kick', 'kale vuruşu'), ('corner kick', 'korner'), ('kick off', 'gol sonrası başlama')))
reg_tr = {'clean': 'kusursuz etiket (kayma yok)', 'second': 'bir saniye kadar kayan etiket, %5 sahte', 'default': 'tipik (±1,5 sn kayma, 0,3-3 sn dağılma, %0-15 sahte)',
          'noisy': 'gürültülü (yarı sayıda etiket, 1,5 sn gecikme, 3 sn dağılma, %15 sahte)', 'false30': 'tipik, %30 sahte etiket'}
rule_rows = '\n'.join(f"| {reg_tr[g]} | {tr(r[g]['c 120']['mean'])} | {tr(r[g]['c 120']['min'])} | {str(r[g]['c 120']['forced_per_copy']).replace('.', ',')} | {pc(r[g]['c 120']['share_of_forced_frames_within_1s_of_a_true_dead_frame'])} | {tr(r[g]['c inf']['mean'])} | {tr(r[g]['c inf']['min'])} |"
                      for g in ('clean', 'second', 'default', 'noisy', 'false30'))
ms = h['missed_stretches']
pmed = f"{ms['largest_pooled_P_dead_on_the_stretch_quantiles_10_25_50_75_90'][2]:.2f}".replace('.', ',')
ENTRY = f"""## K015 — Smart Tagging duran top etiketiyle "kaçırılan duran topu zorla yaz" fikri: ölçüldü, kazanç çok küçük (sürüm değişmedi), 15 Kasım 2026

**Neden.** Takım lideri 15 Kasım 11:47'de şunu sordu: Smart Tagging bir aralık için duran top diyorsa ve biz o aralıkta hiç duran
top yazmamışsak, orada mutlaka bir duran top vardır; ölü top olasılığının en yüksek olduğu yere bir duran top koyup sonra başını
ve sonunu bulsak puan artar mı? Bu daha önce denenmemişti: v3.0 / v3.1 (P002) etiketleri ikinci aşamaya öğrenilen kanıt olarak
vermişti. Organizatörün belgeleri fikri destekliyor ("every set piece is a restart and every restart ends a dead-ball stretch"),
ama aynı yerde etiketlerin otomatik olduğu, sahte ve eksik etiket içerdiği de yazıyor. Bu kayıt yalnız geliştirme ve raporlamadır:
plan kaydedilmedi, doğrulama yapılmadı, hiçbir şey seçilmedi, teslim sistemi **v2.15** olarak kaldı. Sağlanan maç ve etiket dosyası
açılmadı. Sayılar: `possession-k015-tag-rescue.json`; betikler: `experiments/possession_v2/v217/`.

**Veri.** K014'ün 42 geliştirme kopyası (5 dış maç) ve bunlar için saklanan v2.15 kararı. Dış maçlarda Smart Tagging olmadığı için
duran top etiketleri **benzetimle** üretildi: gerçek yeniden başlama anının çevresinde birkaç saniyelik pencere (v3 planındaki
benzetici), tür başına sayılar DATA.md'de yayımlanan sayılara göre (taç 26, korner 12, kale vuruşu 10, serbest vuruş 5, gol sonrası
başlama 4), ardından zaman kayması ve sahte etiket eklenerek.

**Bu durum ne sıklıkta oluyor?** Kopya başına {str(h['per_copy']).replace('.', ',')} duran top (yeniden başlamayla biten ölü top aralığı) var. Kararımız bunların
{pc(1 - h['no_D_of_ours_on_the_stretch'])}'ünde en az bir D karesi yazıyor; hiç D yazmadığımız aralık kopya başına {str(h['per_copy_missed']).replace('.', ',')} (DFL maçlarında %2, Metrica maçlarında %10-20).
Kaçırılanlar kısa (ortanca {str(ms['median_length_s']).replace('.', ',')} sn; bulunanlarda {str(ms['found_median_length_s']).replace('.', ',')} sn) ve top bu karelerin yalnız {pc(ms['ball_seen_share'])}'unda görünüyor.
Kaçırılan aralıklarda en yüksek ölü top olasılığının ortancası {pmed}: model çoğunda bir şey görüyor ama çözücünün
D'ye giriş-çıkış maliyetini aşamıyor.

| tür | kopya başına | hiç D yazmadığımız | sağlanan dosyada yayımlanan etiket sayısı |
|---|---|---|---|
{rows}

Yayımlanan sayılarla etiketler bir maçtaki yeniden başlamaların yaklaşık yarısını kapsıyor (benzetimde kopya başına {str(c['mean_tagged_at_published_counts']).replace('.', ',')} / {str(c['mean_restarts_per_copy']).replace('.', ',')})
ve en çok kaçırdığımız türden (serbest vuruş) yalnız 5 etiket var. "Etiket var, bizde D yok" durumu kopya başına {str(c['published_miss']['stretches_written_per_copy']).replace('.', ',')} kez oluşuyor.

**Tavan (etiketler kusursuz, aralığın gerçek sınırları biliniyor).**

| | bütün yeniden başlamalar etiketli olsaydı | yayımlanan sayılarla |
|---|---|---|
| kaçırılan aralığı D yaz | {tr(c['all_miss']['mean'])} | {tr(c['published_miss']['mean'])} (DFL {tr(c['published_miss']['dfl'])}, Metrica {tr(c['published_miss']['metrica'])}) |
| D'nin bitişini gerçek yeniden başlama anına çek | {tr(c['all_time']['mean'])} | {tr(c['published_time']['mean'])} ({c['published_time']['worse']} kopyada daha kötü) |
| ikisi birlikte | {tr(c['all_both']['mean'])} | {tr(c['published_both']['mean'])} |

**Denenen kural.** Etiket penceresinin 5 sn öncesinden sonuna kadar kararımızda hiç D yoksa: çözücünün o bölgede D'den geçmesinin
en ucuz olduğu kare bulunur (değiştirilmemiş v2 çözücüsünün ileri-geri puanları); bu maliyet bir sınırın altındaysa (120 log
birimi = bir D parçasının giriş-çıkış maliyeti) çözücü o kare D'ye zorlanarak yeniden çalıştırılır; D parçasının başı ve sonu
böylece modelin olasılıklarından çıkar. spellF1 değişimi (42 kopya ortalaması):

| etiket benzetimi | sınır 120: ortalama | en kötü kopya | kopya başına zorlanan | gerçek bir duran topa denk gelen | sınırsız: ortalama | en kötü kopya |
|---|---|---|---|---|---|---|
{rule_rows}

Sınırın başka değerleri (60-110), arama bölgesinin 3 / 8 sn öncesinden başlaması ya da 2 sn sonrasına uzaması, zorlanan parçanın
en az 1 sn yapılması ve parça ile bir sonraki takım değişimi arasındaki kısa sahipliğin D yazılması bu tabloyu değiştirmedi
(hepsi {tr(min(v['mean'] for g in r for k, v in r[g].items() if k != 'c inf'))} ile {tr(max(v['mean'] for g in r for k, v in r[g].items() if k != 'c inf'))} arasında). Etiketin "vuruşu kullanan takım" bilgisinin düzelteceği bir şey yok: bulunan
yeniden başlamalardan sonra yazdığımız ilk takım {d['taker_team']['n']} durumun {d['taker_team']['wrong_team']}'unda yanlış.

**Sonuç.** Fikir mantıklı ve kural beklendiği gibi çalışıyor, ama kazanılabilecek puan çok küçük: kusursuz kullanımda bile
{tr(c['published_miss']['mean'], 3)}, denenen kuralla {tr(r['noisy']['c 120']['mean'], 4)} ile {tr(r['second']['c 120']['mean'], 4)} arası; sınır konmazsa sahte etiketler zarar veriyor ({tr(r['false30']['c inf']['mean'], 4)}'e kadar).
Bu, şimdiye kadarki her adaya uygulanan kazanç kapısının (+0,008) onda biri ve organizatörün tek maçta gürültü saydığı farkın
(0,04) çok altında. Gerçek etiketlerin hata düzeni bilinmiyor ve ölçülemez; etiketleyici topun izine dayanıyorsa zaten bizim de
bulduğumuz duran topları etiketliyor olabilir. Bu yüzden aday olarak kaydedilmedi ve sürüm değiştirilmedi.

**Sınırlar.** Geliştirme kopyaları daha önce kullanıldı ve kural seçenekleri bunların üzerinde karşılaştırıldı; bu bir doğrulama
değildir. Etiketler benzetimdir. Sayılar bozulmuş dış kopyalarda başka sağlayıcıların etiketleriyle uyumdur; yarışma puanı değildir.

"""
s = edit('docs/DENEY_KAYDI_TR.md', [('# Deney kaydı\n\n## K014 —', '# Deney kaydı\n\n' + ENTRY + '## K014 —')])

edit('experiments/possession_v2/README.md', [
    ('`/home/claude/work/v213`, `/home/claude/work/v214`, `/home/claude/work/v215`, `/home/claude/work/v216` | the folders `v213/`, `v214/`, `v215/`, `v216/` below;',
     '`/home/claude/work/v213`, `/home/claude/work/v214`, `/home/claude/work/v215`, `/home/claude/work/v216`, `/home/claude/work/v217` | the folders `v213/`, `v214/`, `v215/`, `v216/`, `v217/` below;'),
    ('| superseded, not run | `test_final_wmx.py`',
     '| K015 set-piece tags of Smart Tagging as a trigger for a missing dead-ball stretch, simulated tags on the 42 development copies (reporting only; `possession-k015-tag-rescue.json`; release unchanged) | in `v217/`: `rest1.py` (restarts of the development matches and their type), `rest2.py` (how the v2.15 decision treats the stretch before each), `orc1.py` (ceilings with the labels as oracle), `taglib.py` (tag simulation, forward-backward scores of the v2 decoder, the rule), `rule1.py` (the rule and its variants in five tag regimes), `team1.py` (team after a restart), `k015_assemble.py`, `docs_k015.py` (record file, log entry and document sentences). They import `errlib.py` of `v216/` |\n'
     '| superseded, not run | `test_final_wmx.py`'),
])

edit('TECHNICAL_DOCUMENT.md', [
    ('and dropped: +0.011 with typical tags but -0.008 without tags, registered gates failed |',
     f'and dropped: +0.011 with typical tags but -0.008 without tags, registered gates failed. A rule that forces a dead-ball stretch at a set-piece tag where the decision has none was explored on '
     f'development copies with simulated tags (log entry K015): the decision already has `D` on {100 * (1 - h["no_D_of_ours_on_the_stretch"]):.0f}% of the stretches before a restart and the published tag counts cover about half of the restarts, '
     f'so the ceiling is {c["published_miss"]["mean"]:+.3f} spellF1 and the rule gave {en(r["noisy"]["c 120"]["mean"])} to {en(r["second"]["c 120"]["mean"])}; not adopted |'),
])

edit('TECHNICAL_DOCUMENT_V2.md', [
    ('''>    match left out at a time, gained 0.0095 on average with a worst copy of -0.023 and was not
>    registered. The release is unchanged.
''',
     f'''>    match left out at a time, gained 0.0095 on average with a worst copy of -0.023 and was not
>    registered. The release is unchanged.
> 10. **Set-piece tags as a trigger for a missing stoppage (K015, 15 November, reporting only).** The
>    organisers' documentation says every set-piece tag is a restart at the end of a dead-ball
>    stretch. On the 42 development copies the v2.15 decision has at least one `D` frame on {100 * (1 - h["no_D_of_ours_on_the_stretch"]):.0f}% of
>    the labelled stretches that end in a restart; the {h["per_copy_missed"]} per copy without any are short (median
>    {ms["median_length_s"]} s) and the ball is seen on {100 * ms["ball_seen_share"]:.0f}% of their frames. Tags simulated at the published per-type counts
>    cover about half of the restarts ({c["published_miss"]["stretches_written_per_copy"]} missed stretches per copy carry one). Writing the true stretch
>    there would gain {en(c["published_miss"]["mean"])} spellF1 (DFL {en(c["published_miss"]["dfl"])}, Metrica {en(c["published_miss"]["metrica"])}); moving the end of our `D` to the true
>    restart {en(c["published_time"]["mean"])}. A rule that forces the unchanged decoder through `D` where it objects least,
>    if that costs at most one entry and exit (120 log units), gained {en(r["clean"]["c 120"]["mean"])} with exact tags,
>    {en(r["second"]["c 120"]["mean"])} with tags accurate to a second, {en(r["default"]["c 120"]["mean"])} / {en(r["noisy"]["c 120"]["mean"])} / {en(r["false30"]["c 120"]["mean"])} with typical / noisy / 30% false tags;
>    without the cost limit false tags cost up to {en(r["false30"]["c inf"]["mean"])}. A tenth of the gain gate used for every
>    candidate, with simulated tags whose real error profile cannot be measured: not registered, the
>    release is unchanged (`possession-k015-tag-rescue.json`, scripts in `experiments/possession_v2/v217/`).
'''),
])

edit('CLAUDE.md', [
    ('''  differences below about 0.04 are noise on one match. Do not present any of this as a validation.
''',
     f'''  differences below about 0.04 are noise on one match. Do not present any of this as a validation.
- **K015 (15 Nov, reporting only; release unchanged):** the team lead asked whether a Smart Tagging set-piece tag
  without a `D` of ours around it should force a dead-ball stretch (`possession-k015-tag-rescue.json`,
  `experiments/possession_v2/v217/`; simulated tags on the 42 development copies, the provided tag file was not read).
  The decision already has `D` on {100 * (1 - h["no_D_of_ours_on_the_stretch"]):.0f}% of the stretches before a restart; the published tag counts (57 without the
  start kick-offs, only 5 free kicks) cover about half of the restarts, so the case occurs {c["published_miss"]["stretches_written_per_copy"]} times per copy. Ceiling
  {en(c["published_miss"]["mean"])}; the rule (force the decoder through `D` where it costs least, cost limit 120) {en(r["noisy"]["c 120"]["mean"])} to {en(r["second"]["c 120"]["mean"])}; without
  the limit false tags cost up to {en(r["false30"]["c inf"]["mean"])}. Not registered (a tenth of the +0.008 gain gate). Do not present it
  as tested on real tags, and do not re-open it without new evidence about the real tags (which cannot be looked at).
'''),
])

new = ['K015: asked by the team lead, whether a Smart Tagging set-piece tag without a dead-ball stretch of ours',
       'around it should force one. Simulated tags on the 42 development copies, reporting only, see',
       'possession-k015-tag-rescue.json and experiments/possession_v2/v217. The decision already has a dead-ball',
       'stretch before 93 per cent of the restarts and the published tag counts cover about half of them, so the',
       'ceiling is 0.003 and the rule gained about 0.001. Not registered. The release is unchanged.',
       '']
anchor = '>> "%POSSESSION_MSG1%" echo K014: error-pattern study of v2.15 on 42 external development copies, reporting only, see'
block = ''.join(('>> "%POSSESSION_MSG1%" echo.\r\n' if not x else '>> "%POSSESSION_MSG1%" echo ' + x + '\r\n') for x in new)
s = edit('GIT-YUKLE-V2.cmd', [
    ('echo Release possession-v2.15 (second model pooled with the v2 models); records K007-K014\r\n',
     'echo Release possession-v2.15 (second model pooled with the v2 models); records K007-K015\r\n'),
    (anchor, block + anchor)], binary=True)
lines = s.split('\r\n')
msg = [l.split(' echo ', 1)[1] for l in lines if l.startswith(('> "%POSSESSION_MSG1%" echo ', '>> "%POSSESSION_MSG1%" echo '))]
assert all(not m.startswith('(') for m in msg) and "'" not in ''.join(msg) and all(len(m) <= 110 for m in msg)
for m in msg:
    t = m.replace('^<', '').replace('^>', '').replace('%%', '')
    assert not any(ch in t for ch in '<>|&%^"'), m
assert f'{100 * (1 - h["no_D_of_ours_on_the_stretch"]):.0f}' == '93' and round(c['published_miss']['mean'], 3) == 0.003
print('records written;', len(msg), 'message lines')
