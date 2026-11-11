"""Write possession-v25b-results.json from exp_v25b.json."""
import json, hashlib, subprocess
from pathlib import Path
S = Path('/home/claude/sc'); W = Path('/home/claude/work')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
d = json.loads((W / 'exp_v25b.json').read_text())
r4 = lambda x: round(float(x), 4)
summ = {}
for k, v in d['summary'].items():
    summ[k] = {kk: (r4(vv) if isinstance(vv, float) else vv) for kk, vv in v.items()}
lag_err = []
for r in d['rows']:
    if r['v2_5b_info']['mode'] == 'clock':
        rep = {h['period']: h for h in r['clock']['report']['halves']}
        for h, true in r['clock']['true_lags'].items():
            if true is not None and rep.get(int(h), {}).get('lag') is not None:
                lag_err.append(abs(rep[int(h)]['lag'] - true))
out = {'version': 'possession-v2.5b experiment (clock-anchored broadcast alignment)', 'provided_fixture_used': False,
       'note': "Simulated broadcast streams and simulated clock readings from external matches; agreement with other providers' labels, not a competition score.",
       'written_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
       'plan_sha256': sha(S / 'possession-v25b-plan.json'),
       'code_sha256': {f: sha(S / 'possession' / f) for f in ('clocksync.py', 'fusion.py', 'broadcast.py')},
       'summary': summ, 'gates': d['gates'], 'selected': d['selected'],
       'clock_lag_error_frames': {'n_halves': len(lag_err), 'median': r4(sorted(lag_err)[len(lag_err) // 2]) if lag_err else None,
                                  'max': max(lag_err) if lag_err else None},
       'per_copy': [{'copy': r['copy'], 'regime': r['regime'], 'path': r['path'], 'v2_4': r['v2_4'], 'v2_5': r['v2_5'], 'v2_5b': r['v2_5b'],
                     'v2_5_alignment': {k: r['v2_5_info'][k] for k in ('mode', 'accepted_fraction', 'alignment_precision')},
                     'v2_5b_alignment': {k: r['v2_5b_info'][k] for k in ('mode', 'accepted_fraction', 'alignment_precision')},
                     'gate_used': [r['v2_5_info']['gate']['used'], r['v2_5b_info']['gate']['used']],
                     'clock_p_read': r['clock']['p_read']} for r in d['rows']],
       'decision': ('v2.5b selected: the clock-anchored alignment is part of the release (with the tracking-only alignment as fallback)'
                    if d['selected'] else 'v2.5b NOT selected: the release uses the tracking-only alignment of v2.5')}
(S / 'possession-v25b-results.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: out[k] for k in ('selected', 'decision', 'clock_lag_error_frames')}))
