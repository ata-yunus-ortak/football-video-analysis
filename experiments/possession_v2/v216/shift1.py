"""Reporting only: the score of external labels against themselves shifted late by 3 / 8 / 25 frames, next to the values the
organisers publish for their own ground truth in EVALUATION.md (0.9818 / 0.8933 / 0.6539). A property of the possession
lengths in a label set; computed on external labels only."""
import errlib as E, numpy as np
seen = set()
for f in E.copies():
    d = E.load(f)
    if d['match'] in seen:
        continue
    seen.add(d['match'])
    lab, per = d['lab'], d['per']
    gs = E.spells(lab, per); dur = np.array([b - a for a, b, _ in gs]) / 25.0
    out = []
    for s in (3, 8, 25):
        sh = lab.copy()
        for a, b in E.play_blocks(per):
            sh[a + s:b] = lab[a:b - s]; sh[a:a + s] = lab[a]
        out.append(E.f1_of(lab, sh, per))
    alive = sum(b - a for a, b, _ in gs) / 25.0
    print(f"{d['match']}: spells {len(gs)}, mean length {dur.mean():.1f} s, median {np.median(dur):.1f} s, share < 1 s {np.mean(dur < 1):.3f}, < 2 s {np.mean(dur < 2):.3f}, < 3 s {np.mean(dur < 3):.3f} | late by 3 / 8 / 25 frames: {out[0]:.4f} / {out[1]:.4f} / {out[2]:.4f}")
print('organisers, their full-match ground truth (EVALUATION.md):                                              0.9818 / 0.8933 / 0.6539; public 5 minutes: 17 possessions, mean 14.2 s')
