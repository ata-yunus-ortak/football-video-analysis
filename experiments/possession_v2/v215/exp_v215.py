"""v2.15 validation (possession-v215-plan.json): possession-v2.11 vs the pooled system of the v2.14 candidate with a
smaller weight for the network. Everything is the v2.14 validation (v214/exp_v214.py: the same six weight files, the
same arithmetic pool, the unchanged v2 decoder, no pooling on the v2.3 path; copies, conditions and the v2_11 arm from
v213/exp_v213.py, imported unchanged) except
  weight    pooling.WEIGHT (fixed in the plan; v2.14 used 0.5),
  seeds     a third set: copy 19100 + 10 * match_index + j; broadcast stream 49100 + 100 * regime_index + 2 * match_index
            + j; clock 59100 + 100 * regime_index + 2 * match_index + j; teammate's simulator 69100 + match_index;
            Metrica game 3 after the decision: copy 39103, copy index 8, teammate's simulator 69108.
Systems: v2_11, fused (the candidate), tcn_alone (reported).
Usage: /usr/bin/python3 exp_v215.py PART     PART = 0 | 1 | 2 | 3 (validation match index) | reserved | smoke
(smoke: wiring check on training match J03WOH, in-sample for every model; it computes NO score)
"""
import sys, json, os, platform, hashlib, time, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work'); sys.path.insert(0, '/home/claude/work/v213')
import exp_v213 as E
from possession.decode import emissions, decode_blocks
from possession.features import play_blocks
from tcn import infer as tinfer, fuse as tfuse, decode as tdecode
sys.path.insert(0, '/home/claude/work/v215')
import pooling

V214 = '/home/claude/work/v214/'          # the weight files (unchanged since the v2.14 validation)
V215 = '/home/claude/work/v215/'
SEED, STREAM, CLOCK, SIM2, RESERVED_SEED = 19100, 49100, 59100, 69100, 39103
DFL4 = ['dfl4_both_s0.npz', 'dfl4_both_s1.npz', 'dfl4_both_s2.npz']
DFL6 = ['dfl6_both_s0.npz', 'dfl6_both_s1.npz', 'dfl6_both_s2.npz']
WEIGHTS = {'J03WN1': DFL4, 'J03WR9': DFL4, 'J03WOH': DFL6, 'MET1': DFL6, 'MET2': DFL6, 'MET3': DFL6}
LETTERS = np.array(['H', 'A', 'D'])
_MEM = {}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()

# the copies are built by exp_v213.copy_rows, which reads these module constants when it runs
E.STREAM, E.CLOCK = STREAM, CLOCK


def members(name):
    key = tuple(WEIGHTS[name])
    if key not in _MEM:
        _MEM[key] = sum((tinfer.load_weights(V214 + 'tcn_weights/' + f) for f in key), [])
    return _MEM[key]


def fused_labels(mem, m_in, period, p_dead, p_home, path, decoder):
    """(fused labels or None on the v2.3 path, TCN-alone labels). The TCN runs on every play block on its own; the
    pooled probabilities (pooling.pool) go through possession.decode with the decoder constants of the path."""
    n = len(period)
    alone = np.full(n, 'D', dtype='<U1')
    tcn = np.full((n, 3), 1.0 / 3.0)
    for a, b in play_blocks(period):
        prob = tinfer.probabilities(mem, *E.tcn_arrays(m_in, a, b))
        alone[a:b] = LETTERS[tdecode.decode(prob, tfuse.SWITCH_COST, tinfer.STRIDE, b - a)]
        tcn[a:b] = tdecode.upsample(np.asarray(prob, np.float64), tinfer.STRIDE, b - a)
    if path != 'v2.1':
        return None, alone
    pd2, ph2 = pooling.pool(tcn, p_dead, p_home)
    return decode_blocks(emissions(pd2, ph2), period, decoder), alone


def row_for(name, key, cond, path, base_input, lab, per, check=False, extra=None, with_scores=True):
    t0 = time.time()
    decoder = E.PATHS[path][2]
    if E.V2_SIDE[name] == 'validation models':
        p11, pd_, ph = E.v2_validation(path, base_input, per)
    else:
        p11, pd_, ph = E.v2_released(path, base_input)
        assert E.bundle(path)['decoder'] == decoder, 'the released bundle decodes with other constants'
    t1 = time.time()
    fus, alone = fused_labels(members(name), base_input, per, pd_, ph, path, decoder)
    fused_used = fus is not None
    if not fused_used:
        fus = p11
    row = {'copy': key, 'condition': cond, 'path': path, 'v2_side': E.V2_SIDE[name], 'tcn_weights': WEIGHTS[name],
           'fused_on_this_path': fused_used}
    play = per > 0
    if with_scores:
        r11, rf, ra = E.metrics(lab, p11, per), E.metrics(lab, fus, per), E.metrics(lab, alone, per)
        if check:      # the v2_11 arm with validation models is exactly exp_v25.run_path, as in every earlier validation
            ref = E.run_path(path, base_input, lab, per)
            assert abs(ref[0] - r11['spell_f1']) < 1e-12 and abs(ref[1] - r11['macro_f1']) < 1e-12, (ref, r11)
        row.update(v2_11=r11, fused=rf, tcn_alone=ra, diff_spell_f1=rf['spell_f1'] - r11['spell_f1'],
                   diff_macro_f1=rf['macro_f1'] - r11['macro_f1'])
    else:              # smoke: wiring only, nothing is compared with labels
        assert set(np.unique(fus)) <= {'H', 'A', 'D'} and set(np.unique(alone)) <= {'H', 'A', 'D'}
        assert (fus[~play] == 'D').all() and len(fus) == len(p11) == len(per)
        row.update(label_shares_in_play={k: {c: round(float(np.mean(v[play] == c)), 3) for c in 'HAD'}
                                         for k, v in (('v2_11', p11), ('fused', fus), ('tcn_alone', alone))})
    row['frames_changed'] = int(np.sum(p11 != fus))
    if extra:
        row.update(extra)
    row['seconds_v2'], row['seconds_tcn'] = round(t1 - t0), round(time.time() - t1)
    return row


E.row_for = row_for                    # exp_v213.copy_rows calls the module-level row_for


if __name__ == '__main__':
    import pandas, sklearn
    assert pooling.POOL in ('arithmetic', 'geometric') and pooling.WEIGHT is not None, 'the candidate is not fixed'
    part = sys.argv[1]
    OUT = f'{V215}exp_v215_{part}.json'
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': []}
    res['environment'] = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pandas.__version__,
                          'scikit_learn': sklearn.__version__}
    res['fusion'] = {'pool': pooling.POOL, 'weight': pooling.WEIGHT, 'decoder': 'possession.decode with the constants of the path',
                     'fused_paths': ['v2.1'], 'stride': tinfer.STRIDE, 'prob_decimals': tinfer.PROB_DECIMALS}
    res['sha256'] = {'weights': {w: sha(V214 + 'tcn_weights/' + w) for w in DFL4 + DFL6},
                     'tcn_modules': {f: sha('/home/claude/work/v213/tcn/' + f) for f in ('infer.py', 'features.py', 'decode.py', 'fuse.py', 'degrade.py')},
                     'exp_v213.py': sha('/home/claude/work/v213/exp_v213.py'), 'exp_v215.py': sha(V215 + 'exp_v215.py'),
                     'pooling.py': sha(V215 + 'pooling.py')}
    done = {(r['copy'], r['condition']) for r in res['rows']}
    if part == 'reserved':
        E.copy_rows('MET3', RESERVED_SEED, 8, res, OUT, done, ('tactical', 'fill_good', 'fill_medium', 'view42'), sim2_seed=SIM2 + 8)
    elif part == 'smoke':      # wiring check on a TRAINING match, in-sample for every model; no score is computed
        E.copy_rows('J03WOH', 1, 99, res, OUT, done, ('tactical', 'fill_good'), with_scores=False, sim2_seed=99)
        m, lab = E.load('J03WOH')
        rng = np.random.default_rng(1)
        fixed, _ = E.keeper2.correct_goalkeepers(E.packed(E.degrade(m, lab, rng, E.sample_params(rng, ranges=E.RANGES))))
        # the code paths the copy above did not take: the v2.3 path (not pooled) of both model sets and the released bundles
        for side, path in (('validation models', 'v2.3'), ('released bundles', 'v2.1'), ('released bundles', 'v2.3')):
            key = f'J03WOH|1|forced {side} {path}'
            if (key, 'tactical') in done:
                continue
            E.V2_SIDE['J03WOH'] = side
            row = row_for('J03WOH', key, 'tactical', path, fixed, lab, m['period'], with_scores=False)
            assert row['fused_on_this_path'] == (path == 'v2.1') and (row['frames_changed'] == 0) == (path != 'v2.1')
            res['rows'].append(row); E.save(res, OUT)
            print(key, row['frames_changed'], flush=True)
    else:
        i = int(part)
        for j in E.COPIES_TACTICAL:
            conds = ('tactical',) + (('fill_good', 'fill_medium', 'view42') if j in E.COPIES_OTHER else ())
            E.copy_rows(E.NAMES[i], SEED + 10 * i + j, 2 * i + j, res, OUT, done, conds, sim2_seed=(SIM2 + i) if j == 0 else None)
    E.save(res, OUT)
    print('V215DONE', part, flush=True)
