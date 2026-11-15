"""Apply the gates of possession-v212-plan.json once to all rows of exp_v212_{0,1,2,3}.json and write
possession-v212-results.json (reporting of the reserved Metrica game 3 is added only if exp_v212_reserved.json exists,
which is run after the decision). Usage: /usr/bin/python3 assemble_v212.py"""
import json, os, hashlib, subprocess
import numpy as np

V = '/home/claude/work/v212/'
REPO = '/home/claude/sc/'
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
DFL, MET = NAMES[:2], NAMES[2:]


def rows():
    out = []
    for part in range(4):
        out += json.load(open(f'{V}exp_v212_{part}.json'))['rows']
    return out


def sel(R, cond, names=NAMES):
    return [r for r in R if r['condition'] == cond and r['copy'].split('|')[0] in names]


def mean(xs):
    return float(np.mean(xs)) if xs else None


def r4(x):
    return None if x is None else round(x, 4)


def gate_values(rs):
    """Unrounded inputs of the gates (audit finding B1: gates are applied to unrounded means and minimum)."""
    return {'diff_spell_f1_mean': mean([r['diff_spell_f1'] for r in rs]),
            'diff_macro_f1_mean': mean([r['diff_macro_f1'] for r in rs]),
            'diff_spell_f1_min': float(min(r['diff_spell_f1'] for r in rs)) if rs else None}


def summary(rs):
    """Rounded, for display only."""
    gv = gate_values(rs)
    s = {'n': len(rs), 'diff_spell_f1_mean': r4(gv['diff_spell_f1_mean']), 'diff_macro_f1_mean': r4(gv['diff_macro_f1_mean']),
         'diff_spell_f1_min': r4(gv['diff_spell_f1_min']),
         'copies_better': sum(r['diff_spell_f1'] > 0 for r in rs), 'copies_worse': sum(r['diff_spell_f1'] < 0 for r in rs),
         'paths': {p: sum(r['path'] == p for r in rs) for p in ('v2.1', 'v2.3')}}
    v1 = [r for r in rs if isinstance(r['v2_12'], dict)]
    for tag in ('v2_11', 'v2_12'):
        s[tag] = {'spell_f1': r4(mean([r[tag]['spell_f1'] if isinstance(r[tag], dict) else r['v2_11']['spell_f1'] for r in rs])),
                  'macro_f1': r4(mean([r[tag]['macro_f1'] if isinstance(r[tag], dict) else r['v2_11']['macro_f1'] for r in rs]))}
        if v1:
            g = sum(r[tag]['gt_spells_under_2s'] for r in v1)
            s[tag]['recall_under_2s_iou03'] = round(sum(r[tag]['found_under_2s_iou03'] for r in v1) / max(g, 1), 4)
            g1 = sum(r[tag]['gt_spells_under_1s'] for r in v1)
            s[tag]['recall_under_1s_iou03'] = round(sum(r[tag]['found_under_1s_iou03'] for r in v1) / max(g1, 1), 4)
            s[tag]['trans_f1_12'] = r4(mean([r[tag]['trans_f1_12'] for r in v1]))
            s[tag]['trans_f1_25'] = r4(mean([r[tag]['trans_f1_25'] for r in v1]))
            s[tag]['pred_spells_per_copy'] = r4(mean([r[tag]['n_pred_spells'] for r in v1]))
    if v1:
        s['gt_spells_per_copy'] = r4(mean([r['v2_11']['n_gt_spells'] for r in v1]))
    return s


def main():
    R = rows()
    tac = sel(R, 'tactical')
    assert len(tac) == 16 and len(sel(R, 'fill_good')) == 8 and len(sel(R, 'fill_medium')) == 8 and len(sel(R, 'view42')) == 8, 'incomplete'
    S = {'tactical': summary(tac), 'tactical_DFL': summary(sel(R, 'tactical', DFL)), 'tactical_Metrica': summary(sel(R, 'tactical', MET)),
         'fill_good': summary(sel(R, 'fill_good')), 'fill_medium': summary(sel(R, 'fill_medium')), 'view42': summary(sel(R, 'view42'))}
    for c in ('fill_good', 'fill_medium'):
        S[c]['gate_opened'] = sum(bool(r['gate']['used']) for r in sel(R, c))
    GV = {k: gate_values(sel(R, *a)) for k, a in (('tactical', ('tactical',)), ('tactical_DFL', ('tactical', DFL)),
                                                  ('tactical_Metrica', ('tactical', MET)), ('fill_good', ('fill_good',)),
                                                  ('fill_medium', ('fill_medium',)))}
    G = {
     'G1 gain': GV['tactical']['diff_spell_f1_mean'] >= 0.008,
     'G2 gain on provider flags': GV['tactical_DFL']['diff_spell_f1_mean'] >= 0.008,
     'G3 no harm on event proxies': GV['tactical_Metrica']['diff_spell_f1_mean'] >= -0.002,
     'G4 no bad copy': GV['tactical']['diff_spell_f1_min'] >= -0.010,
     'G5 macroF1': GV['tactical']['diff_macro_f1_mean'] >= -0.003,
     'G6 broadcast fill': GV['fill_good']['diff_spell_f1_mean'] >= 0.0 and GV['fill_medium']['diff_spell_f1_mean'] >= 0.0,
    }
    plan = json.load(open(REPO + 'possession-v212-plan.json'))
    out = {'version': 'possession-v2.12-results', 'written_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
           'plan_sha256': sha(REPO + 'possession-v212-plan.json'), 'plan_registered_at': plan['registered_at'],
           'summary': S, 'gate_values_unrounded': GV, 'gates': G, 'selected': all(G.values()),
           'decision': ('all six gates pass: possession-v2.12 is selected for integration (release only after the integration '
                        'checks of the plan)') if all(G.values()) else 'a gate failed: possession-v2.11 stays the release',
           'rows': R, 'scripts_sha256': {n: sha(V + n) for n in ('exp_v212.py', 'assemble_v212.py', 'train_val.py')},
           'provided_fixture_used': False}
    if os.path.exists(V + 'exp_v212_reserved.json'):
        rr = json.load(open(V + 'exp_v212_reserved.json'))['rows']
        out['reserved_metrica_game3_after_decision'] = {'note': 'one new copy (seed 32103), run once after the decision; not a gate',
                                                        'rows': rr}
    json.dump(out, open(REPO + 'possession-v212-results.json', 'w'), indent=1)
    print(json.dumps({'summary': {k: {kk: v[kk] for kk in ('n', 'diff_spell_f1_mean', 'diff_macro_f1_mean', 'diff_spell_f1_min',
                                                         'copies_better', 'copies_worse')} for k, v in S.items()},
                      'gates': G, 'selected': out['selected']}, indent=1))


if __name__ == '__main__':
    main()
