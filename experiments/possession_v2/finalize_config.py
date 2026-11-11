"""Write possession-v2-config.json for the selected candidate.
Usage: finalize_config.py CANDIDATE_KEY FEATURE_VERSION VERSION_STRING"""
import json, sys
from pathlib import Path
key, fv, version = sys.argv[1], int(sys.argv[2]), sys.argv[3]
W = Path('/home/claude/work')
cfg_path = Path('/home/claude/sc/possession-v2-config.json')
cfg = json.loads(cfg_path.read_text())
grid = json.loads((W / f'grid3_{key}.json').read_text())
best = max(grid, key=lambda r: (r['all'], r['macro']))
base = json.loads((W / 'base_eval.json').read_text())
def bmean(tag):
    ks = [k for k in base if k.startswith(tag + '|')]
    return round(sum(base[k]['spell_f1_mean'] for k in ks) / len(ks), 4)
cfg['version'] = version
cfg['feature_version'] = fv
cfg['decoder'] = {k: float(v) for k, v in best['prm'].items()}
if key.startswith('stack'):
    cfg['stack'] = {'step': 3, 'hyperparameters': {'max_iter': 200, 'learning_rate': 0.05, 'max_leaf_nodes': 15,
                                                   'min_samples_leaf': 400, 'l2_regularization': 1.0}}
else:
    cfg.pop('stack', None)
cfg['selection_summary'] = {
    'candidate': key,
    'validation_mean_spell_f1': float(best['all']), 'validation_dfl_spell_f1': float(best['dfl']),
    'validation_metrica_spell_f1': float(best['met']), 'validation_macro_f1': float(best['macro']),
    'selected_by': 'highest mean official spell_f1_mean over 8 validation copies (DFL J03WN1/J03WR9, '
                   'Metrica 1-2; seeds 101/102), macro_f1 tie-break; candidates and grids in possession-v2-results.json',
    'models_for_validation_trained_on': ['J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ'],
    'final_bundle_trained_on': cfg['train_fixtures'],
    'comparators_same_copies': {'organizer_baseline_smooth50': bmean('baseline50'), 'team_S001': bmean('S001')}}
cfg_path.write_text(json.dumps(cfg, indent=2) + '\n')
print(json.dumps(cfg, indent=1))
