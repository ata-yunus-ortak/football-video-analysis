"""Smoke test of exp_v211.py on a TRAINING match (in-sample numbers, meaningless): does the code run, how much memory?"""
import sys, json, resource, time
sys.path.insert(0, '/home/claude/work')
import exp_v211 as E
E.CONDITIONS = tuple(c for c in E.CONDITIONS if c[0] in ('view42_none', 'gk_part'))
res = {'rows': []}
t0 = time.time()
E.rows_for('J03WOH', 99999, 0, res, '/home/claude/work/gk2/smoke_v211.json', set())
print('peak RSS GB', round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2), 'seconds', round(time.time() - t0))
print(json.dumps(res['rows'][-1], indent=1)[:1500])
