"""Write possession-v23-config.json for the v2.3 component of the v2.4 release (only after SELECT_V24)."""
import json
from pathlib import Path
W = Path('/home/claude/work'); S = Path('/home/claude/sc')
ev = json.loads((W / 'eval_v24.json').read_text())
assert ev['selected'], 'v2.4 not selected'
ev23 = json.loads((W / 'eval_v23.json').read_text())
cfg = json.loads((S / 'possession-v2-config.json').read_text())
cfg['version'] = 'possession-v2.3'
cfg['degrade_profile'] = 'v2.3'
cfg['smooth_half'] = 2
cfg['sources'] = ['data.py', 'features.py', 'trees.py', 'decode.py', 'pipeline.py', 'bundle.py', 'run.py',
                  'stack.py', 'tags.py', 'smooth.py', 'noise.py', 'run24.py']
cfg['decoder'] = {k: float(v) for k, v in ev23['summary']['v23']['decoder'].items()}
s = ev['summary']
cfg['selection_summary'] = {
    'role': 'v2.3 path of the noise-gated possession-v2.4 release (used only when the measured input noise exceeds 0.30 m)',
    'plans': ['possession-v23-plan.json', 'possession-v24-plan.json'],
    'v2_3_decoder_selected_on': '24 v2.3 validation copies (possession-v23-results.json)',
    'v2_4_fresh_copies_spell_f1': {'v2.1': round(s['v2_1']['all24'], 4), 'v2.4': round(s['v2_4']['all24'], 4)},
    'v2_4_fresh_orig_spell_f1': {'v2.1': round(s['v2_1']['orig'], 4), 'v2.4': round(s['v2_4']['orig'], 4)},
    'gates': ev['gates'],
    'models_for_validation_trained_on': ['J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ'],
    'final_bundle_trained_on': cfg['train_fixtures']}
(S / 'possession-v23-config.json').write_text(json.dumps(cfg, indent=2) + '\n')
print(json.dumps(cfg, indent=1))
