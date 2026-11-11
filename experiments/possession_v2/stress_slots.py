"""Reporting-only diagnostic: two documented properties of the provided ATD that the validation never simulated.

DATA.md: "Slots appear, vanish and swap identity as the tracker loses and re-acquires people" and the number
of tracked objects "occasionally exceeds 22 when the tracker duplicates someone". The corruption used for
training and validation (possession.degrade) keeps one column per player and adds no duplicated tracks.

Design, fixed before the first result (no selection, no gate, nothing is changed by the outcome of this
script alone): Metrica sample games 1, 2 and 3 (not in the training set of the release bundles), one corrupted
copy each (v2 profile, seeds 8101-8103, new), the frozen release logic in memory (noise gate, then the v2.1 or
v2.3 bundle), scored with the organisers' metric on the external labels. Variants of the same corrupted copy:
  base      the layout used in every validation so far (one column per player, extra columns for wrong-team tracklets)
  sticky    tracklets packed into 46 anonymous slots (23 per team); a track lost for <= 1 s returns to its slot
  lru       packed; a track never returns to its slot (identity never kept)
  swap      packed; a new track takes the slot that was freed last (another person follows directly in a slot)
  dup1      base plus duplicated tracks at the rate of the rehearsal bundle (about 0.6% of tracked positions)
  dup5      base plus five times as many duplicated tracks
Usage: stress_slots.py OUT_JSON
"""
import json
import os
import sys
import time
import warnings
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
sys.path.insert(0, '/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova')
from harness import load
from possession.degrade import degrade, sample_params, RANGES
from possession.bundle import load as load_bundle
from possession.pipeline import predict_labels
from possession.smooth import smooth_positions
from possession.noise import estimate_noise, choose_path
from possession.evaluate import score
from prova_build import pack, tracklets, duplicates

CASES = (('MET1', 8101), ('MET2', 8102), ('MET3', 8103))
DUP_RATE = 0.0012


def release_labels(m, b21, b23, half):
    noise = estimate_noise(m)
    path, _ = choose_path(noise)
    if path == 'v2.3':
        return predict_labels(smooth_positions(m, half), b23)[0], path
    return predict_labels(m, b21)[0], path


if __name__ == '__main__':
    OUT = sys.argv[1]
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': []}
    done = {(r['match'], r['variant']) for r in res['rows']}
    b21 = load_bundle('/home/claude/sc/models/possession-v2.npz')
    b23 = load_bundle('/home/claude/sc/models/possession-v23.npz')
    half = int(b23['card']['smooth_half'])
    for name, seed in CASES:
        if all((name, v) in done for v in ('base', 'sticky', 'lru', 'swap', 'dup1', 'dup5')):
            continue
        m, lab = load(name)
        rng = np.random.default_rng(seed)
        dm = degrade(m, lab, rng, sample_params(rng, ranges=RANGES))
        n = len(dm['ball'])
        items = tracklets(dm['players'], dm['team'])
        slot46 = np.r_[np.zeros(23, np.int8), np.ones(23, np.int8)]
        wide = np.r_[np.zeros(30, np.int8), np.ones(30, np.int8)]
        rd = np.random.default_rng(seed + 500)
        d1 = duplicates(dm['players'], dm['team'], rd, DUP_RATE)
        d5 = d1 + duplicates(dm['players'], dm['team'], rd, 4 * DUP_RATE)
        tracked = float(np.isfinite(dm['players']).all(2).sum())

        def variant(v):
            if v == 'base':
                return dm, {}
            if v in ('sticky', 'lru', 'swap'):
                P, peak = pack(n, items, slot46, v)
                return dict(dm, players=P, team=slot46), {'peak_simultaneous_per_team': peak}
            dups = d1 if v == 'dup1' else d5
            extra = [(a, b, t, f'dup{i}', xy) for i, (a, b, t, xy) in enumerate(dups)]
            P, peak = pack(n, items + extra, wide, 'sticky', gap=10 ** 9)
            return dict(dm, players=P, team=wide), {'duplicated_tracks': len(dups),
                                                     'duplicated_share_of_tracked_positions': round(sum(b - a for a, b, _, _ in dups) / tracked, 4)}

        for v in ('base', 'sticky', 'lru', 'swap', 'dup1', 'dup5'):
            if (name, v) in done:
                continue
            t0 = time.time()
            mv, info = variant(v)
            labels, path = release_labels(mv, b21, b23, half)
            r = score(lab, labels, m['period'])
            row = dict({'match': name, 'seed': seed, 'variant': v, 'path': path, 'spell_f1': round(r['spell_f1_mean'], 4),
                        'macro_f1': round(r['macro_f1'], 4), 'slots': int(mv['players'].shape[1]),
                        'tracklets': len(items), 'seconds': round(time.time() - t0)}, **info)
            res['rows'].append(row)
            json.dump(res, open(OUT, 'w'), indent=1)
            print(json.dumps(row), flush=True)
            del mv, labels
    print('STRESSDONE', flush=True)
