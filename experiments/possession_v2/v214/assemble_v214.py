"""Apply the gates of possession-v214-plan.json once to all rows of exp_v214_{0,1,2,3}.json and write
possession-v214-results.json (the Metrica game 3 rows are added only if exp_v214_reserved.json exists, which is run
after the decision; likewise pff_v214.json). The gates are evaluated on unrounded values.
Usage: /usr/bin/python3 assemble_v214.py"""
import json, os, hashlib, subprocess
import numpy as np

V = '/home/claude/work/v214/'
REPO = '/home/claude/sc/'
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
DFL, MET = NAMES[:2], NAMES[2:]
SYSTEMS = ('v2_11', 'fused', 'tcn_alone')


def rows():
    out = []
    for part in range(4):
        out += json.load(open(f'{V}exp_v214_{part}.json'))['rows']
    return out


def sel(R, cond, names=NAMES):
    return [r for r in R if r['condition'] == cond and r['copy'].split('|')[0] in names]


def mean(xs):
    return float(np.mean(xs)) if xs else None


def r4(x):
    return None if x is None else round(x, 4)


def gate_values(rs):
    """Unrounded inputs of the gates."""
    return {'diff_spell_f1_mean': mean([r['diff_spell_f1'] for r in rs]),
            'diff_macro_f1_mean': mean([r['diff_macro_f1'] for r in rs]),
            'diff_spell_f1_min': float(min(r['diff_spell_f1'] for r in rs)) if rs else None}


def summary(rs):
    """Rounded, for display only."""
    gv = gate_values(rs)
    s = {'n': len(rs), 'diff_spell_f1_mean': r4(gv['diff_spell_f1_mean']), 'diff_macro_f1_mean': r4(gv['diff_macro_f1_mean']),
         'diff_spell_f1_min': r4(gv['diff_spell_f1_min']),
         'copies_better': sum(r['diff_spell_f1'] > 0 for r in rs), 'copies_worse': sum(r['diff_spell_f1'] < 0 for r in rs),
         'paths': {p: sum(r['path'] == p for r in rs) for p in ('v2.1', 'v2.3')},
         'copies_not_pooled': sum(not r['fused_on_this_path'] for r in rs),
         'frames_changed_per_copy': r4(mean([r['frames_changed'] for r in rs]))}
    for tag in SYSTEMS:
        g2, g1 = sum(r[tag]['gt_spells_under_2s'] for r in rs), sum(r[tag]['gt_spells_under_1s'] for r in rs)
        s[tag] = {'spell_f1': r4(mean([r[tag]['spell_f1'] for r in rs])), 'macro_f1': r4(mean([r[tag]['macro_f1'] for r in rs])),
                  'recall_under_2s_iou03': round(sum(r[tag]['found_under_2s_iou03'] for r in rs) / max(g2, 1), 4),
                  'recall_under_1s_iou03': round(sum(r[tag]['found_under_1s_iou03'] for r in rs) / max(g1, 1), 4),
                  'trans_f1_12': r4(mean([r[tag]['trans_f1_12'] for r in rs])),
                  'trans_f1_25': r4(mean([r[tag]['trans_f1_25'] for r in rs])),
                  'pred_spells_per_copy': r4(mean([r[tag]['n_pred_spells'] for r in rs]))}
    if rs:
        s['gt_spells_per_copy'] = r4(mean([r['v2_11']['n_gt_spells'] for r in rs]))
    return s


def gates(R):
    """(display summary, unrounded gate inputs, gate verdicts) of the rows of parts 0-3."""
    tac = sel(R, 'tactical')
    assert len(tac) == 16 and len(sel(R, 'fill_good')) == 8 and len(sel(R, 'fill_medium')) == 8 and len(sel(R, 'view42')) == 8 \
        and len(sel(R, 'tactical_sim2')) == 4, 'incomplete'
    assert len(sel(R, 'tactical', DFL)) == 8 and len(sel(R, 'tactical', MET)) == 8, 'sources'
    assert len({(r['copy'], r['condition']) for r in R}) == len(R), 'duplicate rows'
    S = {'tactical': summary(tac), 'tactical_DFL': summary(sel(R, 'tactical', DFL)), 'tactical_Metrica': summary(sel(R, 'tactical', MET)),
         'fill_good': summary(sel(R, 'fill_good')), 'fill_medium': summary(sel(R, 'fill_medium')), 'view42': summary(sel(R, 'view42')),
         'tactical_sim2': summary(sel(R, 'tactical_sim2')),
         'fill_good_DFL': summary(sel(R, 'fill_good', DFL)), 'fill_good_Metrica': summary(sel(R, 'fill_good', MET)),
         'fill_medium_DFL': summary(sel(R, 'fill_medium', DFL)), 'fill_medium_Metrica': summary(sel(R, 'fill_medium', MET))}
    for c in ('fill_good', 'fill_medium'):
        S[c]['gate_opened'] = sum(bool(r['gate']['used']) for r in sel(R, c))
    GV = {k: gate_values(sel(R, *a)) for k, a in (('tactical', ('tactical',)), ('tactical_DFL', ('tactical', DFL)),
                                                  ('tactical_Metrica', ('tactical', MET)), ('fill_good', ('fill_good',)),
                                                  ('fill_medium', ('fill_medium',)), ('tactical_sim2', ('tactical_sim2',)))}
    G = {
     'G1 gain': GV['tactical']['diff_spell_f1_mean'] >= 0.008,
     'G2 gain on provider flags': GV['tactical_DFL']['diff_spell_f1_mean'] >= 0.008,
     'G3 no harm on event proxies': GV['tactical_Metrica']['diff_spell_f1_mean'] >= -0.002,
     'G4 no bad copy': GV['tactical']['diff_spell_f1_min'] >= -0.010,
     'G5 macroF1': GV['tactical']['diff_macro_f1_mean'] >= -0.003,
     'G6 broadcast fill': GV['fill_good']['diff_spell_f1_mean'] >= 0.0 and GV['fill_medium']['diff_spell_f1_mean'] >= 0.0,
     'G7 other simulator': GV['tactical_sim2']['diff_spell_f1_mean'] >= 0.0,
    }
    return S, GV, {k: bool(v) for k, v in G.items()}


def main():
    R = rows()
    S, GV, G = gates(R)
    plan = json.load(open(REPO + 'possession-v214-plan.json'))
    parts = [json.load(open(f'{V}exp_v214_{p}.json')) for p in range(4)]
    assert all(p['sha256'] == parts[0]['sha256'] and p['fusion'] == parts[0]['fusion'] for p in parts), 'parts differ in code or weights'
    for f in ('exp_v214.py', 'exp_v213.py', 'fuse2.py'):
        assert parts[0]['sha256'][f] == plan['hashes']['validation_scripts'][f], f + ' differs from the registered one'
    assert parts[0]['sha256']['weights'] == plan['hashes']['tcn_weights_sha256'], 'weights differ from the registered ones'
    assert parts[0]['fusion']['pool'] == plan['fusion_rule_fixed_before_any_score']['pool'] and parts[0]['fusion']['weight'] == plan['fusion_rule_fixed_before_any_score']['weight'], 'pooling differs from the registered one'
    assert sha(V + 'assemble_v214.py') == plan['hashes']['validation_scripts']['assemble_v214.py'], 'assembler differs from the registered one'
    out = {'version': 'possession-v2.14-results', 'written_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
           'plan_sha256': sha(REPO + 'possession-v214-plan.json'), 'plan_registered_at': plan['registered_at'],
           'summary': S, 'gate_values_unrounded': GV, 'gates': G, 'selected': all(G.values()),
           'decision': ('all seven gates pass: the pooled system is selected for integration as possession-v2.14 (release only '
                        'after the integration checks of the plan)') if all(G.values())
                       else 'a gate failed: possession-v2.11k stays the release; the pooled system is not used',
           'environment': parts[0]['environment'], 'fusion': parts[0]['fusion'], 'sha256': parts[0]['sha256'],
           'rows': R, 'provided_fixture_used': False}
    if os.path.exists(V + 'exp_v214_reserved.json'):
        rr = json.load(open(V + 'exp_v214_reserved.json'))['rows']
        out['metrica_game3_after_decision'] = {'note': 'one new copy (seed 36103) and one copy of the teammate\'s simulator, run once '
                                                       'after the decision; not a gate; game 3 was used in the development of this '
                                                       'candidate (diagnostics and the choice of the pooling)', 'rows': rr}
    if os.path.exists(V + 'pff_v214.json'):
        out['pff_game_3839_after_decision'] = json.load(open(V + 'pff_v214.json'))
    json.dump(out, open(REPO + 'possession-v214-results.json', 'w'), indent=1)
    print(json.dumps({'summary': {k: {kk: v[kk] for kk in ('n', 'diff_spell_f1_mean', 'diff_macro_f1_mean', 'diff_spell_f1_min',
                                                         'copies_better', 'copies_worse')} for k, v in S.items()},
                      'gates': G, 'selected': out['selected']}, indent=1))


if __name__ == '__main__':
    main()
