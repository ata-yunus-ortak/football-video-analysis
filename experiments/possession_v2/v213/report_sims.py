"""Reporting only: what the copies of the two simulators look like and how the three systems score on them."""
import json
import numpy as np
R = json.load(open('/home/claude/sc/possession-v213-results.json'))['rows']
for cond in ('tactical', 'tactical_sim2'):
    rs = [r for r in R if r['condition'] == cond]
    for src, names in (('DFL', ('J03WN1', 'J03WR9')), ('Metrica', ('MET1', 'MET2')), ('all', ('J03WN1', 'J03WR9', 'MET1', 'MET2'))):
        q = [r for r in rs if r['copy'].split('|')[0] in names]
        m = lambda f: round(float(np.mean([f(r) for r in q])), 4)
        print(cond, src, 'n', len(q), 'ball noise m', m(lambda r: r['noise_m']['ball_m']), 'player noise m', m(lambda r: r['noise_m']['players_m']),
              'ball visible', m(lambda r: r['ball_visible_in_play']), '| v2.11', m(lambda r: r['v2_11']['spell_f1']), 'fused', m(lambda r: r['fused']['spell_f1']),
              'tcn', m(lambda r: r['tcn_alone']['spell_f1']), 'diff', m(lambda r: r['diff_spell_f1']),
              'tcn>=v2 on', sum(r['tcn_alone']['spell_f1'] >= r['v2_11']['spell_f1'] for r in q), 'fused best on', sum(r['fused']['spell_f1'] > max(r['v2_11']['spell_f1'], r['tcn_alone']['spell_f1']) for r in q))
rs = [r for r in R if r['condition'] == 'tactical']
print('ball noise range our copies', min(r['noise_m']['ball_m'] for r in rs), max(r['noise_m']['ball_m'] for r in rs), 'players', min(r['noise_m']['players_m'] for r in rs), max(r['noise_m']['players_m'] for r in rs))
rs2 = [r for r in R if r['condition'] == 'tactical_sim2']
print('ball noise range sim2', min(r['noise_m']['ball_m'] for r in rs2), max(r['noise_m']['ball_m'] for r in rs2), 'players', min(r['noise_m']['players_m'] for r in rs2), max(r['noise_m']['players_m'] for r in rs2))
# does the difference go with the measured noise on our own 16 copies? (reporting only)
x = np.array([r['noise_m']['ball_m'] for r in rs]); y = np.array([r['diff_spell_f1'] for r in rs]); v = np.array([r['ball_visible_in_play'] for r in rs])
print('corr(diff, ball noise) on our 16 copies', round(float(np.corrcoef(x, y)[0, 1]), 3), 'corr(diff, ball visible)', round(float(np.corrcoef(v, y)[0, 1]), 3))
print(sorted((round(float(a), 3), round(float(b), 4)) for a, b in zip(x, y)))
