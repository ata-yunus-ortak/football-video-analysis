"""Transfer a known COCO ball logit into a dedicated dense ball classifier."""
import numpy as np


def transfer_array(array, source_ball_id=37, unused_bias=-10.):
    value = np.asarray(array)
    if value.ndim not in (1,2) or value.shape[0] != 91 or not np.isfinite(value).all():
        raise ValueError('Finite 91-row COCO classifier tensor required')
    if type(source_ball_id) is not int or not 0 <= source_ball_id < 91 or not np.isfinite(unused_bias):
        raise ValueError('Explicit valid source class and finite unused bias required')
    result = np.zeros((2,*value.shape[1:]),dtype=value.dtype)
    result[0] = value[source_ball_id]
    if value.ndim == 1:
        result[1] = unused_bias
    return result
