"""Frozen model bundle: exported trees + feature layout + decoder costs, numpy-only, no pickle."""
import json
import hashlib
from pathlib import Path
import numpy as np
from .trees import FIELDS

KEYS = FIELDS + ('offsets', 'baseline')


def save(path, dead, home, feature_names, decoder, card, stack=None):
    """stack: optional (stack_dead, stack_home, stack_feature_names) second stage."""
    arrays = {}
    models = [('dead', dead), ('home', home)]
    if stack is not None:
        models += [('stack_dead', stack[0]), ('stack_home', stack[1])]
        arrays['stack_feature_names'] = np.array(json.dumps(stack[2]))
    for tag, model in models:
        for k in KEYS:
            arrays[f'{tag}__{k}'] = np.asarray(model[k])
    arrays['feature_names'] = np.array(json.dumps(feature_names))
    arrays['decoder'] = np.array(json.dumps(decoder, sort_keys=True))
    arrays['card'] = np.array(json.dumps(card, sort_keys=True))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        np.savez_compressed(f, **arrays)


def load(path):
    z = np.load(path, allow_pickle=False)
    out = {'dead': {k: z[f'dead__{k}'] for k in KEYS}, 'home': {k: z[f'home__{k}'] for k in KEYS},
           'feature_names': json.loads(str(z['feature_names'])),
           'decoder': json.loads(str(z['decoder'])), 'card': json.loads(str(z['card']))}
    if 'stack_feature_names' in z.files:
        for tag in ('stack_dead', 'stack_home'):
            out[tag] = {k: z[f'{tag}__{k}'] for k in KEYS}
        out['stack_feature_names'] = json.loads(str(z['stack_feature_names']))
    out['sha256'] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return out
