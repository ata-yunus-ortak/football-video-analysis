"""Descriptive one-to-one box coverage, not official AP/HOTA or possession accuracy."""
import math


def valid_box(box):
    return (len(box) == 4 and all(math.isfinite(x) for x in box)
            and box[2] > box[0] and box[3] > box[1])


def iou(a, b):
    if not valid_box(a) or not valid_box(b): raise ValueError('Finite positive xyxy boxes required')
    intersection = max(0., min(a[2], b[2]) - max(a[0], b[0])) * max(0., min(a[3], b[3]) - max(a[1], b[1]))
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection
    return intersection / union


def match_boxes(predictions, references, threshold):
    if not math.isfinite(threshold) or not 0 < threshold <= 1:
        raise ValueError('Explicit IoU threshold in (0,1] required')
    if any(not valid_box(r['box_xyxy']) or not math.isfinite(r['confidence'])
           or not 0 <= r['confidence'] <= 1 for r in predictions):
        raise ValueError('Valid predicted box/confidence required')
    if any(not valid_box(r['box_xyxy']) for r in references):
        raise ValueError('Valid reference box required')
    remaining, pairs = set(range(len(references))), []
    for p in sorted(range(len(predictions)), key=lambda k: (-predictions[k]['confidence'], k)):
        choices = [(iou(predictions[p]['box_xyxy'], references[g]['box_xyxy']), g) for g in sorted(remaining)]
        if not choices: break
        overlap, g = max(choices, key=lambda item: (item[0], -item[1]))
        if overlap >= threshold:
            pairs.append({'prediction': p, 'reference': g, 'iou': overlap})
            remaining.remove(g)
    return {'matches': pairs, 'reference_count': len(references),
            'prediction_count': len(predictions), 'unmatched_references': len(remaining),
            'unmatched_predictions': len(predictions) - len(pairs)}
