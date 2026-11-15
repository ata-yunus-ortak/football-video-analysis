"""Stores the probabilities of both model families on the copies of the v2.13 validation (same seeds, already scored
yesterday: development data from now on). Usage: cache_old.py MATCH_INDEX [conditions]"""
import sys
import lib214 as L
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
mi = int(sys.argv[1])
conds = sys.argv[2].split(',') if len(sys.argv) > 2 else ['tactical']
if mi == 4:      # Metrica game 3, yesterday's after-decision copy
    L.cache('MET3', 33103, 8, conds, sim2_seed=63108 if 'tactical_sim2' in conds else None)
else:
    name = NAMES[mi]
    for j in (0, 1, 2, 3):
        cj = [c for c in conds if c in ('tactical',) or j < 2]
        L.cache(name, 13100 + 10 * mi + j, 2 * mi + j, [c for c in cj if c != 'tactical_sim2'])
    if 'tactical_sim2' in conds:
        L.cache(name, 13100 + 10 * mi, 2 * mi, ['tactical_sim2'], sim2_seed=63100 + mi)
print('CACHEDONE', mi, flush=True)
