"""Write possession-v22-config.json from the v2.2 validation result (only after SELECT_V22)."""
import json
from pathlib import Path
W = Path('/home/claude/work'); S = Path('/home/claude/sc')
ev = json.loads((W / 'eval_v22.json').read_text())
assert ev['selected'], 'v2.2 not selected'
cfg = json.loads((S / 'possession-v2-config.json').read_text())
cfg['version'] = 'possession-v2.2'
cfg['degrade_profile'] = 'v2.2'
cfg['decoder'] = {k: float(v) for k, v in ev['summary']['v22']['decoder'].items()}
s = ev['summary']
cfg['selection_summary'] = {
    'plan': 'possession-v22-plan.json',
    'validation_16_copies_spell_f1': {'v2.1': round(s['v21']['all16'], 4), 'v2.2': round(s['v22']['all16'], 4)},
    'V_orig_spell_f1': {'v2.1': round(s['v21']['orig'], 4), 'v2.2': round(s['v22']['orig'], 4)},
    'V_ext_spell_f1': {'v2.1': round(s['v21']['ext'], 4), 'v2.2': round(s['v22']['ext'], 4)},
    'gates': ev['gates'],
    'models_for_validation_trained_on': ['J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ'],
    'final_bundle_trained_on': cfg['train_fixtures']}
(S / 'possession-v22-config.json').write_text(json.dumps(cfg, indent=2) + '\n')
print(json.dumps(cfg, indent=1))
