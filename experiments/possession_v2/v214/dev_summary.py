"""Collect what was seen on external data while this candidate was developed (all on copies already scored in the v2.13
validation, or on Metrica game 3; none of it is a validation) and apply the rule that fixes pool and weight.
Reads explore2_dev.json (explore2.py dev d4s0,d4s1,d4s2 d6s0,d6s1,d6s2), explore2_his.json (explore2.py his his his) and
the diagnostic log; writes development_summary.json. Usage: /usr/bin/python3 dev_summary.py"""
import json, re
import numpy as np

V = '/home/claude/work/v214/'
dev = json.load(open(V + 'explore2_dev.json'))
his = json.load(open(V + 'explore2_his.json'))
GRID = ['ari20', 'ari30', 'ari40', 'ari50', 'ari60', 'geo30', 'geo40', 'geo50', 'geo60']
assert len(dev) == 22 and len(his) == 22, (len(dev), len(his))


def stats(rows, name, keys=None):
    keys = keys or list(rows)
    d = np.array([rows[k][name][0] - rows[k]['v2_11'][0] for k in keys])
    return {'n': len(keys), 'mean': round(float(d.mean()), 4), 'min': round(float(d.min()), 4), 'better': int((d > 0).sum()),
            'below_-0.010': int((d < -0.010).sum())}


groups = {'all 22': list(dev), 'DFL 10': [k for k in dev if k.startswith('J03')], 'Metrica 12': [k for k in dev if k.startswith('MET')],
          'our simulator 17': [k for k in dev if k.endswith('_tactical')], 'his simulator 5': [k for k in dev if k.endswith('sim2')]}
table = {g: {n: stats(dev, n, ks) for n in ['tcn_alone', 'v213rule'] + GRID} for g, ks in groups.items()}
table_his = {g: {n: stats(his, n, ks) for n in ['tcn_alone', 'v213rule'] + GRID} for g, ks in groups.items()}

# the rule, written before the Metrica rows of the re-trained weights were looked at (NOTES.md, 14 Nov 21:23)
ok = [n for n in GRID if table['all 22'][n]['below_-0.010'] == 0]
best = max(table['all 22'][n]['mean'] for n in ok)
near = [n for n in ok if best - table['all 22'][n]['mean'] <= 0.001]
chosen = min(near, key=lambda n: int(n[3:]))
if len({n[:3] for n in near if int(n[3:]) == int(chosen[3:])}) > 1:      # both pools at the same smallest weight: the larger mean
    chosen = max([n for n in near if int(n[3:]) == int(chosen[3:])], key=lambda n: table['all 22'][n]['mean'])
unrounded = {n: float(np.mean([dev[k][n][0] - dev[k]['v2_11'][0] for k in dev])) for n in GRID}
pool = {'ari': 'arithmetic', 'geo': 'geometric'}[chosen[:3]]
weight = int(chosen[3:]) / 100.0

diag = {}
for line in open(V + 'diag1_met3_7772.log'):
    m = re.match(r'MET3 7772 (\S+) (\{.*\})', line)
    if m:
        diag[m.group(1)] = round(json.loads(m.group(2))['spell_f1'], 4)

fmt = lambda s: f"{s['mean']:+.4f} (worst copy {s['min']:+.4f}, better on {s['better']} of {s['n']})"
seen = [
 'Everything in this list was computed on copies that had already been scored: the 20 copies of the v2.13 validation with the '
 'tactical camera or the team member\'s simulator (seeds 13100-13133, 63100-63103), the two Metrica game 3 copies scored after the '
 'v2.13 decision (33103, 63108) and one further Metrica game 3 copy (seed 7772). They are development data, not a validation.',
 'possession-v213-results.json (13 Nov): the v2.13 rule with the committed weights, +0.0063 on 16 copies (DFL -0.0045, Metrica '
 '+0.0172), TCN alone 0.6257 against 0.6598; three gates failed.',
 'Diagnostic, committed weights tcn_dfl6.npz alone on a Metrica game 3 copy (seed 7772) with one component of our simulator '
 'switched off (spellF1): ' + ', '.join(f'{k} {v}' for k, v in diag.items()) + '. The same weights on a training match with our '
 'corruption: 0.8165 (in-sample, therefore not used for diagnosis).',
 'Committed weights, 22 development copies, mean spellF1 difference to v2.11: v2.13 rule ' + fmt(table_his['all 22']['v213rule']) +
 '; TCN alone ' + fmt(table_his['all 22']['tcn_alone']) + '; arithmetic pool 0.2 through the v2 decoder ' + fmt(table_his['all 22']['ari20']) +
 '; 0.3 ' + fmt(table_his['all 22']['ari30']) + '. DFL 10: v2.13 rule ' + fmt(table_his['DFL 10']['v213rule']) + ', pool 0.2 ' +
 fmt(table_his['DFL 10']['ari20']) + '.',
 'One development model without J03WN1 (five matches, both simulators, one seed; n1_both_s0), five J03WN1 copies: TCN alone '
 '+0.0016 against v2.11 (committed five-match weights: -0.0326), better than the committed weights on all five, the copy of his '
 'own simulator included.',
 'Re-trained weights (dfl4 members on DFL copies, dfl6 members on Metrica copies; three members each), 22 development copies: ' +
 '; '.join(f"{n} {fmt(table['all 22'][n])}" for n in ['tcn_alone', 'v213rule'] + GRID) + '.',
 'The same by source. DFL 10: ' + '; '.join(f"{n} {fmt(table['DFL 10'][n])}" for n in ['tcn_alone'] + GRID) + '. Metrica 12: ' +
 '; '.join(f"{n} {fmt(table['Metrica 12'][n])}" for n in ['tcn_alone'] + GRID) + '. Copies of his simulator (5): ' +
 '; '.join(f"{n} {fmt(table['his simulator 5'][n])}" for n in ['tcn_alone'] + GRID) + '.',
 'Decoder constants around the release values (team change 2-5, entry / exit 50-70, dead bias -0.1 to -0.5) were looked at on the '
 '10 DFL development copies with the geometric pool 0.4: within 0.001 of the release constants or worse. The constants are not changed.',
 'One and two members instead of three (10 DFL development copies): the pooled result changed by less than 0.002 on average.',
 'Other mixing variants were looked at with the committed weights on the same copies (explore.py: the dead-ball probability from one '
 'model and the team probability from the mix, in four combinations; the single-cost decoder with weight 0.3; the TCN alone through '
 'the v2 decoder). None is used.',
 'check_exp_v214.py: on development copy J03WN1 13100 the arms of the validation script, with the geometric pool 0.4 set by hand, '
 'give exactly the numbers computed from stored probabilities (v2.11 0.6256, pooled 0.6674, TCN alone 0.6494). xenv_tcn.py: the '
 '4-decimal network probabilities of one member on one development copy are identical under Python 3.13 / numpy 2.5.3 and '
 'Python 3.10 / numpy 1.26.4 (no score involved).',
 'exp_v214.py smoke run on training match J03WOH (in-sample for every model): wiring only, it computes no score.',
 'Not seen: any score of the candidate, of the new weights or of any pool on a copy with the new seeds; any score with the '
 'broadcast-fill or camera-window conditions for the new weights; PFF game 3839 with the new weights.',
]
choice = ('Grid looked at on the 22 development copies: arithmetic pool with weight 0.2-0.6, geometric pool with weight 0.3-0.6, all '
          'through the unchanged v2 decoder. Rule (written down on 14 Nov at 21:23, after the DFL rows and before the Metrica rows of the '
          're-trained weights existed): drop every setting with a development copy below -0.010; among the rest take the largest mean '
          'difference; settings within 0.001 of it count as equal and the smallest weight wins (the same weight in both pools: the '
          'larger mean). Settings without a copy below -0.010: ' + ', '.join(ok) +
          '; largest mean ' + f'{best:+.4f}' + '; within 0.001: ' + ', '.join(near) + '; chosen: ' + pool + ' pool, weight ' + str(weight) +
          '. The script compares means rounded to four decimals, as it was written; the unrounded means give the same choice: ' +
          ', '.join(f"{n} {unrounded[n]:+.6f}" for n in ok) + '.')
out = {'chosen': {'pool': pool, 'weight': weight, 'name': chosen}, 'choice': choice, 'seen': seen, 'unrounded_means': unrounded,
       'table_retrained_weights': table, 'table_committed_weights': table_his, 'diagnostic_metrica3_seed7772': diag}
json.dump(out, open(V + 'development_summary.json', 'w'), indent=1)
print(json.dumps(out['chosen']), '\n', choice)
for g in groups:
    print('\n', g)
    for n in ['tcn_alone', 'v213rule'] + GRID:
        print('  ', n.ljust(10), table[g][n])
