"""Validate a submission file with the organisers' own checks (vendored possession_metrics).

    python -m possession.validate path/to/submission.csv [--rows 199319]

Prints only aggregate information (row count, label counts, number of possessions), never
frame-level content, so the output can be shared without sharing the provided data.
"""
import argparse
import sys
import numpy as np
from . import official_metrics as pm


def check(path, rows=199319):
    table = pm.read_label_csv(path)
    reason = pm.validate_submission(table, rows)
    if reason:
        return False, {'error': reason}
    codes = pm.label_codes(table)
    runs = pm.valid_runs(codes)
    spells = pm.possession_spells(codes, runs)
    counts = {k: int(np.sum(codes == i)) for i, k in enumerate(pm.LABELS)}
    return True, {'rows': int(len(codes)), 'label_counts': counts, 'possession_spells': len(spells)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('csv')
    p.add_argument('--rows', type=int, default=199319)
    a = p.parse_args()
    ok, info = check(a.csv, a.rows)
    print(('OK ' if ok else 'FAIL ') + str(info))
    sys.exit(0 if ok else 1)
