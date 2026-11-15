"""Reporting only (log entry K007): where does the core decision lose spellF1 on external validation?

Cached v2.1 probabilities of the 8 original validation copies (J03WN1, J03WR9, MET1, MET2 x corruption seeds
101/102; the core models of possession-v2.11 are the v2.1 models), decoded with the frozen decoder. Provider
labels are used to classify the errors and to size what-if headrooms that need the labels (oracles). Nothing
here selects or tunes anything; the copies were used before, so these numbers are a diagnosis, not a test.
Usage: python3 err_spells.py  (writes err_spells.json next to this file)
"""
import sys, json, platform, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
import pandas
from harness import load
from possession.decode import emissions, decode_blocks
from possession.evaluate import _with_separators
from possession import official_metrics as pm

DEC = {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}
C = '/home/claude/work/cache/'
BINS = [('<1s', 0, 25), ('1-2s', 25, 50), ('2-5s', 50, 125), ('5-10s', 125, 250), ('>10s', 250, 10 ** 9)]
SHIFTS = list(range(-25, 26, 5))
THR = list(pm.SPELL_IOUS)
D_CODE = int(pm.label_codes(np.array(['D']))[0])
TEAM_CODES = [int(c) for c in pm.label_codes(np.array(['H', 'A']))]


def bin_of(n):
    for name, a, b in BINS:
        if a <= n < b:
            return name


def greedy_pairs(overlaps, thr):
    used_g, used_p, pairs = set(), set(), []
    for iou, gi, pj in overlaps:
        if iou < thr:
            break
        if gi in used_g or pj in used_p:
            continue
        used_g.add(gi); used_p.add(pj); pairs.append((gi, pj, iou))
    return pairs


def sf1(g, p, runs):
    return pm.spell_scores(g, p, runs)['mean_f1']


def shifted(p, runs, k):
    """Predictions moved k frames later (k > 0) or earlier (k < 0) inside each graded run, edges repeated."""
    out = p.copy()
    for a, b in runs:
        w = p[a:b]
        if k > 0:
            out[a:b] = np.r_[np.repeat(w[:1], k), w[:-k]][:b - a]
        elif k < 0:
            out[a:b] = np.r_[w[-k:], np.repeat(w[-1:], -k)][:b - a]
    return out


def case(name, seed):
    m, lab = load(name)
    per = m['period']
    z = np.load(f'{C}probs_sys_v21_{name}_{seed}_f2.npz')
    pred = decode_blocks(emissions(z['pd'], z['ph']), per, DEC)
    g, p = pm.label_codes(_with_separators(lab, per)), pm.label_codes(_with_separators(pred, per))
    runs = pm.valid_runs(g)
    gs, ps = pm.possession_spells(g, runs), pm.possession_spells(p, runs)
    ov = pm.spell_overlaps(gs, ps)
    nthr = np.zeros(len(gs), int)
    for t in THR:
        nthr += pm.matched_gt_flags(ov, len(gs), t)
    pairs = greedy_pairs(ov, 0.3)
    pmatched = {pj for _, pj, _ in pairs}
    run_start = {a for a, _ in runs}; run_stop = {b for _, b in runs}
    r = {'spell_f1': sf1(g, p, runs), 'n_gt': len(gs), 'n_pred': len(ps)}
    # ground-truth spells by length: matched at all IoU thresholds / some (timing) / none (missed)
    gt_tab = {b[0]: {'n': 0, 'good': 0, 'timing': 0, 'missed': 0} for b in BINS}
    for (a, b, _), k in zip(gs, nthr):
        row = gt_tab[bin_of(b - a)]; row['n'] += 1
        row['good' if k == len(THR) else 'timing' if k else 'missed'] += 1
    pr_tab = {b[0]: {'n': 0, 'spurious': 0} for b in BINS}
    for j, (a, b, _) in enumerate(ps):
        row = pr_tab[bin_of(b - a)]; row['n'] += 1
        row['spurious'] += j not in pmatched
    # boundary offsets of the pairs matched at IoU 0.3, by the kind of ground-truth boundary
    off = {'start_from_dead': [], 'start_from_team': [], 'end_to_dead': [], 'end_to_team': []}
    for gi, pj, _ in pairs:
        (ga, gb, _), (pa, pb, _) = gs[gi], ps[pj]
        if ga not in run_start:
            off['start_from_dead' if g[ga - 1] == D_CODE else 'start_from_team'].append(int(pa - ga))
        if gb not in run_stop:
            off['end_to_dead' if g[gb] == D_CODE else 'end_to_team'].append(int(pb - gb))
    # what-ifs that use the labels (headroom only)
    t_or = p.copy()
    for gi, pj, _ in pairs:
        lo, hi = min(gs[gi][0], ps[pj][0]), max(gs[gi][1], ps[pj][1])
        t_or[lo:hi] = g[lo:hi]
    s_or = p.copy()
    for (a, b, k), n in zip(gs, nthr):
        if n == 0 and b - a < 50:
            s_or[a:b] = k
    f_or = p.copy()
    for j, (a, b, _) in enumerate(ps):
        if j not in pmatched and b - a < 50:
            f_or[a:b] = f_or[a - 1] if a not in run_start else f_or[b]
    r['what_if'] = {'boundaries_of_detected_spells_exact': sf1(g, t_or, runs),
                    'missed_spells_under_2s_inserted': sf1(g, s_or, runs),
                    'spurious_spells_under_2s_removed': sf1(g, f_or, runs)}
    r['shift'] = {k: sf1(g, shifted(p, runs, k), runs) for k in SHIFTS}
    # frames with the wrong team while both say alive: near a ground-truth change (<= 1 s) or far from it
    trans = np.array([t for t, _, _ in pm.transitions(g, runs)])
    team = np.isin(g, TEAM_CODES), np.isin(p, TEAM_CODES)
    wrong = np.flatnonzero(team[0] & team[1] & (g != p))
    near = int(np.sum(np.min(np.abs(wrong[:, None] - trans[None, :]), 1) <= 25)) if len(wrong) and len(trans) else 0
    r['wrong_team_frames'] = {'total': int(len(wrong)), 'within_1s_of_a_change': near}
    r['gt'], r['pred'], r['offsets'] = gt_tab, pr_tab, off
    return r


def main():
    rows = {}
    for name in ('J03WN1', 'J03WR9', 'MET1', 'MET2'):
        for seed in (101, 102):
            rows[f'{name}_{seed}'] = case(name, seed)
            print(name, seed, round(rows[f'{name}_{seed}']['spell_f1'], 4), flush=True)
    R = list(rows.values())
    agg = {'spell_f1': round(float(np.mean([r['spell_f1'] for r in R])), 4)}
    agg['what_if'] = {k: round(float(np.mean([r['what_if'][k] for r in R])), 4) for k in R[0]['what_if']}
    agg['shift'] = {k: round(float(np.mean([r['shift'][k] for r in R])), 4) for k in SHIFTS}
    agg['gt'] = {b: {k: int(sum(r['gt'][b][k] for r in R)) for k in R[0]['gt'][b]} for b in R[0]['gt']}
    agg['pred'] = {b: {k: int(sum(r['pred'][b][k] for r in R)) for k in R[0]['pred'][b]} for b in R[0]['pred']}
    agg['offsets'] = {}
    for k in R[0]['offsets']:
        v = np.concatenate([r['offsets'][k] for r in R]) if any(r['offsets'][k] for r in R) else np.array([])
        if len(v):
            agg['offsets'][k] = {'n': int(len(v)), 'median_frames': float(np.median(v)), 'q25': float(np.percentile(v, 25)),
                                 'q75': float(np.percentile(v, 75)), 'mean_abs_frames': round(float(np.mean(np.abs(v))), 1)}
    agg['wrong_team_frames'] = {k: int(sum(r['wrong_team_frames'][k] for r in R)) for k in R[0]['wrong_team_frames']}
    out = {'record': 'K007 diagnosis, reporting only: spellF1 losses of the core decision on 8 used validation copies',
           'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pandas.__version__},
           'decoder': DEC, 'summary': agg, 'rows': rows, 'provided_fixture_used': False,
           'note': 'labels used only to classify errors and to size oracle headrooms; no selection'}
    json.dump(out, open('/home/claude/work/err_spells.json', 'w'), indent=1, default=float)
    print(json.dumps(agg, indent=1, default=float))


if __name__ == '__main__':
    main()
