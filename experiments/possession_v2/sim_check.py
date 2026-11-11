import sys, numpy as np, warnings, collections
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession import smarttags as st
for name in ('J03WOH', 'MET1'):
    m, lab = load(name)
    graded_min = np.isin(m['period'], (1, 2)).sum() / m['fps'] / 60
    for regime in ('clean', 'default'):
        rng = np.random.default_rng(5)
        p = st.sample_params(rng, regime)
        tags = st.simulate(lab, m['ball'], m['players'], m['team'], m['period'], m['pitch'], m['fps'], rng, p)
        c = collections.Counter(t['code'] for t in tags)
        dur = collections.defaultdict(list)
        for t in tags: dur[t['code']].append((t['end'] - t['start']) / m['fps'])
        print(name, regime, 'minutes %.0f' % graded_min, 'tags', len(tags))
        for k, v in sorted(c.items(), key=lambda x: -x[1]):
            print('   %-30s %4d  median %.1f s' % (k, v, np.median(dur[k])))
        sp = [t for t in tags if t['code'] == 'set pieces']
        print('   set piece types', collections.Counter(t['type'] for t in sp))
        F, names = st.features(tags, len(lab), m['period'], m['fps'])
        print('   feature shape', F.shape, 'nan in blocks', int(np.isnan(F[np.isin(m['period'], (1, 2))]).sum()), 'tag coverage %.2f' % np.nanmean(F[:, names.index('tg_any')]))
