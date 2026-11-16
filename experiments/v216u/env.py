"""Local shim to run the team's v2 experiment harness (wt-ata) on this machine. External matches only."""
import sys, types, warnings
warnings.filterwarnings('ignore')
ROOT = '/Users/umut/BARCELONA/'
EXP = ROOT + 'wt-ata/experiments/possession_v2/'
for p in (EXP + 'v215', EXP + 'v214', EXP + 'v213', EXP, ROOT + 'wt-ata'):
    sys.path.insert(0, p)
import harness
harness.DFL = ROOT + 'ext_data/dfl_prepared/'
harness.MET = ROOT + 'work/v216u/met/'
# exp_v25 loads the four-match validation models (not in the repository) at import; only its constants are needed here
stub = types.ModuleType('exp_v25')
stub.PATHS = {'v2.1': (None, None, {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}),
              'v2.3': (None, None, {'switch': 5, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3})}
stub.MODELS, stub.run_path, stub.quality = {}, None, None
sys.modules['exp_v25'] = stub
import exp_v213 as E
import pooling
from possession.decode import emissions, decode_blocks
from possession.features import play_blocks
from tcn import infer as tinfer, decode as tdecode, fuse as tfuse, features as tfeat, degrade as tdegrade

# real broadcast-quality sampler of exp_v25 (its module cannot be imported: it loads pickles at import)
import synth_broadcast as _sb
_REG = {'good': ((0.0, 0.2), (0.05, 0.25), (0.05, 0.25)), 'medium': ((0.2, 0.6), (0.25, 0.5), (0.25, 0.5))}
def _quality(rng, regime):
    q = _sb.sample_quality(rng, 'default')
    (b0, b1), (s0, s1), (p0, p1) = _REG[regime]
    q.update(bias_sd=float(rng.uniform(b0, b1)), b_sd=float(rng.uniform(s0, s1)), p_sd=float(rng.uniform(p0, p1)))
    return q
stub.quality = _quality
E.quality = _quality
