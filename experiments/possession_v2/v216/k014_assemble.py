"""Assemble possession-k014-error-patterns.json from the development analyses of 15 Nov (errlib.py, mine1-5.py, sem1.py,
shift1.py, oracle1.py, dec1.py, bump1.py, cand_c.py, cand_r.py, stack1.py). Reporting only: nothing here is a validation and
nothing was selected. Usage: k014_assemble.py REPO_DIR"""
import json, sys, numpy as np, platform
from datetime import datetime, timezone, timedelta
from pathlib import Path
REPO = Path(sys.argv[1])
gt, pr = np.load('mine1_gt.npy'), np.load('mine1_pr.npy')
N = len(gt) + len(pr); F = 2 * gt['credit'].sum() / N; LOSS = 1 - F
sh = lambda m, arr: round(float((1 - arr['credit'][m]).sum() / N / LOSS), 4)
def cause(own, oth, dead):
    return np.select([own >= 0.5, oth >= 0.5, dead >= 0.5], [0, 1, 2], 3)
cg = cause(gt['p_own'], gt['p_oth'], gt['p_dead']); cp = cause(pr['g_own'], pr['g_oth'], pr['g_dead'])
miss = ~gt['m03']; part = gt['m03'] & (gt['credit'] < 0.99); pm = ~pr['m03']
bins = [0, 25, 50, 100, 200, 10 ** 9]; names = ['under 1 s', '1-2 s', '2-4 s', '4-8 s', 'over 8 s']
by_len = {}
for k, nm in enumerate(names):
    m = (gt['dur'] >= bins[k]) & (gt['dur'] < bins[k + 1]); q = (pr['dur'] >= bins[k]) & (pr['dur'] < bins[k + 1])
    by_len[nm] = {'share_of_true_possessions': round(float(m.mean()), 4), 'mean_credit': round(float(gt['credit'][m].mean()), 4), 'share_of_loss': sh(m, gt),
                  'share_of_predicted_possessions': round(float(q.mean()), 4), 'mean_credit_of_predicted': round(float(pr['credit'][q].mean()), 4), 'share_of_loss_predicted_side': sh(q, pr)}
per_match = {}
for mt in sorted(set(gt['match'])):
    g, p = gt[gt['match'] == mt], pr[pr['match'] == mt]
    n = len(g) + len(p); f = 2 * g['credit'].sum() / n
    s2 = lambda m, arr: round(float((1 - arr['credit'][m]).sum() / n / (1 - f)), 3)
    per_match[mt] = {'copies': len(set(g['key'])), 'spell_f1': round(float(f), 4), 'true_per_copy': round(len(g) / len(set(g['key']))), 'predicted_per_copy': round(len(p) / len(set(g['key']))),
                     'loss_share_true_under_2s': s2(g['dur'] < 50, g), 'loss_share_missed_true': s2(~g['m03'], g),
                     'loss_share_partial_pairs_both_sides': round(2 * s2(g['m03'] & (g['credit'] < 0.99), g), 3), 'loss_share_spurious_predicted': s2(~p['m03'], p)}
r5 = np.load('mine5.npy')
def turn(sel):
    e = r5['err'][sel]
    return {'n': int(sel.sum()), 'found_within_3s': round(float((e != 999).mean()), 3), 'within_0.25s': round(float((np.abs(e) <= 6).mean()), 3), 'within_0.5s': round(float((np.abs(e) <= 12).mean()), 3), 'within_1s': round(float((np.abs(e) <= 25).mean()), 3)}
stable = (r5['d0'] >= 50) & (r5['d1'] >= 50)
turnovers = {src: {'both possessions >= 2 s, ball seen': turn(s & stable & (r5['seen'] >= 0.8)), 'both possessions >= 2 s, ball unseen': turn(s & stable & (r5['seen'] < 0.2)),
                   'new possession < 2 s, ball seen': turn(s & (r5['d1'] < 50) & (r5['seen'] >= 0.8)), 'new possession < 2 s, ball unseen': turn(s & (r5['d1'] < 50) & (r5['seen'] < 0.2))}
             for src, s in (('DFL', r5['dfl']), ('Metrica', ~r5['dfl']))}
b = np.load('bump1.npy')
bumps = {f'{lo:.2f}-{hi:.2f}': {'n': int(m.sum()), 'true_possession_under_it': round(float(np.mean(b['other'][m] >= 0.5)), 3), 'iou_0.3_with_a_true_possession': round(float(np.mean(b['iou'][m] >= 0.3)), 3)}
         for lo, hi in ((0.2, 0.3), (0.3, 0.4), (0.4, 0.5), (0.5, 1.01)) for m in [(b['peak'] >= lo) & (b['peak'] < hi)]}
orc = json.load(open('oracle1.json')); keys = list(orc)
oracle = {c: round(float(np.mean([orc[k][c] for k in keys])), 4) for c in orc[keys[0]]}
sem = json.load(open('sem1.json'))
semt = {f'labels_tau_{int(t) / 25:.1f}s': {f'prediction_m_{int(m) / 25:.1f}s': round(float(np.mean([sem[k]['f1'][f'{t}|{m}'] for k in sem])), 4) for m in (0, 13, 25, 38, 50, 75)} for t in (0, 13, 25, 38, 50, 75)}
dec = json.load(open('dec1.json'))
decs = {n: round(float(np.mean([dec[k][n] - dec[k]['sw3'] for k in dec])), 4) for n in ('sw2', 'sw4', 'sw5', 'b-0.6', 'b0')}
def cand(file, pick=None):
    r = json.load(open(file)); out = {}
    for c in list(r.values())[0]:
        if c == 'base':
            continue
        v = {x: (r[x][c][0] if isinstance(r[x][c], list) else r[x][c]) for x in r}
        out[c] = {'all': round(float(np.mean(list(v.values()))), 4), 'DFL': round(float(np.mean([v[x] for x in v if x.startswith('J03')])), 4),
                  'Metrica': round(float(np.mean([v[x] for x in v if x.startswith('MET')])), 4), 'worst_copy': round(float(min(v.values())), 4), 'copies_better': int(sum(x > 0 for x in v.values()))}
    return out
st = json.load(open('stack1_all.json')); dv = {k: st[k][0] - st[k][1] for k in st}
stack = {'all': round(float(np.mean(list(dv.values()))), 4), 'DFL': round(float(np.mean([dv[k] for k in dv if k.startswith('J03')])), 4), 'Metrica': round(float(np.mean([dv[k] for k in dv if k.startswith('MET')])), 4),
         'worst_copy': round(float(min(dv.values())), 4), 'copies_better': int(sum(x > 0 for x in dv.values())), 'copies': len(dv),
         'per_match': {m: round(float(np.mean([dv[k] for k in dv if k.startswith(m)])), 4) for m in sorted(set(k.split('_')[0] for k in dv))}}
cc, cr = cand('cand_c.json'), cand('cand_r.json')
import sklearn, pandas
out = {
 'version': 'possession-k014-error-patterns',
 'written_at': datetime.now(timezone(timedelta(hours=3))).isoformat(timespec='seconds'),
 'what': 'Development analysis of 15 Nov 2026, asked for by the team lead: where the decision of possession-v2.15 loses spellF1 on external copies, what the '
         'losses have in common, and whether algorithms built on those patterns do better on matches the models were not trained on. Reporting only: no plan was '
         'registered, nothing is a validation, nothing was selected, the release is unchanged.',
 'data': '42 development copies already scored in earlier validations (J03WN1 10, J03WR9 10, Metrica 1 10, Metrica 2 10, Metrica 3 2; 33 with our corruption simulator, 9 with the '
         'team\'s second one). The tree models and the network that produced the stored probabilities were trained on other matches (4 DFL matches for the DFL copies, '
         '6 for the Metrica copies). DFL labels are the provider\'s per-frame flags, Metrica labels our proxies from events. The provided match was not opened.',
 'method': 'credit of a possession = share of the five IoU thresholds at which the organisers\' greedy matching matches it; spellF1 = 2 * sum(credit) / (true + predicted), so the '
           'loss 1 - spellF1 splits exactly into (1 - credit) of every true and every predicted possession (errlib.py reproduces the official score on all 42 copies).',
 'overall': {'copies': 42, 'true_possessions': int(len(gt)), 'predicted_possessions': int(len(pr)), 'spell_f1_pooled_over_possessions': round(float(F), 4),
             'loss_true_side': round(float((1 - gt['credit']).sum() / N), 4), 'loss_predicted_side': round(float((1 - pr['credit']).sum() / N), 4)},
 'loss_by_length': by_len,
 'loss_by_kind': {
   'true possessions not matched at IoU 0.3': {'share_of_true': round(float(miss.mean()), 4), 'share_of_loss': sh(miss, gt),
       'prediction says the other team': sh(miss & (cg == 1), gt), 'prediction says the same team, merged or misaligned': sh(miss & (cg == 0), gt), 'prediction says dead ball': sh(miss & (cg == 2), gt),
       'under 2 s and the prediction says the other team': sh(miss & (cg == 1) & (gt['dur'] < 50), gt),
       'mean pooled probability of the right team in those': round(float(gt['prob'][miss & (cg == 1) & (gt['dur'] < 50)].mean()), 3)},
   'matched pairs with partial credit (both sides)': {'share_of_true': round(float(part.mean()), 4), 'share_of_loss': round(2 * sh(part, gt), 4)},
   'predicted possessions not matched at IoU 0.3': {'share_of_predicted': round(float(pm.mean()), 4), 'share_of_loss': sh(pm, pr), 'truth is the other team': sh(pm & (cp == 1), pr),
       'truth is the same team (extra piece)': sh(pm & (cp == 0), pr), 'truth is dead ball': sh(pm & (cp == 2), pr)}},
 'per_match': per_match,
 'turnovers_found_and_timed': turnovers,
 'upper_bounds_with_the_labels_as_oracle': dict(oracle, note='base = v2.15; snap = predicted changes with a true counterpart within the window moved to the true moment; nodead = dead-ball frames perfect. Never a method.'),
 'tested_on_the_development_copies': {
   'weak signals inside predicted possessions (bumps of the other team\'s probability), by peak': dict(bumps, note='to pay off under spellF1 at this level, an inserted possession must be real in roughly 4 of 10 cases; none of the groups reaches that'),
   'decoder constants (difference to the release constants)': decs,
   'contact evidence added to the decoder (12 settings)': {'best': max(cc.items(), key=lambda kv: kv[1]['all']), 'worst': min(cc.items(), key=lambda kv: kv[1]['all'])},
   'reception rule that re-times turnovers (24 settings)': {'best': max(cr.items(), key=lambda kv: kv[1]['all']), 'worst': min(cr.items(), key=lambda kv: kv[1]['all'])},
   'learned combination of both model families, leave one match out (exploration only)': dict(stack, note='gradient-boosted classifier on both families\' probabilities and their temporal context, trained on the copies of four matches, tested on the fifth; '
        'difference to v2.15. Average gain about the size of the registered minimum, single copies clearly worse: it would not pass the gate on single copies. Not registered: the v2.15 plan says no further attempt with the second model follows.'),
   'minimum possession length in labels and prediction (reading of the organisers\' rule that a touch without control is no change of possession)': dict(semt,
        note='rows: external labels in which a possession shorter than tau after the other team\'s possession does not count; columns: the same rule applied to the prediction. The best m follows tau. '
             'Which tau describes the competition labels cannot be measured on external data, so nothing was changed.')},
 'label_sets_shifted_against_themselves': 'shift1.py: external labels scored against themselves shifted late by 3 / 8 / 25 frames: J03WN1 0.948 / 0.835 / 0.505, J03WR9 0.952 / 0.875 / 0.601, '
        'Metrica 1-3 0.93-0.96 / 0.85-0.87 / 0.62; the organisers publish 0.9818 / 0.8933 / 0.6539 for their ground truth (EVALUATION.md). Read only as context: their labels seem to contain fewer '
        'very short possessions than ours. Not used for any choice.',
 'conclusions': [
   'Possessions under 2 s are 29% of the true possessions and carry 38% of the lost score; 70% of them are not found. In 6 of 10 the prediction keeps the other team, and neither model family shows them (mean probability of the right team 0.25).',
   'A third of the loss is timing and extent of possessions that are found: with the ball seen, a turnover between two possessions of at least 2 s is timed within 0.5 s in 62% (DFL) and 73% (Metrica) of cases, with the ball unseen in 26-29%. '
   'The decision tends to switch while the ball is still travelling to the new team.',
   'The patterns are the same in all five matches and both label sources. Long true possessions predicted dead occur almost only in the Metrica proxies and are an artefact of those labels.',
   'Rules built on the patterns (contact evidence, re-timing to the reception, decoder constants) changed the score by at most 0.003 either way; a minimum possession length is neutral at 0.5 s and costs 0.008 at 1 s on the external labels. A learned combination of the two families gained about 0.01 on average with single copies 0.01-0.02 worse.',
   'None of this reaches the registered minimum for a release change (+0.008 with no copy below -0.010), and the organisers state that differences below about 0.04 are noise on one match. The release stays possession-v2.15.'],
 'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pandas.__version__, 'scikit-learn': sklearn.__version__},
 'provided_fixture_used': False}
(REPO / 'possession-k014-error-patterns.json').write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
print(json.dumps({k: out[k] for k in ('overall', 'loss_by_kind', 'per_match')}, indent=1)[:3800])
print(json.dumps(out['tested_on_the_development_copies']['contact evidence added to the decoder (12 settings)'])[:400])
print(json.dumps(out['tested_on_the_development_copies']['reception rule that re-times turnovers (24 settings)'])[:500])
print(decs, stack)
