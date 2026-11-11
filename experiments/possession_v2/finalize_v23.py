"""Write possession-v23-config.json from the v2.3 validation result (only after SELECT_V23)."""
import json
from pathlib import Path
W = Path('/home/claude/work'); S = Path('/home/claude/sc')
ev = json.loads((W / 'eval_v23.json').read_text())
assert ev['selected'], 'v2.3 not selected'
cfg = json.loads((S / 'possession-v2-config.json').read_text())
cfg['version'] = 'possession-v2.3'
cfg['degrade_profile'] = 'v2.3'
cfg['smooth_half'] = 2
cfg['sources'] = ['data.py', 'features.py', 'trees.py', 'decode.py', 'pipeline.py', 'bundle.py', 'run.py',
                  'stack.py', 'tags.py', 'smooth.py', 'run23.py']
cfg['decoder'] = {k: float(v) for k, v in ev['summary']['v23']['decoder'].items()}
s = ev['summary']
cfg['selection_summary'] = {
    'plan': 'possession-v23-plan.json',
    'validation_24_copies_spell_f1': {'v2.1': round(s['v21']['all24'], 4), 'v2.3': round(s['v23']['all24'], 4)},
    'V_orig_spell_f1': {'v2.1': round(s['v21']['orig'], 4), 'v2.3': round(s['v23']['orig'], 4)},
    'V_ext_ball_spell_f1': {'v2.1': round(s['v21']['ext_ball'], 4), 'v2.3': round(s['v23']['ext_ball'], 4)},
    'V_ext_players_spell_f1': {'v2.1': round(s['v21']['ext_players'], 4), 'v2.3': round(s['v23']['ext_players'], 4)},
    'gates': ev['gates'],
    'models_for_validation_trained_on': ['J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ'],
    'final_bundle_trained_on': cfg['train_fixtures']}
(S / 'possession-v23-config.json').write_text(json.dumps(cfg, indent=2) + '\n')
print(json.dumps(cfg, indent=1))
