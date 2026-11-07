"""External proposal filtering; never promotes a proposal to an in-play ball."""
import math
import numpy as np
from .vision_box_audit import valid_box
from . import learned_dead_ball as logistic

FEATURE_NAMES = ['confidence', 'log_aspect', 'log_area_fraction',
                 'log_nearest_foot_distance_in_heights', 'log_height_ratio']


def features(box, confidence, person_boxes, image_size):
    if not valid_box(box) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError('Finite box and confidence required')
    iw, ih = image_size
    if not all(math.isfinite(v) and v > 0 for v in (iw, ih)):
        raise ValueError('Positive image dimensions required')
    if any(not valid_box(p) for p in person_boxes):
        raise ValueError('Invalid person box')
    x1, y1, x2, y2 = box
    w, h = x2-x1, y2-y1
    cx, cy = (x1+x2)/2, (y1+y2)/2
    # Stable geometric tie-break makes detection ordering irrelevant.
    candidates = sorted((math.hypot(cx-(p[0]+p[2])/2, cy-p[3])/(p[3]-p[1]),
                         tuple(p)) for p in person_boxes)
    if candidates:
        distance, p = candidates[0]
        context = [math.log1p(distance), math.log(h/(p[3]-p[1]))]
    else:
        context = [float('nan'), float('nan')]
    return [confidence, math.log(w/h), math.log(w*h/(iw*ih)), *context]


def fit(raw, target, weights, l2):
    if np.asarray(raw).ndim != 2 or np.shape(raw)[1] != len(FEATURE_NAMES):
        raise ValueError('Candidate feature schema required')
    if set(np.asarray(target).tolist()) != {0, 1}:
        raise ValueError('Both training classes required')
    model = logistic.fit(raw, target, weights, l2)
    model.update(feature_names=FEATURE_NAMES, model_family='ball-proposal-filter-v1')
    return model


def probability(raw, model):
    if model.get('model_family') != 'ball-proposal-filter-v1' or model['feature_names'] != FEATURE_NAMES:
        raise ValueError('Candidate model schema required')
    if np.asarray(raw).ndim != 2 or np.shape(raw)[1] != len(FEATURE_NAMES):
        raise ValueError('Candidate feature schema required')
    return logistic.sigmoid(logistic.design(raw, np.asarray(model['median']),
        np.asarray(model['scale'])) @ np.asarray(model['coefficients']))
