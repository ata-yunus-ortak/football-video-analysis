"""After the chain rehearsal of the selected possession-v2.15 (possession-v215-rehearsal.json): the rehearsal sentences of
TECHNICAL_DOCUMENT.md (Section 7), TECHNICAL_DOCUMENT_V2.md (fourth addendum, item 7), docs/SAHIPLIK_V2_TR.md and README.md,
and the scripts added to the archive after docs_common.py had written the experiments README.
Run once, after docs_v215_en.py, docs_v215_more.py and docs_common.py. Usage: docs_after_rehearsal.py REPO_DIR"""
import json, sys
from pathlib import Path

REPO = Path(sys.argv[1])
reh = json.loads((REPO / 'possession-v215-rehearsal.json').read_text())
new, old = reh['delivered_file_against_the_bundle_labels'], reh['for_comparison_the_v2.11k_chain_file_13_Nov']
dif = reh['against_the_v2.11k_file']
assert reh['status_lines'][-2].startswith('SONUC: TESLIM HAZIR') and reh['run_record_rows']['Second model'].startswith('used')
assert dif['all_inside_graded_windows'] and dif['all_from_the_kick_offs_on']
f3 = lambda x: f'{x:.3f}'
f4 = lambda x: f'{x:.4f}'
tr = lambda x, nd=3: f'{x:.{nd}f}'.replace('.', ',')
S_NEW, S_OLD = new['graded windows']['spell_f1_mean'], old['graded windows']['spell_f1_mean']
M_NEW, M_OLD = new['graded windows']['macro_f1'], old['graded windows']['macro_f1']
PCT = 100 * dif['share_of_graded_frames']


def edit(name, pairs):
    p = REPO / name
    s = p.read_text(encoding='utf-8')
    for a, b in pairs:
        assert s.count(a) == 1, (name, s.count(a), a[:70])
        s = s.replace(a, b)
    p.write_text(s, encoding='utf-8')


edit('TECHNICAL_DOCUMENT.md', [
 ('''  other team's id (0.766 with the check, 0.431 without). For the release as submitted
  (step 7 with the kick-off rule) the chain was run once more on the first bundle with an
  invented Smart Tagging file whose two kick-off tags are 5 s windows around the bundle's
  kick-offs: every step passed and the file scored 0.764 (0.759 for the same bundle without the
  tag file, where the models label the invented stretch before the second-half kick-off
  themselves). This checks wiring and size, not accuracy on the provided match.''',
  f'''  other team's id (0.766 with the check, 0.431 without). After the kick-off rule of step 7 was
  added the chain was run once more on the first bundle with an
  invented Smart Tagging file whose two kick-off tags are 5 s windows around the bundle's
  kick-offs: every step passed and the file scored 0.764 (0.759 for the same bundle without the
  tag file, where the models label the invented stretch before the second-half kick-off
  themselves). For the release as submitted (with step 9) it was run again on that bundle and
  tag file: every step passed, the file differs from the previous one on {PCT:.1f}% of the graded
  frames and scored {f3(S_NEW)} (`possession-v215-rehearsal.json`). This checks wiring and size, not
  accuracy on the provided match; the games in these bundles had been used in development.'''),
])
edit('TECHNICAL_DOCUMENT_V2.md', [
 ('''>    network); the 4-decimal network probabilities and the output were identical under Python 3.10 /
>    numpy 1.26.4 and Python 3.13 / numpy 2.5.3, the unrounded network outputs were not.''',
  f'''>    network); the 4-decimal network probabilities and the output were identical under Python 3.10 /
>    numpy 1.26.4 and Python 3.13 / numpy 2.5.3, the unrounded network outputs were not. The delivery
>    chain with the default configuration was rehearsed once, after the decision, on the full-size
>    synthetic bundle of K003 with the invented Smart Tagging file of K011
>    (`possession-v215-rehearsal.json`): all steps OK in {reh['seconds']} s on 2 CPUs (the v2.11k chain: {reh['seconds_of_the_v2.11k_chain_13_Nov']} s; with
>    the network one generation took about five minutes longer under Python 3.10 / numpy 1.26.4),
>    peak memory {reh['peak_child_rss_gb']} GB. The
>    delivered file differs from the v2.11k chain file on {dif['frames_that_differ']} frames ({PCT:.1f}% of the graded frames),
>    none before the kick-offs; against the proxy labels of that bundle spellF1 {f4(S_NEW)} (v2.11k chain
>    {f4(S_OLD)}), macroF1 {f4(M_NEW)} ({f4(M_OLD)}). A wiring and size check on games that had been used in
>    development, not a selection input and not an accuracy claim. Whether the chain runs on the
>    team's computer is the last condition of the registered decision rule and is checked there.'''),
])
edit('docs/SAHIPLIK_V2_TR.md', [
 ('''"Second model" satırı vardır: kullanıldı / kullanılmadı. Depoya yeni bir model dosyası girdi
(`models/possession-tcn-v215.npz`, yaklaşık 10 MB; yalnız açık DFL verisiyle eğitildi).''',
  f'''"Second model" satırı vardır: kullanıldı / kullanılmadı. Depoya yeni bir model dosyası girdi
(`models/possession-tcn-v215.npz`, yaklaşık 10 MB; yalnız açık DFL verisiyle eğitildi). Ağ, bir dosya üretimine
yaklaşık beş dakika ekler (provada, 2 işlemcide); zincir bu yüzden öncekinden uzun sürer.

**Tam boy prova (15 Kasım, `possession-v215-rehearsal.json`).** K003'ün sentetik paketi ve K011'in uydurma Smart Tagging
dosyasıyla varsayılan zincir baştan sona çalıştırıldı: bütün adımlar OK, {reh['seconds']} saniye (v2.11k zinciri {reh['seconds_of_the_v2.11k_chain_13_Nov']} saniye),
en çok {tr(reh['peak_child_rss_gb'], 2)} GB bellek. Üretilen dosya v2.11k zincirinin dosyasından puanlanan karelerin %{tr(PCT, 1)}'sında farklı; o
paketin etiketlerine göre spellF1 {tr(S_NEW)} (v2.11k zinciri {tr(S_OLD)}). Bu bir bağlantı ve boyut denetimidir; doğruluk ölçümü
değildir ve hiçbir seçimde kullanılmadı. **Kalan koşul:** zincirin ekibin bilgisayarında da OK bitmesi; `URETIM` ve
`TESLIM` satırlarında `possession-v2.15` yazmalı. Daha alt bir basamağın adı yazarsa teslim edilen o basamaktır.'''),
])
edit('README.md', [
 ('''(`possession-rehearsal-results.json`, log entry K003).''',
  '''(`possession-rehearsal-results.json`, log entry K003), and again for the current release
(`possession-v215-rehearsal.json`, log entry K013).'''),
])
edit('experiments/possession_v2/README.md', [
 ('''`docs_v215_en.py`, `docs_v215_more.py` |''',
  '''`docs_v215_en.py`, `docs_v215_more.py`, `docs_common.py`, `docs_after_rehearsal.py`, `claude_md_v215.py`, `gityukle215.py` (documents and launcher), `log_k012_k013.py` (puts both log entries into the log); rehearsal of the chain: `score_k013.py`, `assemble_rehearsal_v215.py` (`possession-v215-rehearsal.json`) |'''),
])
print('rehearsal sentences written:', f3(S_NEW), f3(S_OLD), f'{PCT:.2f}%', reh['seconds'], 's')
