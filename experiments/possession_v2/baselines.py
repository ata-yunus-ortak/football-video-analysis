import sys, numpy as np
sys.path.insert(0, '/home/claude/sc')

def organizer_baseline(m, window=50):
    """starter/baseline.py logic on the common representation."""
    ball, players, team = m['ball'], m['players'], m['team']
    d = np.linalg.norm(players - ball[:, None], axis=2)
    d = np.where(np.isfinite(d), d, np.inf)
    j = np.argmin(d, 1)
    ok = np.isfinite(ball).all(1) & np.isfinite(d[np.arange(len(d)), j])
    codes = np.where(ok, team[j], -1)
    if window <= 0:
        return np.where(codes == 0, 'H', np.where(codes == 1, 'A', 'D'))
    hc = np.concatenate(([0], np.cumsum(codes == 0))); ac = np.concatenate(([0], np.cumsum(codes == 1)))
    i = np.arange(len(codes)); lo = np.maximum(0, i - window); hi = np.minimum(len(codes), i + window + 1)
    h = hc[hi] - hc[lo]; a = ac[hi] - ac[lo]
    lab = np.full(len(codes), 'D', dtype='<U1'); seen = (h + a) > 0
    lab[seen] = np.where(h[seen] >= a[seen], 'H', 'A')
    return lab

def s001(m):
    from development.sequence_possession import SequenceConfig, predict
    cfg = SequenceConfig(radius_m=3.8073350256105085, relative_speed_scale_mps=3.4176014981269645,
                         max_gap_s=5.9, switch_cost_s=0.25, mode='relative_motion')
    n = len(m['ball'])
    inputs = {'players': m['players'].astype(float), 'ball': m['ball'].astype(float), 'teams': m['team'],
              'period': m['period'], 'frame': np.arange(n), 'fps': np.array(float(m['fps'])),
              'pitch': np.asarray(m['pitch'], float), 'ball_observed': np.isfinite(m['ball']).all(1),
              'player_detected': np.isfinite(m['players']).all(2)}
    return predict(inputs, cfg)
