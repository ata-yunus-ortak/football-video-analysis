"""Assemble possession-v2-results.json (aggregate external numbers only)."""
import json, sys, os, numpy as np
W = '/home/claude/work/'
out = {'version': sys.argv[2] if len(sys.argv) > 2 else 'possession-v2.0', 'provided_fixture_used': False,
       'note': 'Agreement with other providers labels on corrupted external copies; not competition scores.'}
base = json.load(open(W + 'base_eval.json'))
def agg_base(tag):
    ks = [k for k in base if k.startswith(tag + '|')]
    f = lambda kk, m: float(np.mean([base[k][m] for k in kk]))
    d = [k for k in ks if k.split('|')[1].startswith('J03')]; mt = [k for k in ks if k.split('|')[1].startswith('MET')]
    return {'spell_f1_all': f(ks, 'spell_f1_mean'), 'spell_f1_dfl': f(d, 'spell_f1_mean'), 'spell_f1_metrica': f(mt, 'spell_f1_mean'),
            'macro_f1_all': f(ks, 'macro_f1'), 'n_pred_spells': f(ks, 'n_pred_spells'), 'n_gt_spells': f(ks, 'n_gt_spells')}
val = {'baseline50': agg_base('baseline50'), 'S001': agg_base('S001')}
key = sys.argv[3] if len(sys.argv) > 3 else 'models_v2_f2'
sel = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, W)
from harness import load, DFL_VAL, MET_VAL
from possession.decode import emissions, decode_blocks
from possession.evaluate import score
def eval_probs(fn):
    rs = {}
    for name in DFL_VAL + MET_VAL:
        m, lab = load(name)
        for seed in (101, 102):
            z = np.load(f'{W}cache/probs_{key}_{name}_{seed}.npz')
            rs[(name, seed)] = score(lab, fn(z, m), m['period'])
    ks = list(rs); d = [k for k in ks if k[0].startswith('J03')]; mt = [k for k in ks if k[0].startswith('MET')]
    f = lambda kk, m_: float(np.mean([rs[k][m_] for k in kk]))
    return {'spell_f1_all': f(ks, 'spell_f1_mean'), 'spell_f1_dfl': f(d, 'spell_f1_mean'), 'spell_f1_metrica': f(mt, 'spell_f1_mean'),
            'macro_f1_all': f(ks, 'macro_f1'), 'alive_dead_f1': f(ks, 'alive_dead_f1'), 'team_acc_both_alive': f(ks, 'team_acc_both_alive'),
            'f1_D': f(ks, 'f1_D'), 'n_pred_spells': f(ks, 'n_pred_spells'), 'n_gt_spells': f(ks, 'n_gt_spells'),
            'per_copy': {f'{k[0]}|{k[1]}': {'spell_f1': rs[k]['spell_f1_mean'], 'macro_f1': rs[k]['macro_f1']} for k in ks}}
val['v2_argmax'] = eval_probs(lambda z, m: np.where(z['pd'] > .5, 'D', np.where(z['ph'] > .5, 'H', 'A')))
if sel:
    val['v2_selected'] = eval_probs(lambda z, m: decode_blocks(emissions(z['pd'], z['ph']), m['period'], sel))
    val['v2_selected']['decoder'] = sel
out['validation'] = val
for fn, k in (('stress_v2.json', 'stress_test_stage1_candidate'), ('stress_final.json', 'stress_test_final'),
              ('stress2_final.json', 'stress_test_tracker_artefacts'), ('reserved_test_v2.json', 'reserved_test'),
              ('diagnostics_final.json', 'diagnostics')):
    if os.path.exists(W + fn):
        out[k] = json.load(open(W + fn))
CAND = {'models_v2_f2': 'stage-1 GBDT, feature set v2', 'stack_v2_f2': 'stage-1 v2 + stage-2 temporal stacking',
        'models_v3_f3': 'stage-1 GBDT, feature set v3 (1 s tempo speeds)',
        'stack_v3_f3': 'stage-1 v3 + stage-2 temporal stacking'}
out['candidates'] = {}
for ck, desc in CAND.items():
    if os.path.exists(W + 'grid3_' + ck + '.json'):
        g = json.load(open(W + 'grid3_' + ck + '.json'))
        b = max(g, key=lambda r: (r['all'], r['macro']))
        out['candidates'][ck] = {'description': desc, 'best_decoder': b['prm'], 'spell_f1_all': b['all'],
                                 'spell_f1_dfl': b['dfl'], 'spell_f1_metrica': b['met'], 'macro_f1': b['macro'],
                                 'grid_points': len(g), 'selected': ck == key}
if os.path.exists(W + 'grid3_' + key + '.json'):
    out['decoder_grid'] = [{k: r[k] for k in ('all', 'dfl', 'met', 'macro', 'spells', 'prm')} for r in json.load(open(W + 'grid3_' + key + '.json'))]
from possession.bundle import load as load_bundle
b = load_bundle('/home/claude/sc/models/possession-v2.npz')
out['final_bundle'] = {'path': 'models/possession-v2.npz', 'sha256': b['sha256'], 'version': b['card']['version'],
                       'trained_on': b['card']['train_fixtures'], 'rows': b['card']['rows'],
                       'decoder': b['decoder'], 'stack': b['card'].get('stack'),
                       'feature_version': b['card']['feature_version'],
                       'sklearn_version_used_for_training': b['card']['sklearn_version_used_for_training'],
                       'note': 'validation numbers above come from the same recipe trained on the four training matches; '
                               'the final bundle adds the two DFL validation matches, so only the reserved test measures it'}
json.dump(out, open(sys.argv[1], 'w'), indent=1, default=float)
print('written', sys.argv[1])
