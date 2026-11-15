"""Development: regenerate the tracking of a development copy (same seeds -> same copy) and store what the boundary study
needs: ball position, nearest player distance per team, per frame. Usage: track1.py KEY [KEY ...]"""
import sys, os, numpy as np, time
import errlib as E
import lib214 as L
OUT = '/home/claude/work/v216/track/'
os.makedirs(OUT, exist_ok=True)
for key in sys.argv[1:]:
    name, seed, cond = key.split('_')[0], int(key.split('_')[1]), '_'.join(key.split('_')[2:])
    if os.path.exists(OUT + key + '.npz'):
        continue
    t0 = time.time()
    gen = L.inputs(name, seed, 0, ['tactical']) if cond == 'tactical' else L.inputs(name, 0, 0, ['tactical_sim2'], sim2_seed=seed)
    for c, k, path, base, lab, per, info in gen:
        d = E.load(L.PROBS + key + '.npz')
        assert (np.asarray(lab) == d['lab']).all() and (np.isfinite(base['ball'][:, 0]) == d['ball_seen']).all(), 'not the stored copy'
        ball = base['ball'][:, :2].astype(np.float32)
        pl, tm = base['players'], np.asarray(base['team'])
        dist = []
        for t in (0, 1):
            p = pl[:, tm == t, :]
            dd = np.hypot(p[:, :, 0] - ball[:, None, 0], p[:, :, 1] - ball[:, None, 1])
            dist.append(np.where(np.isnan(dd).all(1), np.nan, np.nanmin(np.where(np.isnan(dd), np.inf, dd), 1)).astype(np.float32))
        np.savez_compressed(OUT + key + '.npz', ball=ball, d0=dist[0], d1=dist[1])
        print(key, list(base.keys()), pl.shape, round(time.time() - t0), 's', flush=True)
