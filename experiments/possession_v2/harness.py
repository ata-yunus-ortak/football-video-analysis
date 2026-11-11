import sys, os, json, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from possession.data import read_dfl_prepared, read_metrica_csv, read_epts
from possession.features import features
import possession.features as _F
from possession.degrade import degrade
from metrica_labels import labels_from_events, game3_events_df

DFL = '/mnt/user-data/uploads/sportec-development-20261107/prepared-v1/'
MET = '/home/claude/ext/metrica/data/'
CACHE = '/home/claude/work/cache/'
DFL_TRAIN = ['J03WOH', 'J03WOY', 'J03WPY', 'J03WQQ']
DFL_VAL = ['J03WN1', 'J03WR9']
MET_VAL = ['MET1', 'MET2']
_MEM = {}

def load(name):
    if name in _MEM:
        return _MEM[name]
    if name.startswith('J03'):
        m, lab = read_dfl_prepared(DFL + name)
    elif name in ('MET1', 'MET2'):
        g = name[-1]
        base = f'{MET}Sample_Game_{g}/Sample_Game_{g}_'
        m = read_metrica_csv(base + 'RawTrackingData_Home_Team.csv', base + 'RawTrackingData_Away_Team.csv')
        ev = pd.read_csv(base + 'RawEventsData.csv')
        lab, _ = labels_from_events(ev, len(m['period']))
    elif name == 'MET3':
        m, info = read_epts('/home/claude/ext/sd/data/Sample_Game_3/Sample_Game_3_metadata.xml',
                            '/home/claude/ext/sd/data/Sample_Game_3/Sample_Game_3_tracking.txt')
        p = info['provider_parameters']
        per = np.zeros(len(m['ball']), np.int8)
        a1, b1, a2, b2 = (int(p[k]) for k in ('first_half_start', 'first_half_end', 'second_half_start', 'second_half_end'))
        per[a1 - 1:b1] = 1; per[a2 - 1:b2] = 2
        m['period'] = per
        ev = game3_events_df('/home/claude/ext/sd/data/Sample_Game_3/Sample_Game_3_events.json')
        lab, _ = labels_from_events(ev, len(per))
    else:
        raise KeyError(name)
    _MEM.clear(); _MEM[name] = (m, lab)
    return m, lab

def degraded(name, seed, params=None):
    m, lab = load(name)
    return degrade(m, lab, np.random.default_rng(seed), params) if seed >= 0 else m

def feats(name, seed, swap, tag=None):
    if tag is None:
        tag = '' if getattr(_F, 'FEATURE_VERSION', 1) == 1 else f'_f{_F.FEATURE_VERSION}'
    path = f'{CACHE}{name}_s{seed}_w{int(swap)}{tag}.npy'
    if os.path.exists(path):
        return np.load(path)
    X, names = features(degraded(name, seed), swap=swap)
    np.save(path, X)
    json.dump(names, open(CACHE + f'names{tag}.json', 'w'))
    return X

def names(tag=''):
    return json.load(open(CACHE + f'names{tag}.json'))
