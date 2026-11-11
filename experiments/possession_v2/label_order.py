"""K005: do the Metrica proxy labels depend on how ties in 'Start Frame' are ordered? metrica_labels.labels_from_events
sorted the events with the default (unstable) sort until 11 Nov 2026. For each sample game: label counts, a hash and the
number of possessions (as the scorer counts them on the play blocks) with the old default sort ('quicksort') and with
the file order among ties ('stable'), in the environment that runs this script.
Usage: label_order.py OUT_JSON"""
import hashlib, json, sys, platform
import numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
import metrica_labels as ML
from harness import MET, read_metrica_csv
from possession.data import read_epts
from possession.evaluate import score


def labels(ev, n, kind):
    orig = pd.DataFrame.sort_values
    pd.DataFrame.sort_values = lambda self, by, **kw: orig(self, by, **dict(kw, kind=kind))
    try:
        return ML.labels_from_events(ev, n)[0]
    finally:
        pd.DataFrame.sort_values = orig


games = {}
for g in ('1', '2'):
    base = f'{MET}Sample_Game_{g}/Sample_Game_{g}_'
    m = read_metrica_csv(base + 'RawTrackingData_Home_Team.csv', base + 'RawTrackingData_Away_Team.csv')
    games['MET' + g] = (pd.read_csv(base + 'RawEventsData.csv'), m['period'])
m3, info = read_epts('/home/claude/ext/sd/data/Sample_Game_3/Sample_Game_3_metadata.xml', '/home/claude/ext/sd/data/Sample_Game_3/Sample_Game_3_tracking.txt')
p = info['provider_parameters']
per = np.zeros(len(m3['ball']), np.int8)
a1, b1, a2, b2 = (int(p[k]) for k in ('first_half_start', 'first_half_end', 'second_half_start', 'second_half_end'))
per[a1 - 1:b1] = 1; per[a2 - 1:b2] = 2
games['MET3'] = (ML.game3_events_df('/home/claude/ext/sd/data/Sample_Game_3/Sample_Game_3_events.json'), per)
out = {'environment': {'python': platform.python_version(), 'pandas': pd.__version__, 'numpy': np.__version__}, 'games': {}}
for name, (ev, per) in games.items():
    row = {'events': int(len(ev)), 'events_that_share_a_start_frame': int(ev.duplicated('Start Frame', keep=False).sum())}
    lab = {}
    for kind in ('quicksort', 'stable'):
        l = labels(ev, len(per), kind)
        lab[kind] = l
        row[kind] = {'counts': {k: int((l == k).sum()) for k in 'HADX'}, 'sha256': hashlib.sha256(''.join(l.tolist()).encode()).hexdigest(),
                     'possessions_on_play_blocks': int(score(l, l, per)['n_gt_spells'])}
    row['frames_that_differ'] = int((lab['quicksort'] != lab['stable']).sum())
    out['games'][name] = row
json.dump(out, open(sys.argv[1], 'w'), indent=1)
for k, v in out['games'].items():
    print(out['environment'], k, v['quicksort']['counts'], v['quicksort']['possessions_on_play_blocks'], '|', v['stable']['counts'], v['stable']['possessions_on_play_blocks'], '| differ', v['frames_that_differ'], v['quicksort']['sha256'][:12], v['stable']['sha256'][:12])
