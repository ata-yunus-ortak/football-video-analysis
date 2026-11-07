"""H/A/D external evaluation with explicit unknown-target boundaries.

The evaluation targets never enter inference. Implements temporal IoU matching
and prediction abstention fill as described by the public competition metric;
provider-derived external targets are not official competition ground truth.
"""
import numpy as np


def _runs(mask, period):
    if not len(mask): return []
    edges = np.r_[0, np.flatnonzero((mask[1:] != mask[:-1]) | (period[1:] != period[:-1])) + 1, len(mask)]
    return [(int(a), int(b)) for a, b in zip(edges[:-1], edges[1:]) if mask[a]]


def evaluate(target, prediction, period):
    y, p, period = np.asarray(target), np.asarray(prediction), np.asarray(period)
    if (y.ndim != 1 or y.shape != p.shape or y.shape != period.shape
            or not np.isin(y, ('H','A','D','X')).all() or not np.isin(p, ('H','A','D','X')).all()):
        raise ValueError('Aligned H/A/D/X evaluation arrays required')
    known = (y != 'X') & np.isin(period, (1,2))
    blocks = _runs(known, period)
    filled = p.copy()
    for a,b in blocks:
        ids = np.flatnonzero(p[a:b] != 'X')
        if not len(ids): continue
        index = np.maximum.accumulate(np.where(p[a:b] != 'X', np.arange(b-a), -1))
        index[index < 0] = ids[0]
        filled[a:b] = p[a:b][index]
    per_class = {}
    for label in ('H','A','D'):
        tp = int(np.sum(known & (y == label) & (p == label)))
        fp = int(np.sum(known & (y != label) & (p == label)))
        fn = int(np.sum(known & (y == label) & (p != label)))
        per_class[label] = {'precision':tp/max(1,tp+fp), 'recall':tp/max(1,tp+fn),
                            'f1':2*tp/max(1,2*tp+fp+fn), 'tp':tp, 'fp':fp, 'fn':fn}
    values = []
    for threshold in (.3,.4,.5,.6,.7):
        hits = ng = npred = 0
        for a,b in blocks:
            for label in ('H','A'):
                gt = _runs(y[a:b] == label, period[a:b])
                ps = _runs(filled[a:b] == label, period[a:b])
                ng += len(gt); npred += len(ps)
                i = j = 0; pairs = []
                while i < len(gt) and j < len(ps):
                    l,r = gt[i]; c,d = ps[j]
                    overlap = max(0, min(r,d)-max(l,c))
                    iou = overlap/(max(r,d)-min(l,c))
                    if iou >= threshold: pairs.append((iou,i,j))
                    if r <= d: i += 1
                    else: j += 1
                used_g, used_p = set(), set()
                for _,i,j in sorted(pairs, reverse=True):
                    if i not in used_g and j not in used_p:
                        used_g.add(i); used_p.add(j); hits += 1
        values.append(2*hits/max(1,ng+npred))
    return {'macro_f1_HAD':float(np.mean([v['f1'] for v in per_class.values()])),
            'per_class':per_class,'external_spell_f1':float(np.mean(values)),
            'known_target_frames':int(known.sum()),
            'frame_agreement':float(np.mean(y[known] == p[known])) if known.any() else None,
            'competition_score':False}
