"""External teacher proxy with competition-style abstention treatment.

Not official scores: targets are automatic provider estimates, with no D truth.
Unknown targets delimit evaluation blocks and never become dead-ball labels.
"""
import numpy as np
from clean_model.metrics import measure


def fill_prediction_gaps(target, prediction, period):
    target, prediction, period = map(np.asarray, (target, prediction, period))
    if (target.ndim != 1 or prediction.shape != target.shape or period.shape != target.shape
            or not np.isin(target, ('H', 'A', 'X')).all()
            or not np.isin(prediction, ('H', 'A', 'X')).all()):
        raise ValueError('Aligned external H/A/X targets and predictions required')
    result = prediction.copy()
    known = np.isin(target, ('H', 'A')) & np.isin(period, (1, 2))
    result[~known] = 'X'
    boundaries = np.r_[0, np.flatnonzero((known[1:] != known[:-1]) | (period[1:] != period[:-1])) + 1, len(target)]
    for a, b in zip(boundaries[:-1], boundaries[1:]):
        if not known[a]:
            continue
        ids = np.flatnonzero(result[a:b] != 'X')
        if not len(ids):
            continue
        block = result[a:b]
        index = np.maximum.accumulate(np.where(block != 'X', np.arange(b-a), -1))
        index[index < 0] = ids[0]
        result[a:b] = block[index]
    return result


def evaluate(target, prediction, period):
    original = measure(target, prediction, period)
    filled = fill_prediction_gaps(target, prediction, period)
    temporal = measure(target, filled, period)
    return {**original, 'provider_filled_spell_f1': temporal['provider_team_spell_iou_f1'],
            'abstention_fraction': float(np.mean(np.asarray(prediction) == 'X')),
            'D_validated': False}
