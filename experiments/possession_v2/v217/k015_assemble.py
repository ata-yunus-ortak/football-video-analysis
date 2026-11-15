"""Assemble possession-k015-tag-rescue.json from the development analyses of 15 Nov (rest1.py, rest2.py, orc1.py, taglib.py,
rule1.py, team1.py). Reporting only: no plan was registered, nothing was validated, nothing was selected.
Usage: k015_assemble.py REPO_DIR"""
import json, sys, hashlib, platform, numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, '/home/claude/work/v217')
import taglib as T
E = T.E
REPO = Path(sys.argv[1]); V = Path('/home/claude/work/v217')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
r4 = lambda x: round(float(x), 4)
R = json.load(open(V / 'restarts.json'))
# the restarts were taken from labels recomputed today; they must be those of the stored copies
for f in E.copies():
    d = E.load(f)
    for s, t, typ, p, n, first in R[d['match']]['restarts']:
        assert (d['lab'][s:t] == 'D').all() and d['lab'][t] == n and (s == 0 or d['lab'][s - 1] != 'D' or d['per'][s - 1] != d['per'][s]), (d['key'], s, t)
a = np.load(V / 'rest2.npy')
FIRST = {(m, s) for m in R for s, t, typ, p, n, first in R[m]['restarts'] if first}      # a D frame at the very start of a half is not a stoppage in play
a = a[[(str(m), int(s)) not in FIRST for m, s in zip(a['match'], a['s'])]]
dur = (a['t'] - a['s']) / 25.0; miss = a['cov'] == 0
ncop = len(set(a['key']))
by_type = {typ: {'per_copy': round(float((a['typ'] == typ).sum() / ncop), 1), 'no_D_of_ours_on_the_stretch': r4(miss[a['typ'] == typ].mean()),
                 'median_length_s': round(float(np.median(dur[a['typ'] == typ])), 1), 'published_tags_of_this_type_in_the_provided_file': T.PUB[typ]}
           for typ in ('throw-in', 'corner kick', 'goal kick', 'free kick', 'kick off')}
by_len = {f'{lo}-{hi} s' if hi < 1e8 else f'over {lo} s': {'share': r4(m.mean()), 'no_D_of_ours_on_the_stretch': r4(miss[m].mean()), 'mean_share_of_the_stretch_written_D': r4(a['cov'][m].mean())}
          for lo, hi in ((0, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 1e9)) for m in [(dur >= lo) & (dur < hi)]}
orc = json.load(open(V / 'orc1.json')); ks = list(orc)
def agg(k):
    v = np.array([orc[c][k] for c in ks]); n = np.array([orc[c][k + '_n'] for c in ks]); dfl = np.array([c.startswith('J03') for c in ks])
    return {'mean': r4(v.mean()), 'dfl': r4(v[dfl].mean()), 'metrica': r4(v[~dfl].mean()), 'min': r4(v.min()), 'max': r4(v.max()), 'better': int((v > 1e-9).sum()), 'worse': int((v < -1e-9).sum()),
            'stretches_written_per_copy': round(float(n[:, 0].mean()), 1), 'restarts_moved_per_copy': round(float(n[:, 1].mean()), 1)}
rule = {}
for fn in ('rule1_clean_default.json', 'rule1_noisy_false30_second.json'):
    for k, v in json.load(open(V / fn)).items():
        reg, nm = k.split('|')
        rule.setdefault(reg, {})[nm] = {'mean': r4(v['mean']), 'dfl': r4(v['dfl']), 'metrica': r4(v['met']), 'min': r4(v['min']), 'max': r4(v['max']), 'better': v['better'], 'worse': v['worse'],
                                        'macro_f1_mean': r4(v['macro']), 'forced_per_copy': round(v['acted'], 1), 'share_of_forced_frames_within_1s_of_a_true_dead_frame': None if v['precision'] is None else round(v['precision'], 2)}
tm = json.load(open(V / 'team1.json')); g = np.array(tm['gain'])
import pandas
out = {
 'version': 'possession-k015-tag-rescue (exploration, reporting only)',
 'written_at': datetime.now(timezone(timedelta(hours=3))).isoformat(timespec='seconds'),
 'what': 'Question of the team lead (15 Nov 11:47): a Smart Tagging set-piece tag says a restart happened in its window, so a dead-ball stretch ends there; if the decision has no D around the window, '
         'force one at the most likely place and then settle its extent. This had not been tried (v3.0 / v3.1 gave the tags to the second stage as learned evidence). Measured here on the 42 development copies '
         'of K014 with SIMULATED set-piece tags, because no external match has Smart Tagging. No plan was registered, nothing was validated, nothing was selected; the release stays possession-v2.15.',
 'data': {'copies': ncop, 'matches': {m: {'minutes_graded': round(R[m]['minutes'], 1), 'restarts': len(R[m]['restarts'])} for m in R},
          'decision': 'the v2.15 decision stored for K014 (pooled probabilities, v2 decoder); the models behind the probabilities had not seen these matches',
          'restart': 'a labelled D stretch followed by H or A inside a half (one single D frame at the start of a half of J03WN1 is left out of the counts under how_often); type guessed from the clean ball position (possession.tags._restart_type), as in the simulator of possession-v3-plan.json. '
                     'Metrica proxy labels end many stoppages at an event, so goal kicks of the Metrica games fall under "free kick"',
          'published_counts_used': 'DATA.md of the organisers: Throw-in 26, Corner Kick 12, Goal Kick 10, Free Kick 5, Kick Off (After Goal) 4 per 158,857 graded frames (the 2 start kick-offs are used by the kick-off rule already). '
                                   'Public documentation; the provided tag file was not read'},
 'how_often': {'true_stretches_ending_in_a_restart': int(len(a)), 'per_copy': round(len(a) / ncop, 1), 'no_D_of_ours_on_the_stretch': r4(miss.mean()), 'per_copy_missed': round(float(miss.sum() / ncop), 1),
               'by_match': {m: r4(miss[a['match'] == m].mean()) for m in sorted(set(a['match']))}, 'by_type': by_type, 'by_length_of_the_stretch': by_len,
               'missed_stretches': {'median_length_s': round(float(np.median(dur[miss])), 1), 'found_median_length_s': round(float(np.median(dur[~miss])), 1), 'ball_seen_share': r4(a['seen'][miss].mean()),
                                    'ball_seen_share_on_found': r4(a['seen'][~miss].mean()), 'same_team_before_and_after': r4((a['p'][miss] == a['n'][miss]).mean()),
                                    'largest_pooled_P_dead_on_the_stretch_quantiles_10_25_50_75_90': [r4(x) for x in np.quantile(a['pmax'][miss], [.1, .25, .5, .75, .9])]}},
 'ceilings_with_the_labels_as_oracle': {
     'what': 'spellF1 change if tags were used perfectly: "miss" writes the true stretch as D where we have no D on it; "time" moves the end of our D to the true restart; "both". '
             '"all" = every restart tagged; "published" = tagged with the per-type probabilities that give the published counts (one draw per copy, seeds 900000 + copy index)',
     'mean_restarts_per_copy': round(float(np.mean([orc[c]['n_all'] for c in ks])), 1), 'mean_tagged_at_published_counts': round(float(np.mean([orc[c]['n_pub'] for c in ks])), 1),
     'all_miss': agg('all_miss'), 'all_time': agg('all_time'), 'all_both': agg('all_both'), 'published_miss': agg('pub_miss'), 'published_time': agg('pub_time'), 'published_both': agg('pub_both')},
 'rule_tried': {
     'definition': 'for every set-piece window without a D of the decision in [start - 5 s, end): the frame of that region through which the decoder passes D at the least cost (forward-backward scores of the unchanged v2 decoder); '
                   'if that cost is at most c (log units; one D run costs 120 in transitions), the decoder is re-run with that frame forced to D, which also settles the extent of the run. '
                   'Variants: other c, search region from 3 s / 8 s before or up to 2 s after the window, runs widened to 1 s, short possession pieces between the forced run and the next team change written D (bridge)',
     'simulated_tags': 'windows [restart - U(0.5, 4) s, restart + U(1, 5) s] as in possession-v3-plan.json, kept with the published per-type rates times a scale, start and end shifted by lag + N(0, sigma); false windows of 3-7 s on live frames. '
                       'Regimes: ' + json.dumps(T.REG) + ' (scale, lag s, sigma s, false windows as a share of the tags; pairs are uniform ranges); seeds 910000 + 1000 * regime index + copy index',
     'spell_f1_change_by_regime_and_variant': rule},
 'taker_team': {'what': 'tagged restarts with a team (not throw-ins) where a possession of ours starts after a D within 3 s of the restart: how often it is the wrong team, and the gain if the label were corrected',
                'n': tm['tagged_restarts_with_team_and_found_possession'], 'wrong_team': tm['wrong_team'], 'oracle_gain_mean': r4(g.mean()), 'min': r4(g.min()), 'max': r4(g.max())},
 'conclusions': [
     'The decision has at least one D frame on 93% of the dead-ball stretches that end in a restart. The stretches without any (about 6 per copy; 2% in the DFL matches, 10-20% in the Metrica games) are short (median 4.7 s against 21 s) and the ball is seen on 9% of their frames (31% on the stretches that are found).',
     'The published tag counts cover about half of the restarts of a match and only 5 free kicks, the type we miss most often; about 2.4 missed stretches per copy carry a tag.',
     'Ceiling with perfect tags and the true extents: +0.003 spellF1 (+0.004 with the restart moment as well). The rule that was tried gives +0.001 with clean tags, +0.0016 with tags accurate to a second, +0.0005 to +0.001 with noisy or false tags, '
     'and only with the cost limit: without it false tags cost up to -0.0045.',
     'The taker team of the tags has nothing to correct (wrong team after a found restart in 1.4% of the cases).',
     'Not adopted and not registered: the possible gain is a tenth of the gain gate used for every candidate so far (+0.008) and far below what one match can show (the organisers: differences under about 0.04 are noise); '
     'the error profile of the real tags is unknown and cannot be measured.'],
 'limits': ['Development copies that earlier work has used; variants were compared on them; nothing here is a validation.',
            'The tags are simulated from the labels. How the real tagger chooses which restarts to tag is unknown; if it needs the tracked ball it may tag exactly the stretches the models find anyway.',
            'Agreement with other providers labels on corrupted external copies; not a competition score.'],
 'scripts_sha256': {n: sha(V / n) for n in ('rest1.py', 'rest2.py', 'orc1.py', 'taglib.py', 'rule1.py', 'team1.py', 'k015_assemble.py')},
 'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pandas.__version__,
                 'labels': 'stored with the development copies (file-order Metrica proxy labels of K005); the restarts recomputed today with the current metrica_labels.py were checked against them'},
 'provided_fixture_used': False}
(REPO / 'possession-k015-tag-rescue.json').write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
print(json.dumps({k: out[k] for k in ('how_often', 'ceilings_with_the_labels_as_oracle', 'taker_team', 'environment')}, indent=1)[:6000])
