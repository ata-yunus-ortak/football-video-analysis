"""Pipeline-correctness check against the organisers' public 5-minute ground truth: PASS/FAIL only.

    python -m possession.public_check path/to/submission.csv path/to/BAR-ATH_possession_gt_public.csv

RULES.md says what the published five minutes are for: "checking that your pipeline is correct --
frames aligned, file well-formed, labels meaning what you think". They are not training data, not a
tuning set, and never a way to choose between two versions. This tool therefore prints PASS or FAIL
per check and no score, and it stores no score. The thresholds are fixed in
possession-final-check-plan.json before the first run on a real file; they only separate a working
pipeline from a broken one (teams exchanged, frames shifted, wrong file):

  valid_submission   the file passes the organisers' own format checks for this ground truth
  above_broken_floor spell_f1_mean >= 0.20 and macro_f1 >= 0.50 (the organisers' scorer gives a
                     prediction with the two teams exchanged 0.00 and about 0.33)
  teams_not_exchanged the file does not score lower than the same file with H and A exchanged

A FAIL means: look for a mapping or indexing bug in the pipeline. It is never a reason to change a
model, a threshold or the release. The verdict of a (submission, ground truth) pair is computed once
and stored next to the submission; later calls show the stored verdict.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np
from . import official_metrics as pm

MIN_SPELL_F1 = 0.20
MIN_MACRO_F1 = 0.50
CHECKS = ('valid_submission', 'above_broken_floor', 'teams_not_exchanged')


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def exchange_teams(codes):
    out = codes.copy()
    out[codes == pm.H] = pm.A
    out[codes == pm.A] = pm.H
    return out


def verdict(sub_path, gt_path):
    """{check: bool}; scores are computed in memory and not returned."""
    gt = pm.label_codes(pm.read_label_csv(gt_path))
    res = {k: False for k in CHECKS}
    try:
        table = pm.read_label_csv(sub_path)
    except Exception:
        return res
    if pm.validate_submission(table, len(gt)):
        return res
    res['valid_submission'] = True
    pred = pm.label_codes(table)
    own = pm.evaluate(gt, pred)
    other = pm.evaluate(gt, exchange_teams(pred))
    res['above_broken_floor'] = bool(own['spell_f1_mean'] >= MIN_SPELL_F1 and own['macro_f1'] >= MIN_MACRO_F1)
    res['teams_not_exchanged'] = bool(own['spell_f1_mean'] >= other['spell_f1_mean'] and own['macro_f1'] >= other['macro_f1'])
    return res


def check(sub_path, gt_path, store=True):
    """(checks, stored): the verdict for this pair, from the marker file when it exists for these bytes."""
    sub_path, gt_path = Path(sub_path), Path(gt_path)
    key = {'submission_sha256': _sha(sub_path), 'ground_truth_sha256': _sha(gt_path),
           'thresholds': {'spell_f1_mean': MIN_SPELL_F1, 'macro_f1': MIN_MACRO_F1}}
    marker = sub_path.with_name(sub_path.name + '.public_check.json')
    if marker.exists():
        try:
            old = json.loads(marker.read_text(encoding='utf-8'))
            if all(old.get(k) == v for k, v in key.items()) and set(old.get('checks', {})) == set(CHECKS):
                return {k: bool(old['checks'][k]) for k in CHECKS}, True
        except (ValueError, OSError):
            pass
    res = verdict(sub_path, gt_path)
    if store:
        marker.write_text(json.dumps(dict(key, checks=res, checked_at=time.strftime('%Y-%m-%dT%H:%M:%S'),
                                          note='PASS/FAIL only; no score is stored'), indent=1), encoding='utf-8')
    return res, False


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('submission')
    p.add_argument('public_ground_truth')
    a = p.parse_args(argv)
    res, stored = check(a.submission, a.public_ground_truth)
    for k in CHECKS:
        print(('PASS ' if res[k] else 'FAIL ') + k)
    print('PUBLIC CHECK ' + ('OK' if all(res.values()) else 'FAILED') + (' (stored verdict)' if stored else ''))
    return 0 if all(res.values()) else 2


if __name__ == '__main__':
    sys.exit(main())
