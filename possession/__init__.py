"""Possession v2: tracking-based H/A/D inference selected on external fixtures only.

Package layout:
  data.py      common in-memory match representation + readers (EPTS/ATD, DFL, Metrica)
  degrade.py   simulator that makes clean external tracking resemble automatic tracking
  features.py  per-frame features (ball, players, team interaction, dead-ball context)
  trees.py     numpy evaluator for exported gradient-boosted trees (version independent)
  decode.py    H/A/D Viterbi decoder with transition costs
  pipeline.py  feature -> probabilities -> labels
  run.py       command line entry point for the competition bundle (run locally by the team)
"""
