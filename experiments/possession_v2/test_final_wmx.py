"""Final fresh test on DFL J03WMX (never downloaded before the freeze), once, with the FROZEN release:
v2.1 vs v2.4 vs v2.5 on corrupted copies (v2.1 corruption, extended ball, extended players) x simulated
broadcast accuracy regimes (good / medium / bad), with simulated clock readings. Reported, not a gate.
Usage: test_final_wmx.py <prepared J03WMX dir>"""
import sys, json, subprocess, time, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work')
from possession.data import read_dfl_prepared
from possession.degrade import degrade, sample_params, RANGES
from possession.bundle import load as load_bundle
from possession.pipeline import predict_labels
from possession.smooth import smooth_positions
from possession.noise import estimate_noise, choose_path
from possession.fusion import align_auto, fuse_gated
from possession.clocksync import half_lags
from possession.features import play_blocks
from possession.evaluate import score
from possession import run25
import synth_broadcast2 as sb2
import synth_clock as sc
from exp_v25 import quality, REGIMES

S = '/home/claude/sc/'
m, lab = read_dfl_prepared(sys.argv[1])
per, fps = m['period'], float(m['fps'])
blocks = play_blocks(per)
halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(blocks)]
graded = per > 0
b21, b23 = load_bundle(S + 'models/possession-v2.npz'), load_bundle(S + 'models/possession-v23.npz')
half = int(b23['card']['smooth_half'])
PROF = {'v2': (RANGES, (7101, 7102)), 'ext_ball': (dict(RANGES, ball_sigma_m=(0.3, 0.6), ball_bias_sd_m=(0.2, 0.6), ball_bias_tau_s=(1.0, 10.0)), (7301, 7302)),
        'ext_players': (dict(RANGES, player_sigma_m=(0.3, 0.6)), (7501, 7502))}


def path_labels(path, mm):
    return predict_labels(smooth_positions(mm, half), b23)[0] if path == 'v2.3' else predict_labels(mm, b21)[0]


out = {'fixture': 'DFL J03WMX (reserved; first and only use)', 'run_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
       'release': json.load(open(S + 'possession-v25-release.json')), 'use_clock': run25.USE_CLOCK, 'cases': []}
ci = 0
for prof, (ranges, seeds) in PROF.items():
    for seed in seeds:
        rng = np.random.default_rng(seed)
        dm = degrade(m, lab, rng, sample_params(rng, ranges=ranges))
        path, _ = choose_path(estimate_noise(dm))
        r21 = score(lab, predict_labels(dm, b21)[0], per)
        r24 = score(lab, path_labels(path, dm), per) if path == 'v2.3' else r21
        for ri, regime in enumerate(REGIMES):
            rb = np.random.default_rng(39000 + 100 * ri + ci)
            q = quality(rb, regime)
            bro, valid, true_t, clock_t = sb2.simulate_with_clock(m, lab, rb, q)
            rc = np.random.default_rng(49000 + 100 * ri + ci)
            lags = {}
            if run25.USE_CLOCK:
                obs_t = sc.observations(np.arange(len(m['ball'])), blocks, fps, rc, 0.8, 0.02)
                obs_b = sc.observations(clock_t, blocks, fps, rc, 0.8, 0.02)
                lags, _ = half_lags(obs_t, obs_b, fps, halves)
            bro2, t_of_b, arep = align_auto(dm, bro, valid, fps, m['pitch'], halves, clock_lags=lags)
            fb, frep = fuse_gated(dm['ball'], bro2['ball'], t_of_b, fps, graded)
            r25 = score(lab, path_labels(path, dict(dm, ball=fb)), per) if frep['used'] else r24
            case = {'corruption': prof, 'seed': seed, 'regime': regime, 'path': path, 'alignment_mode': arep['mode'],
                    'fill_used': frep['used'], 'median_distance_m': frep.get('median_distance_m'),
                    **{k: {'spell_f1': round(r['spell_f1_mean'], 4), 'macro_f1': round(r['macro_f1'], 4)} for k, r in (('v2.1', r21), ('v2.4', r24), ('v2.5', r25))}}
            out['cases'].append(case)
            print(prof, seed, regime, path, 'v2.1 %.4f v2.4 %.4f v2.5 %.4f' % (r21['spell_f1_mean'], r24['spell_f1_mean'], r25['spell_f1_mean']), 'fill', frep['used'], flush=True)
        ci += 1
mean = lambda k, sel: round(float(np.mean([c[k]['spell_f1'] for c in sel])), 4)
out['mean'] = {f'{prof}|{regime}': {k: mean(k, [c for c in out['cases'] if c['corruption'] == prof and c['regime'] == regime]) for k in ('v2.1', 'v2.4', 'v2.5')}
               for prof in PROF for regime in REGIMES}
out['mean_all'] = {k: mean(k, out['cases']) for k in ('v2.1', 'v2.4', 'v2.5')}
json.dump(out, open('/home/claude/work/final_test_wmx.json', 'w'), indent=1)
print('SUMMARY', json.dumps(out['mean_all']), flush=True)
