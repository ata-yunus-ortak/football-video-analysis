# Possession TCN (`possession/`)

Second possession model for the More Than A Hack 2027 Initial Challenge, built to be fused
with the team's v2.x models. Status on 12 Nov 2026: **not validated under the team protocol
yet** (see "Validation").

## What it is

1. External tracking with per-frame possession labels is degraded to look like automatic
   tracking (`degrade.py`: ball drop-outs in bursts, jitter, false ball detections, missing
   players).
2. 37 team-symmetric features per frame (`features.py`).
3. A dilated temporal convolution network at 12.5 Hz gives P(team 0), P(team 1), P(dead)
   (`train.py`; 3 seeds, averaged over both team orders).
4. A Viterbi pass with a fixed switch cost turns probabilities into possessions (`decode.py`).

## Data and licence

Shipped weights `possession/weights/tcn_dfl6.npz` are trained only on six matches of the
open DFL/IDSSE dataset (Bassek et al. 2025, figshare 10.6084/m9.figshare.28196177, CC-BY 4.0):
J03WN1, J03WOH, J03WOY, J03WPY, J03WQQ, J03WR9. J03WMX and the Metrica sample games are not
in these weights. Nothing from the competition match (tracking, video, tags, ground truth)
was used for training or for choosing any setting. No match data is in this repository.

Disclosure: during development (before these weights) J03WMX and Metrica games 1-3 were used
in cross-validation and in an earlier set of weights that is not shipped. Development scores
on those matches were seen, so they are not untouched test data for this model family.

## Commands

    # regenerate the submission part of this model (NumPy only)
    python -m possession.predict --data DATA_DIR --out OUT.csv --switch-cost 6 \
        [--kickoff none] [--probs-out probs.npz]

    # retrain (PyTorch)
    python -m possession.dfl ...                       # DFL XML -> npz, see module docstring
    python -m possession.train cache --dfl DIR --metrica DIR --cache CACHE
    python -m possession.train final --cache CACHE --out MODELS --epochs 20 --seeds 3 \
        --exclude dfl_J03WMX metrica_
    python -m possession.infer export --models MODELS --out possession/weights/tcn_dfl6.npz

`--probs-out` writes per-frame `p_dead` and `p_home_given_alive` on the 25 fps video frame
grid (NaN outside the graded blocks). Home is the first `<Team>` in the ATD metadata.

## Determinism

Inference is NumPy float64 on CPU (`infer.py`), and probabilities are rounded to 4 decimals
before decoding. It agrees with the PyTorch forward pass to 1e-6. Byte-identical output across
operating systems is expected but has not been tested on Windows/Linux yet. Training on Apple
MPS is not bit-reproducible; the exported weights are the reference.

## Kick-off

`--kickoff tag` (default) writes D from the start of each graded block up to the first
automatic Smart Tagging "Kick Off (Start)" inside it, if that tag is within 10 minutes of the
block start; otherwise the model decides. `--kickoff none` always lets the model decide. The
tag rule cannot be measured on external data. No frame number is hard-coded.

## Validation

Development numbers (not registered; weight and switch cost were looked at on the same
copies; own Metrica labels, not `metrica_labels.py`): on 24 degraded copies of Metrica 1-3,
team v2.4 path 0.702 spellF1, this model 0.714, 50/50 probability average 0.731 (cost 6).
These motivate the registered run in `docs/POSSESSION_TCN_VALIDATION_PLAN.md`; they are not a claim.
