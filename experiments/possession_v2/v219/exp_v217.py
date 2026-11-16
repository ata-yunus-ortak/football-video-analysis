"""v2.17 validation (possession-v217-plan.json): possession-v2.16 against the same system with another second model.
  arms        v2_16      the release: three network members (dfl4_both_s0-2 on the DFL rows, dfl6_both_s0-2 on the Metrica
                         rows; 37 features; tcn/infer.py of commit 167dc7b), network weight 0.2 (v215/exp_v215.fused_labels,
                         unchanged)
              candidate  eight network members of the team member's branch mtah-possession, commit 74bedbf (d4_a_s0-3 +
                         d4_f_s0-3 on the DFL rows, d6_a_s0-3 + d6_f_s0-3 on the Metrica rows; four on the 37 features of
                         features.py, four on the 71 features of features2.py; infer.py of commit 74bedbf, byte copies
                         under v219/tcn2/), network weight 0.4
  Both arms share the copy, the model input, the probabilities of the v2 models, the arithmetic pool (pooling.pool) and
  the decoder of the path. On the v2.3 path neither arm pools: both are the v2.11 output.
  conditions  tactical        16 copies (j = 0..3): tactical camera only
              fill_good        8 copies (j = 0, 1): simulated broadcast stream, regime good; model input as possession.run216
                               (ball filled behind the gate, lost players added: v218/exp_v216.stream and arms, unchanged)
              fill_medium      8 copies (j = 0, 1): regime medium
              tactical_sim2    4 copies (one per match): tactical copy made with the team member's simulator
  seeds       copy 29100 + 10 * match_index + j; stream 54100 + 100 * regime_index + 4 * match_index + j (good 0,
              medium 1); clock readings 84100 + the same offset; other simulator 94100 + match_index
Usage: /usr/bin/python3 exp_v217.py PART     PART = 0 | 1 | 2 | 3 (match index) | wiring_met | wiring_dfl | wiring_fill
(wiring_*: copies of earlier validations, to check that this script reproduces known rows; no copy of this validation)"""
import sys, json, os, time, platform, hashlib, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/work/v219'); sys.path.insert(0, '/home/claude/work/v218'); sys.path.insert(0, '/home/claude/sc')
import exp_v216 as G                                    # stream(), arms(): the model input of possession-v2.16
C, X = G.C, G.X                                         # v218/cam1.py, v215/exp_v215.py
E = X.E                                                 # v213/exp_v213.py
from possession.decode import emissions, decode_blocks
from possession.features import play_blocks
from tcn import fuse as tfuse, decode as tdecode        # byte copies of commit 167dc7b (v213/tcn)
from tcn2 import infer as tinfer2                       # byte copies of commit 74bedbf (v219/tcn2)

V = '/home/claude/work/v219/'
SEED, STREAM, CLOCK, SIM2 = 29100, 54100, 84100, 94100
NAMES = ['J03WN1', 'J03WR9', 'MET1', 'MET2']
RI = {'good': 0, 'medium': 1}
ARMS = ('v2_16', 'candidate')
CAND_WEIGHT = 0.4
STEMS = ['a_s0', 'a_s1', 'a_s2', 'a_s3', 'f_s0', 'f_s1', 'f_s2', 'f_s3']
CAND = {n: [('d4_' if n.startswith('J03') else 'd6_') + s + '.npz' for s in STEMS] for n in NAMES}
_MEM = {}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def cand_members(name):
    key = tuple(CAND[name])
    if key not in _MEM:
        _MEM[key] = sum((tinfer2.load_weights(V + 'weights/' + f) for f in key), [])
        assert len(_MEM[key]) == 8 and sorted(w['stem.weight'].shape[1] for w in _MEM[key]) == [37] * 4 + [71] * 4
    return _MEM[key]


def candidate_labels(mem, m_in, period, p_dead, p_home, decoder):
    """(pooled labels, network-alone labels) of the candidate; the network runs on every play block on its own."""
    n = len(period)
    alone = np.full(n, 'D', dtype='<U1')
    tcn = np.full((n, 3), 1.0 / 3.0)
    for a, b in play_blocks(period):
        prob = tinfer2.probabilities(mem, *E.tcn_arrays(m_in, a, b))
        alone[a:b] = X.LETTERS[tdecode.decode(prob, tfuse.SWITCH_COST, tinfer2.STRIDE, b - a)]
        tcn[a:b] = tdecode.upsample(np.asarray(prob, np.float64), tinfer2.STRIDE, b - a)
    pd2, ph2 = X.pooling.pool(tcn, p_dead, p_home, weight=CAND_WEIGHT)
    return decode_blocks(emissions(pd2, ph2), period, decoder), alone


def rows_for(name, key, cond, path, base_input, lab, per):
    """One row per arm; the v2 models run once."""
    t0 = time.time()
    decoder = E.PATHS[path][2]
    if E.V2_SIDE[name] == 'validation models':
        p11, pd_, ph = E.v2_validation(path, base_input, per)
    else:
        p11, pd_, ph = E.v2_released(path, base_input)
        assert E.bundle(path)['decoder'] == decoder, 'the released bundle decodes with other constants'
    r11 = E.metrics(lab, p11, per)
    t1 = time.time()
    rows, labels = [], {}
    for arm in ARMS:
        ta = time.time()
        if path != 'v2.1':
            fus, alone = p11, None
        elif arm == 'v2_16':
            fus, alone = X.fused_labels(X.members(name), base_input, per, pd_, ph, path, decoder)
        else:
            fus, alone = candidate_labels(cand_members(name), base_input, per, pd_, ph, decoder)
        labels[arm] = fus
        rows.append({'copy': key, 'condition': f'{cond}|{arm}', 'path': path, 'v2_side': E.V2_SIDE[name],
                     'tcn_weights': X.WEIGHTS[name] if arm == 'v2_16' else CAND[name],
                     'weight': X.pooling.WEIGHT if arm == 'v2_16' else CAND_WEIGHT, 'pooled_on_this_path': path == 'v2.1',
                     'v2_11': r11, 'fused': E.metrics(lab, fus, per),
                     'tcn_alone': E.metrics(lab, alone, per) if alone is not None else None,
                     'frames_changed_from_v2_11': int(np.sum(p11 != fus)),
                     'seconds_v2': round(t1 - t0), 'seconds_tcn': round(time.time() - ta)})
    rows[1]['frames_changed_from_v2_16'] = int(np.sum(labels['v2_16'] != labels['candidate']))
    return rows


def emit(res, OUT, done, rows):
    for row in rows:
        res['rows'].append(row); done.add((row['copy'], row['condition']))
    json.dump(res, open(OUT + '.tmp', 'w'), indent=0); os.replace(OUT + '.tmp', OUT)
    a, c = rows
    print(time.strftime('%H:%M:%S'), a['copy'], a['condition'].split('|')[0], a['path'], 'v2_11 %.4f' % a['v2_11']['spell_f1'],
          'v2_16 %.4f' % a['fused']['spell_f1'], 'candidate %.4f' % c['fused']['spell_f1'],
          'diff %+.4f' % (c['fused']['spell_f1'] - a['fused']['spell_f1']), a['seconds_v2'], a['seconds_tcn'], c['seconds_tcn'], 's', flush=True)


def have(done, key, cond):
    return all((key, f'{cond}|{a}') in done for a in ARMS)


def fill(res, OUT, done, name, key, m, lab, mm, path, fixed, regime, sseed, cseed, tactical_rows=None):
    cond = f'fill_{regime}'
    if have(done, key, cond):
        return
    bro2, t_of_b, fb, frep, extra = G.stream(m, lab, mm, regime, sseed, cseed)
    inp, st = G.arms(m, mm, fixed, bro2, t_of_b, fb, frep)
    del bro2
    res['stats'][f'{key}|{cond}'] = dict(st, **extra)
    if not st['gate_used'] and tactical_rows is not None:      # gate closed: the input is the tactical one
        rows = [dict(r, condition=f"{cond}|{r['condition'].split('|')[1]}") for r in tactical_rows]
    else:
        rows = rows_for(name, key, cond, path, inp['candidate'], lab, m['period'])
    emit(res, OUT, done, rows)


def tactical_copy(m, lab, seed):
    rng = np.random.default_rng(seed)
    mm = E.packed(E.degrade(m, lab, rng, E.sample_params(rng, ranges=E.RANGES)))
    path, _ = E.choose_path(E.estimate_noise(mm))
    fixed, _ = E.keeper2.correct_goalkeepers(mm)
    return mm, path, fixed


if __name__ == '__main__':
    import pandas, sklearn
    part = sys.argv[1]
    OUT = f'{V}exp_v217_{part}.json'
    res = json.load(open(OUT)) if os.path.exists(OUT) else {'rows': [], 'stats': {}}
    res['environment'] = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pandas.__version__, 'scikit_learn': sklearn.__version__,
                          'blas_threads': os.environ.get('OPENBLAS_NUM_THREADS')}
    res['sha256'] = {'candidate_weights': {f: sha(V + 'weights/' + f) for n in ('J03WN1', 'MET1') for f in CAND[n]},
                     'release_weights': {f: sha(X.V214 + 'tcn_weights/' + f) for f in X.DFL4 + X.DFL6},
                     'tcn2': {f: sha(V + 'tcn2/' + f) for f in ('__init__.py', 'infer.py', 'features.py', 'features2.py', 'decode.py')},
                     'exp_v217.py': sha(V + 'exp_v217.py'), 'exp_v216.py': sha('/home/claude/work/v218/exp_v216.py'),
                     'cam1.py': sha('/home/claude/work/v218/cam1.py'), 'exp_v215.py': sha('/home/claude/work/v215/exp_v215.py'),
                     'exp_v213.py': sha('/home/claude/work/v213/exp_v213.py'), 'pooling.py': sha('/home/claude/work/v215/pooling.py'),
                     'possession/playerfill.py': sha('/home/claude/sc/possession/playerfill.py')}
    done = {(r['copy'], r['condition']) for r in res['rows']}
    if part.startswith('wiring'):
        if part == 'wiring_fill':     # copy J03WN1|28100, condition good of the v2.16 validation: arm v2_16 must be its candidate row
            name, mi, j = 'J03WN1', 0, 0
            m, lab = E.load(name)
            mm, path, fixed = tactical_copy(m, lab, G.SEED + 10 * mi + j)
            off = 100 * G.RI['good'] + 4 * mi + j
            fill(res, OUT, done, name, f'{name}|{G.SEED + 10 * mi + j}', m, lab, mm, path, fixed, 'good', G.STREAM + off, G.CLOCK + off)
        else:                         # tactical copies of the v2.15 validation: MET1|19120, J03WN1|19100
            name, seed = ('MET1', 19120) if part == 'wiring_met' else ('J03WN1', 19100)
            m, lab = E.load(name)
            mm, path, fixed = tactical_copy(m, lab, seed)
            if not have(done, f'{name}|{seed}', 'tactical'):
                emit(res, OUT, done, rows_for(name, f'{name}|{seed}', 'tactical', path, fixed, lab, m['period']))
        print('done', flush=True)
        sys.exit(0)
    mi = int(part); name = NAMES[mi]
    m, lab = E.load(name)
    for j in (0, 1, 2, 3):
        seed = SEED + 10 * mi + j
        key = f'{name}|{seed}'
        conds = ['tactical'] + (['fill_good', 'fill_medium'] if j < 2 else [])
        if all(have(done, key, c) for c in conds):
            continue
        mm, path, fixed = tactical_copy(m, lab, seed)
        if not have(done, key, 'tactical'):
            emit(res, OUT, done, rows_for(name, key, 'tactical', path, fixed, lab, m['period']))
        tac = [r for r in res['rows'] if r['copy'] == key and r['condition'].startswith('tactical|')]
        if j < 2:
            for regime in ('good', 'medium'):
                off = 100 * RI[regime] + 4 * mi + j
                fill(res, OUT, done, name, key, m, lab, mm, path, fixed, regime, STREAM + off, CLOCK + off, tactical_rows=tac)
        del mm, fixed
    key = f'{name}|{SIM2 + mi}'
    if not have(done, key, 'tactical_sim2'):
        m2 = E.packed(E.sim2(m, SIM2 + mi))
        path2, _ = E.choose_path(E.estimate_noise(m2))
        fixed2, _ = E.keeper2.correct_goalkeepers(m2)
        emit(res, OUT, done, rows_for(name, key, 'tactical_sim2', path2, fixed2, lab, m['period']))
    print('done', flush=True)
