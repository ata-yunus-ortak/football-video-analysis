"""Consistency check of the validation script on a DEVELOPMENT copy (J03WN1, seed 13100 of the v2.13 validation, already
scored): exp_v214's fused arm, with the pooling set by hand to the geometric pool 0.4, must give the number that
explore2.py gave for that copy from stored probabilities. No new copy is touched. Usage: check_exp_v214.py"""
import sys, json
sys.path.insert(0, '/home/claude/work/v214')
import exp_v214 as X
from exp_v214 import E, fuse2
fuse2.POOL, fuse2.WEIGHT = 'geometric', 0.4
E.STREAM, E.CLOCK = 43100, 53100                 # the old streams (not used by the tactical condition)
res = {'rows': []}
E.copy_rows('J03WN1', 13100, 0, res, '/home/claude/work/v214/check_exp_v214.json', set(), ('tactical',))
r = res['rows'][0]
dev = json.load(open('/home/claude/work/v214/explore2_d4.json'))['J03WN1_13100_tactical']
print('exp_v214: v2_11', r['v2_11']['spell_f1'], 'fused', r['fused']['spell_f1'], 'tcn_alone', r['tcn_alone']['spell_f1'])
print('explore2: v2_11', dev['v2_11'][0], 'geo40', dev['geo40'][0], 'tcn_alone', dev['tcn_alone'][0])
print('equal:', abs(r['v2_11']['spell_f1'] - dev['v2_11'][0]) < 1e-12, abs(r['fused']['spell_f1'] - dev['geo40'][0]) < 1e-12,
      abs(r['tcn_alone']['spell_f1'] - dev['tcn_alone'][0]) < 1e-12)
