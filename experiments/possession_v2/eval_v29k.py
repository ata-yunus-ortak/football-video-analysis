"""Apply the registered rule of possession-v29-amendment-plan.json (run once, after exp_v29k.py has finished).

Evaluation set per regime: the 8 replacement copies (kind 'k002', exp_v29_k002.json) plus the 8 copies with degrade
seeds 4500-4531 (kind 'ext_players') already in possession-v29-results.json. Gates unchanged from possession-v29-plan.json.
Writes possession-v29-amendment-results.json next to the plan; the original plan and results files are not touched.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import numpy as np

SC, WORK = Path('/home/claude/sc'), Path('/home/claude/work')
REG = ('good', 'medium', 'bad')
SYS = ('v2_4', 'v2_5b', 'v2_9')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def summary(rows):
    out = {}
    for reg in REG:
        rr = [r for r in rows if r['regime'] == reg]
        s = {k: round(float(np.mean([r[k][0] for r in rr])), 4) for k in SYS}
        diff = np.array([r['v2_9'][0] - r['v2_5b'][0] for r in rr])
        s.update(n=len(rr),
                 gate_open={k: int(sum(bool(r[k + '_info']['gate'].get('used')) for r in rr)) for k in ('v2_5b', 'v2_9')},
                 v29_higher=int((diff > 1e-12).sum()), v29_equal=int((np.abs(diff) <= 1e-12).sum()), v29_lower=int((diff < -1e-12).sum()),
                 worst_diff=round(float(diff.min()), 4), best_diff=round(float(diff.max()), 4),
                 mean_diff_vs_v2_5b=round(float(diff.mean()), 4),
                 macro={k: round(float(np.mean([r[k][1] for r in rr])), 4) for k in SYS})
        out[reg] = s
    return out


def gates(rows):
    m = {reg: {k: float(np.mean([r[k][0] for r in rows if r['regime'] == reg])) for k in SYS} for reg in REG}
    gain = float(np.mean([m[reg]['v2_9'] - m[reg]['v2_5b'] for reg in REG]))
    return {'medium: v2.9 >= v2.5b + 0.010': bool(m['medium']['v2_9'] >= m['medium']['v2_5b'] + 0.010),
            'good: v2.9 >= v2.5b - 0.003': bool(m['good']['v2_9'] >= m['good']['v2_5b'] - 0.003),
            'bad: v2.9 >= v2.4 - 0.003': bool(m['bad']['v2_9'] >= m['bad']['v2_4'] - 0.003),
            'mean of regimes: v2.9 >= v2.5b + 0.005': bool(gain >= 0.005)}, round(gain, 4)


def main():
    plan_path, old_path = SC / 'possession-v29-amendment-plan.json', SC / 'possession-v29-results.json'
    out_path = SC / 'possession-v29-amendment-results.json'
    if out_path.exists():
        sys.exit('the amendment was already evaluated (run once)')
    plan = json.loads(plan_path.read_text())
    assert sha(SC / 'possession-v29-plan.json') == plan['sha256']['possession-v29-plan.json']
    assert sha(old_path) == plan['sha256']['possession-v29-results.json_before_amendment']
    assert sha(WORK / 'exp_v29k.py') == plan['sha256']['work/exp_v29k.py']
    for name in ('possession/register.py', 'possession/fusion.py'):
        assert sha(SC / name) == plan['sha256'][name], name
    new = json.loads((WORK / 'exp_v29_k002.json').read_text())
    new = new['rows'] if isinstance(new, dict) else new
    new = [r for r in new if r['kind'] == 'k002']
    old = [r for r in json.loads(old_path.read_text())['rows'] if r['kind'] == 'ext_players']
    copies = sorted({r['copy'] for r in new})
    want = sorted(f'{m}|{7100 + 10 * i + j}|k002' for i, m in enumerate(('J03WN1', 'J03WR9', 'MET1', 'MET2')) for j in (0, 1))
    assert copies == want, copies
    assert len(new) == 24 and len(old) == 24 and all(sum(r['regime'] == g for r in new) == 8 for g in REG)
    both = new + old
    g, gain = gates(both)
    g8, gain8 = gates(new)
    passed = all(g.values())
    now = subprocess.run(['date', '-Iseconds'], capture_output=True, text=True).stdout.strip()
    res = {'version': 'possession-v2.9 validation amendment results', 'written_at': now, 'provided_fixture_used': False,
           'plan': 'possession-v29-amendment-plan.json', 'plan_sha256': sha(plan_path),
           'evaluation_set': '8 replacement copies (degrade seeds 7100-7131, v2.1 corruption) + 8 copies with degrade seeds 4500-4531 '
                             '(rows unchanged from possession-v29-results.json), x 3 regimes of the warp simulator',
           'summary': summary(both), 'mean_regime_gain_over_v2_5b': gain, 'gates': g,
           'decision': ('possession-v2.9 stays the selected release (all four registered gates passed on the amended evaluation set)'
                        if passed else
                        'possession-v2.9 is WITHDRAWN (a registered gate failed on the amended evaluation set); the submission system is '
                        'possession-v2.5c (python -m possession.run25c, possession-v25c-release.json)'),
           'reported_alongside': {
               'replacement_copies_alone': {'summary': summary(new), 'mean_regime_gain_over_v2_5b': gain8, 'gates_for_information_only': g8},
               'original_16_copies_as_run': 'possession-v29-results.json (unchanged): good 0.6832 -> 0.6812, medium 0.6474 -> 0.6784, '
                                            'bad 0.6474 -> 0.6474, mean regime gain +0.0097, all four gates passed'},
           'limits': plan['limits'],
           'rows_replacement': new,
           'rows_kept': 'the 24 rows with kind ext_players in possession-v29-results.json',
           'sha256': {'work/exp_v29_k002.json': sha(WORK / 'exp_v29_k002.json'), 'work/exp_v29k.py': sha(WORK / 'exp_v29k.py'),
                      'work/eval_v29k.py': sha(Path(__file__)), 'possession-v29-results.json': sha(old_path)}}
    out_path.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ('summary', 'mean_regime_gain_over_v2_5b', 'gates', 'decision')}, indent=1))
    print(json.dumps(res['reported_alongside']['replacement_copies_alone'], indent=1))


if __name__ == '__main__':
    main()
