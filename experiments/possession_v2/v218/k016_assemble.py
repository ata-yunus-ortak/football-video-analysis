"""Assemble possession-k016-camera-priority.json from the development runs of 15 Nov (cam1.py, cam2.py, cam3.py):
which camera should supply a position that both see, and what else the second camera can add. Reporting only; the
registered candidate that came out of it is possession-v216-plan.json. Usage: k016_assemble.py REPO_DIR"""
import json, sys, glob, hashlib, numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
REPO = Path(sys.argv[1]); V = Path('/home/claude/work/v218')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
r4 = lambda x: round(float(x), 4)
rows, stats, pstats, dstats, env = [], {}, {}, {}, None
for f in sorted(glob.glob(str(V / 'cam1_*_*.json'))):
    d = json.loads(Path(f).read_text()); rows += d['rows']; stats.update(d['stats']); env = d['environment']
for f in sorted(glob.glob(str(V / 'cam2_*.json'))):
    d = json.loads(Path(f).read_text()); rows += d['rows']; pstats.update(d['stats'])
for f in sorted(glob.glob(str(V / 'cam3_*.json'))):
    d = json.loads(Path(f).read_text()); rows += d['rows']; dstats.update(d['stats'])
by = {(r['copy'], r['condition']): r for r in rows}
assert len(by) == len(rows)
NAMES = {'T': 'no second camera (tactical tracking only)', 'B1': 'broadcast ball where both see the ball and agree within 0.5 m',
         'B2': 'broadcast ball wherever both see the ball', 'C': 'mean of the two balls where they agree within 0.5 m',
         'P': 'B1, and tactical players replaced by their registered broadcast counterpart within 0.5 m',
         'F': 'release + broadcast players with no tactical player of either team within 1.5 m, added',
         'PF': 'P + F'}


def table(reg, ref='A'):
    out = {}
    for v in NAMES:
        d = []
        for c in sorted({c for c, k in by}):
            a = by.get((c, f'{reg}|{ref}')); x = by.get((c, 'sharp|T')) if v == 'T' else by.get((c, f'{reg}|{v}'))
            if a is not None and x is not None and not (v == 'T' and reg != 'sharp' and (c, f'{reg}|{ref}') not in by):
                d.append((c, x['fused']['spell_f1'] - a['fused']['spell_f1']))
        if d:
            v_ = np.array([x for _, x in d]); isd = np.array([c.startswith('J03') for c, _ in d])
            out[v] = {'what': NAMES[v], 'copies': len(d), 'mean': r4(v_.mean()), 'dfl': r4(v_[isd].mean()) if isd.any() else None, 'metrica': r4(v_[~isd].mean()) if (~isd).any() else None,
                      'min': r4(v_.min()), 'max': r4(v_.max()), 'better': int((v_ > 1e-9).sum()), 'worse': int((v_ < -1e-9).sum()), 'per_copy': {c: r4(x) for c, x in d}}
    return out


def usage(reg):
    ss = [v for k, v in stats.items() if k.endswith('|' + reg)]
    keys = ['share_tactical_ball', 'share_broadcast_ball', 'share_both_balls', 'share_both_within_0.5m', 'share_ball_filled_from_broadcast', 'share_no_ball_after_fill',
            'share_frames_with_an_accepted_broadcast_frame', 'median_error_m_tactical_ball_where_both', 'median_error_m_broadcast_ball_where_both', 'gate_median_distance_m']
    out = {'copies': len(ss), 'gate_open': int(sum(s['gate_used'] for s in ss))}
    out.update({k: round(float(np.mean([s[k] for s in ss if s.get(k) is not None])), 3) for k in keys})
    pp = [s['players'] for s in ss if 'players' in s]
    out['players'] = {k: round(float(np.mean([p[k] for p in pp])), 3) for k in ('share_of_tactical_player_positions_replaced', 'share_replaced_among_players_within_15m_of_the_ball',
                                                                               'median_error_m_of_replaced_tactical_positions', 'median_error_m_of_their_broadcast_positions')}
    return out


deg = []
for c in sorted({c for c, k in by if k == 'good_degraded|F'}):
    deg.append((c, by[(c, 'good_degraded|F')]['fused']['spell_f1'] - by[(c, 'good_degraded|A')]['fused']['spell_f1']))
dv = np.array([x for _, x in deg])
import pandas
out = {
 'version': 'possession-k016-camera-priority (exploration, reporting only)',
 'written_at': datetime.now(timezone(timedelta(hours=3))).isoformat(timespec='seconds'),
 'what': 'Question of the team lead (15 Nov 12:24): the broadcast camera is closer and clearer; should its tracking take priority where it agrees with the tactical tracking, also for the few players it shows? '
         'And how much of the match is taken from each camera now? Explored on development copies with a simulated second camera. The release takes everything from the tactical tracking and, behind the 0.50 m agreement gate, '
         'only the ball from the broadcast tracking where the tactical ball is missing. No plan was registered for this exploration; the one variant with a gain was then registered as possession-v216-plan.json.',
 'data': {'matches': ['J03WN1', 'J03WR9', 'MET1', 'MET2'], 'copies': 'possession.degrade, v2 profile, seed 23100 + 10 * match_index + j (j = 0, 1); packed into 46 slots; v2.15 decision in every arm',
          'second_camera': 'synth_broadcast3.simulate_warp from the clean positions: a window of 18-30 m by 12-20 m around the ball, close-ups and replays, per-shot calibration bias and warp, noise; stream seeds 53100, clock 63100. '
                           'Regimes (calibration bias, ball noise, player noise, m): sharp (0-0.05, 0.01-0.05, 0.01-0.05; new here: a stream clearly more precise than the tactical copy, whose ball noise is 0.05-0.3 and player noise 0.03-0.3), '
                           'good (0-0.2, 0.05-0.25, 0.05-0.25) and medium (0.2-0.6, 0.25-0.5, 0.25-0.5) as in the v2.5 / v2.9 / v2.15 validations',
          'unchanged_in_every_variant': 'alignment, registration, gate and ball fill of the release; noise path of the copy; models, pooling and decoders'},
 'how_much_of_each_camera_the_release_uses': {
     'by_design': 'tactical tracking: every frame, all players and the ball. Broadcast tracking: the ball only, on frames where the tactical ball is missing, an accepted broadcast frame exists and the gate is open; broadcast players only to measure the calibration error. Video pixels: the match clock only.',
     'simulated_copies_share_of_graded_frames': {reg: usage(reg) for reg in ('sharp', 'good', 'medium')},
     'provided_match': 'not known to this record: the provided data are not read by the agent, and aggregates computed on them are not copied into files. DATA.md publishes: tactical ball in 56.9% of frames, broadcast ball in 50.5% of its frames, broadcast homography usable on 65.8% of its rows.'},
 'spell_f1_difference_to_the_release_by_stream_regime': {reg: table(reg) for reg in ('sharp', 'good', 'medium')},
 'added_players_statistics': {k: v for k, v in pstats.items()},
 'stream_that_loses_and_invents_players': {
     'what': 'regime good with the broadcast players degraded before the alignment (cam3.degrade_bro, fixed before its rows were computed): each track missing 10% of the time and in 25% of close encounters, four ghost tracks '
             '(copies of visible players displaced by 2-5 m, 30% under the other team), two more tracks under the wrong team; arms: release and F',
     'F_minus_release': {'copies': len(dv), 'mean': r4(dv.mean()), 'min': r4(dv.min()), 'max': r4(dv.max()), 'per_copy': {c: r4(x) for c, x in deg}},
     'statistics': dstats},
 'conclusions': [
     'Taking a position from the broadcast stream where both cameras have it and agree does not help: the ball -0.001 (sharp), +0.001 (good), -0.005 (medium); ball and players +0.002, 0.000, -0.004; always the broadcast ball -0.002 / -0.005; '
     'the mean of the two balls -0.005 / 0.000. This holds for a stream five times as precise as the tactical copy (ball error 0.03 m against 0.15 m; players 0.04 m against 0.13 m). Where two measurements agree within half a metre, '
     'choosing between them changes little, and precision below the level the models were trained with is not what limits them.',
     'The second camera matters through what the first does not see: without it the score is 0.036-0.043 lower on these copies (all 8 lower). On the simulated copies the tactical ball is there on 46% of graded frames, '
     'the broadcast ball adds 15-17%, and on 38-40% neither camera has it; both have it on 22-25%.',
     'Players that the tactical copy has lost and the broadcast stream sees: adding them (F) gained +0.0057 (sharp) and +0.0097 (good) on four copies, and +0.0069 with a stream that itself loses and invents players, '
     'where only 41-67% of the added positions are real players. 9 of the 12 comparisons better, worst -0.0027. Replacing positions as well (PF) was not clearly better and moves tactical positions.',
     'F was registered as a candidate with the gates of the earlier plans (possession-v216-plan.json).'],
 'limits': ['Four development copies per comparison (eight for B1 and P in two regimes); differences under about 0.005 are within the spread between copies.',
            'The second camera is simulated from clean positions. How the provided broadcast tracking behaves was not looked at.',
            'Agreement with other providers labels on corrupted external copies; not a competition score.'],
 'scripts_sha256': {n: sha(V / n) for n in ('cam1.py', 'cam2.py', 'cam3.py', 'sum1.py', 'k016_assemble.py')},
 'environment': dict(env, pandas=pandas.__version__),
 'provided_fixture_used': False}
(REPO / 'possession-k016-camera-priority.json').write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
t = out['spell_f1_difference_to_the_release_by_stream_regime']
for reg in t:
    print(reg, {v: (x['copies'], x['mean'], x['better'], x['worse']) for v, x in t[reg].items()})
print(out['stream_that_loses_and_invents_players']['F_minus_release'])
print(json.dumps(out['how_much_of_each_camera_the_release_uses']['simulated_copies_share_of_graded_frames']['good'], indent=0)[:900])
