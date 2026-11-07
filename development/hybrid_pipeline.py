"""Experimental motion pipeline with tactical-first hybrid measurement input."""
from .hybrid_tracking import fuse
from .motion_possession import predict


def predict_hybrid(tactical, broadcast, alignment, view, hybrid_config,
                   tactical_baseline_labels, motion_config, **motion_options):
    overlay = fuse(tactical, broadcast, alignment, view, hybrid_config)
    result = predict(overlay['inputs'], tactical_baseline_labels, motion_config, **motion_options)
    result['hybrid'] = overlay
    return result
