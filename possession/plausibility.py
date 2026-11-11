"""Plausibility check of a generated submission (no ground truth, no video, no tuning).

    python -m possession.plausibility path/to/submission.csv

Compares a few aggregate statistics of the label sequence with wide ranges observed for this
system and for provider labels on external matches (measured values: docs/DENEY_KAYDI_TR.md, entry R002).
It prints PASS/FAIL per check without the values, so the result can be shared. A FAIL does not
say the output is wrong; it says the run should be inspected before it is submitted (wrong
file, wrong half boundaries, a reader problem). It never changes the output.
"""
import argparse
import sys
import numpy as np
from . import official_metrics as pm

FPS = 25.0
# (low, high): external range of this system and of provider labels, widened (see module docstring)
RANGES = {'dead_share_in_play': (0.15, 0.70), 'spells_per_minute': (1.5, 7.0), 'median_spell_s': (2.0, 14.0),
          'home_share_of_possession': (0.20, 0.85), 'longest_spell_s': (20.0, 240.0), 'longest_dead_in_play_s': (30.0, 420.0),
          'play_minutes': (85.0, 115.0)}


def _runs(x):
    br = np.flatnonzero(x[1:] != x[:-1]) + 1
    st = np.r_[0, br]; en = np.r_[br, len(x)]
    return st, en, x[st]


def stats(labels):
    """Aggregate statistics of an H/A/D sequence; play = first..last possession frame without the
    longest dead run (the half-time break when the file covers a whole recording)."""
    x = np.asarray(labels)
    pos = np.flatnonzero(x != 'D')
    if len(pos) < 2:
        return {k: float('nan') for k in RANGES}
    x = x[pos[0]:pos[-1] + 1]
    st, en, val = _runs(x)
    dead = (val == 'D'); dl = (en - st)[dead]
    if len(dl) and dl.max() >= 5 * 60 * FPS:      # a break of five minutes or more is not play
        k = np.flatnonzero(dead)[np.argmax(dl)]
        halves = [x[:st[k]], x[en[k]:]]
    else:
        halves = [x]
    n = sum(len(h) for h in halves); sp, dd = [], []; nh = na = nd = 0
    for h in halves:
        s, e, v = _runs(h)
        sp += list((e - s)[v != 'D']); dd += list((e - s)[v == 'D'])
        nh += int(np.sum(h == 'H')); na += int(np.sum(h == 'A')); nd += int(np.sum(h == 'D'))
    return {'dead_share_in_play': nd / n, 'spells_per_minute': len(sp) / (n / FPS / 60), 'median_spell_s': float(np.median(sp)) / FPS,
            'home_share_of_possession': nh / max(nh + na, 1), 'longest_spell_s': max(sp) / FPS,
            'longest_dead_in_play_s': (max(dd) if dd else 0) / FPS, 'play_minutes': n / FPS / 60}


def check(path):
    table = pm.read_label_csv(path)
    lab = np.array([str(v).strip().upper() for v in table['label'].values])
    lab = np.where(lab == 'X', 'D', lab)
    s = stats(lab)
    return {k: bool(np.isfinite(s[k]) and RANGES[k][0] <= s[k] <= RANGES[k][1]) for k in RANGES}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('csv')
    a = p.parse_args()
    res = check(a.csv)
    for k, ok in res.items():
        print(('PASS ' if ok else 'FAIL ') + k)
    print('PLAUSIBILITY ' + ('OK' if all(res.values()) else 'CHECK NEEDED'))
    sys.exit(0 if all(res.values()) else 2)
