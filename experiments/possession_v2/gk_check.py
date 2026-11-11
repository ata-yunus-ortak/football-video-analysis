"""Development check (training match, in-sample for the release bundles: relative effect only): release logic with
and without the goalkeeper correction, ids correct and both goalkeepers wrong, sticky 46-slot layout."""
import sys, json, time, warnings
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.bundle import load as load_bundle
from possession.evaluate import score
from possession.keeper import correct_goalkeepers
from possession.epts_export import tracklets, pack
from stress_roles import goalkeepers, variant
from stress_slots import release_labels
name = sys.argv[1]
m, lab = load(name); gk = goalkeepers(m)
seed = 5000 + sum(map(ord, name)) % 1000
rng = np.random.default_rng(seed); dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
n = len(dm['ball']); SLOT46 = np.r_[np.zeros(23, np.int8), np.ones(23, np.int8)]
b21 = load_bundle('/home/claude/sc/models/possession-v2.npz'); b23 = load_bundle('/home/claude/sc/models/possession-v23.npz'); half = int(b23['card']['smooth_half'])
for ci, cond in enumerate(('base', 'gk_both')):
    mv = variant(cond, dm, m, gk, np.random.default_rng(seed + 10 + 2 * ci))
    P, _ = pack(n, tracklets(np.asarray(mv['players']), mv['team']), SLOT46)
    mm = dict(mv, players=P, team=SLOT46)
    fixed, rep = correct_goalkeepers(mm)
    for tag, x in (('as is', mm), ('corrected', fixed)):
        t0 = time.time()
        labels, path = release_labels(x, b21, b23, half)
        r = score(lab, labels, m['period'])
        print(json.dumps({'match': name, 'condition': cond, 'input': tag, 'path': path, 'spell_f1': round(r['spell_f1_mean'], 4), 'macro_f1': round(r['macro_f1'], 4),
                          'moved_pieces': rep['moved_pieces'], 'moved_frames': rep.get('moved_frames'), 'seconds': round(time.time() - t0)}), flush=True)
