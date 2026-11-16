# v216u: more TCN members for the pooled system (development, 15-16 Nov 2026)

Proposal for a possible possession-v2.16: keep everything of v2.15, add TCN ensemble members
trained here, and re-choose the pooling weight by the team's rule. Same architecture and key
layout as commit 167dc7b, so `possession/tcn/infer.py` runs these files unchanged.

Nothing here is a validation. External matches only; the provided match was not opened.

## What is different from the v2.15 members (`tcn_jax.py`, dfl*_both_s*)

- Training copies go through what the release applies before the network: the corruption
  simulator, then the 46 packed anonymous slots (`exp_v213.packed`) and the goalkeeper
  correction (`keeper2`). The v2.15 members were trained on unpacked copies.
- 16 copies of the team's simulator + 8 of the second simulator per match (v2.15: 6 + 6).
  Seeds 7100000 + 1000 * match + r and 7200000 + 1000 * match + r.
- PyTorch on Apple MPS, 12 epochs (about 2,500 steps for four matches, 3,700 for six; the
  v2.15 members had about 940). Not bit-reproducible; the .npz files are the reference.
- Recipe a: as 167dc7b (dropout 0.15). Recipe b: dropout 0.25 and the pitch mirrored across
  its long axis in half of the crops.

Files (`possession/weights/v216u/`, SHA-256 in `SHA256SUMS`): `d4_*` trained on J03WOH,
J03WOY, J03WPY, J03WQQ (for validation rows on J03WN1 / J03WR9); `d6_*` on all six (Metrica
rows and a release). One member per file.

## Development numbers

Copies: the tactical and second-simulator copies of the v2.14 and v2.15 validations (their
seeds; 10 per match, 40 in all), rebuilt here with `lib214.inputs`. Check of the local
harness: the v2.15 Metrica rows of `possession-v215-results.json` are reproduced to four
decimals (v2_11, fused, tcn_alone) with `models/possession-tcn-v215.npz`.

Metrica 1-2, 20 copies, released bundles, pooled as v2.15 (arithmetic, v2 decoder, v2.3 path
not pooled). Mean spellF1 difference to v2.11 | worst copy:

| TCN members | TCN alone | w 0.2 | w 0.3 | w 0.4 | w 0.5 |
|---|---|---|---|---|---|
| v2.15 (3) | +0.0091 / -0.034 | +0.0136 / -0.0031 | +0.0162 / -0.0019 | not run | +0.0187 / -0.0160 |
| v2.15 (3) + d6_a_s0, s1 | +0.0209 / -0.026 | +0.0155 / 0.0 | +0.0198 / 0.0 | +0.0222 / 0.0 | +0.0221 / -0.0032 |
| v2.15 (3) + d6_a_s0, s1, d6_b_s0, s1 | +0.0188 / -0.031 | +0.0157 / -0.0028 | +0.0189 / 0.0 | +0.0240 / 0.0 | +0.0239 / -0.0074 |
| d6_a_s0, s1, d6_b_s0, s1 only | +0.0108 / -0.036 | +0.0166 / 0.0 | +0.0199 / 0.0 | +0.0216 / -0.0071 | +0.0170 / -0.0124 |

DFL (J03WN1, J03WR9): TCN alone only, because the four-match v2 validation models are not in
the repository. On the 10 copies of the v2.15 validation: v2.15's three dfl4 members 0.6473
(from the results file), d4_a_s0 + s1 0.6538, all four d4 files 0.6498; v2.11 0.6436.
All 20 DFL copies: d4_a pair 0.6554, d4_b pair 0.6434, all four 0.6526.

Reading: recipe a adds more than recipe b. With the a members added, the worst copy stops
going negative up to weight 0.4 on Metrica. The pooled effect on DFL is unknown here.

## Update 16 Nov, night: pooled numbers on DFL as well

`v2val.py` rebuilds the four-match v2.1 validation models (`models_v2.pkl`, `stack_v2.pkl`) with the
logic of `train1.py` (FTAG=_f2) and `exp_stack.py _f2`, scikit-learn 1.9.1. Check: on all ten DFL
copies of the v2.15 validation the rebuilt models give the v2_11 spellF1 of
`possession-v215-results.json` to four decimals (e.g. J03WN1|19100 0.6043, J03WR9|19110 0.7158).
All 20 DFL development copies are on the v2.1 path.

More members: `d4_a_s2`, `d4_a_s3`, `d6_a_s2`, `d6_a_s3` (recipe a, seeds 2 and 3). Also tried and
not kept: hidden 192 (three seeds), hidden 256, 7 epochs - single members differ by seed, ensembles
end at the same level as recipe a.

Pooled exactly as v2.15 (`grid216.py`), mean spellF1 difference to v2.11 / worst copy, 20 DFL + 20 Metrica copies:

| TCN members | side | TCN alone | w 0.2 | w 0.3 | w 0.4 | w 0.5 |
|---|---|---|---|---|---|---|
| a_s0..s3 (4) | DFL | +0.0134 / -0.026 | +0.0179 / +0.0047 | +0.0252 / +0.0090 | +0.0297 / +0.0142 | +0.0290 / +0.0069 |
| a_s0..s3 (4) | Metrica | +0.0083 / -0.032 | +0.0172 / 0.0 | +0.0206 / -0.0004 | +0.0219 / -0.0104 | +0.0218 / -0.0086 |
| v2.15 (3) | Metrica | +0.0091 / -0.034 | +0.0136 / -0.0031 | +0.0162 / -0.0019 | +0.0194 / 0.0 | +0.0187 / -0.0160 |
| v2.15 (3) + a_s0..s3 + three hidden-192 | Metrica | +0.0186 / -0.023 | +0.0168 / 0.0 | +0.0208 / 0.0 | +0.0233 / 0.0 | +0.0257 / -0.0066 |

For comparison, the registered v2.15 result (w 0.2, its own new copies): DFL +0.0126, Metrica +0.0097.
The v2.15 four-match members are not in the repository, so sets containing them cannot be scored on DFL here.

Reading: with the recipe-a members the pooled gain is about +0.025 (DFL) and +0.021 (Metrica) at
w 0.3 with no copy clearly worse, against about +0.013 / +0.014 for v2.15 at w 0.2. Same caveat as
above: reused copies, several sets and weights compared.

## Limits

- The 40 copies were used before (v2.14 / v2.15 validations and their development), and the
  table compares 4 member sets x 4 weights on them: optimistic by construction.
- Sets that include the v2.15 members could not be pooled on DFL here.
- Run time: each member adds about one minute per match in the NumPy inference.

## Reproduce

    python cache_train.py MATCH 16 8          # six matches; needs env.py paths
    python train216.py TAG SEED 12 DROPOUT MATCH...   # from the mtah-possession checkout
    python dev216.py prep NAME ; python fwd216.py 'MET*' W.npz... ; python dev216.py score d6 0.2,0.3,0.4,0.5 STEM...

`env.py` points the team's harness (`experiments/possession_v2`) at local copies of the
prepared DFL matches (`tools/sportec_prepare.py`, pinned hashes verified) and the Metrica CSVs.
