# Registered validation plan: v2.x + TCN fusion

Written 12 Nov 2026, before any score of the DFL-only weights (`tcn_dfl6.npz`) on any match.

Fixed in advance:
- Fusion: arithmetic mean of class probabilities [home, away, dead], weight 0.5 / 0.5.
- Decoder: single Viterbi, switch cost 6, no other tuning.
- TCN weights: `tcn_dfl6.npz` as committed (SHA-256 recorded in the result file).
- Baseline: frozen v2.11 / v2.11g as shipped.
- Noise: new seeds, not used in any earlier run; both noise simulators.
- Scorer: organisers' `possession_metrics.py`. Metrica labels from the stable-sort
  `metrica_labels.py` (log K005); Python / pandas / numpy versions recorded.

Reported separately:
1. Metrica games 1-3 (unseen by both sets of weights; development scores of an earlier TCN
   on these games were seen, and game 3 is no longer a reserved test).
2. DFL, leave-one-match-out for both models. The TCN side needs six retrainings with the same
   recipe; the v2.x side needs its leave-one-match-out bundles. If those are not available,
   no DFL fusion number is claimed.
3. Each with and without the simulated broadcast fill.

Decision rule: same gates as v2.12 (must hold on DFL and on Metrica). If the gates fail or the
run is not finished by the internal freeze (Sat 14 Nov 23:59), v2.11 / v2.11g is submitted and
the fusion is documented as future work.

J03WMX: not in `tcn_dfl6.npz`, but earlier TCN cross-validation scores on it were seen. Not to
be touched for this fusion without a team decision.
