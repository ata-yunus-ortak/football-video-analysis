"""Collect what possession-v211-plan.json lists as 'reported alongside' (nothing here is a gate or a choice):
the reserved Metrica game 3 rows, the analysis of what v2.10 moved, the development counts on training matches and
the full-size rehearsals. Writes possession-v211-followup.json. Usage: assemble_followup.py

Scores of bundle A are computed against truth_stable.npz (the proxy labels in file order, log entry K005;
rescore_k003.py), not against the truth file written when the bundle was built. G1 and G2 were built in the
experiment environment and carry the file-order labels."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
import numpy as np

REPO, WORK = Path('/home/claude/sc'), Path('/home/claude/work')
P = Path('/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova')
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(P))
from score_prova import report
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
TRUTH = {'A': P / 'A' / 'truth_stable.npz', 'G1': P / 'G1' / 'truth.npz', 'G2': P / 'G2' / 'truth.npz'}
_lab = np.load(TRUTH['A'])['lab']
assert all(np.array_equal(_lab, np.load(TRUTH[g])['lab']) for g in ('G1', 'G2'))          # one set of labels for all three bundles


def jsonl(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            pass
    return rows


def run(bundle, module):
    """Score, model path, what was moved, time and memory of one entry-point run on a rehearsal bundle."""
    s = report(TRUTH[bundle], P / bundle / f'out-{module}' / 'submission.csv')['graded windows (as the organisers grade)']
    r = json.loads((P / bundle / f'out-{module}' / 'run.json').read_text())
    last = (P / 'logs' / f'{bundle}_{module}.log').read_text().strip().splitlines()[-1]
    m = re.match(r'\[exit (\d+); (\d+) s; peak child RSS ([\d.]+) GB\]', last)
    k = r.get('goalkeeper_correction') or {}
    out = {'spell_f1': s['spell_f1_mean'], 'macro_f1': s['macro_f1'], 'f1_H': s['f1_H'], 'f1_A': s['f1_A'], 'f1_D': s['f1_D'],
           'model_path': r['path'], 'broadcast_fill_used': r['broadcast_fill_used'],
           'exit': int(m.group(1)), 'seconds': int(m.group(2)), 'peak_memory_gb': float(m.group(3))}
    if k:
        out['goalkeeper_correction'] = {'moved_pieces': k['moved_pieces'], 'moved_frames': k['moved_frames'], 'new_columns': k['new_columns'],
                                        'evidence_frames_per_half_and_goal': [h[f'{s_}_evidence_frames'] for h in k['halves'] for s_ in ('left', 'right')]}
    return out


def chain(log, bundle, csv):
    text = (P / 'logs' / log).read_text()
    steps = re.findall(r'^\[\s*\d+\] ([A-Z ]+?) \.+ (.+)$', text, re.M)
    last = text.strip().splitlines()[-1]
    m = re.match(r'\[exit (\d+); (\d+) s; peak child RSS ([\d.]+) GB\]', last)
    s = report(TRUTH[bundle], csv)
    g = s['graded windows (as the organisers grade)']
    return {'steps': {a.strip(): b.strip() for a, b in steps}, 'result_line': re.search(r'^SONUC: (.+)$', text, re.M).group(1),
            'exit': int(m.group(1)), 'seconds': int(m.group(2)), 'peak_memory_gb': float(m.group(3)),
            'spell_f1': g['spell_f1_mean'], 'macro_f1': g['macro_f1'], 'lead_in_labels': s['lead-in labels']}


def main():
    out = {'version': 'possession-v2.11-followup',
           'written_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
           'note': 'Reported alongside the v2.11 decision (possession-v211-plan.json): not gates, nothing was selected or changed because of these numbers.',
           'results_sha256': sha(REPO / 'possession-v211-results.json')}
    out['reserved_metrica_game_3'] = {'note': 'one new corrupted copy (seed 31103), the seven conditions, run once after the decision',
                                      'rows': json.loads((WORK / 'exp_v211_reserved.json').read_text())['rows']}
    out['what_v2_10_moved_with_correct_ids'] = {
        'script': 'experiments/possession_v2/gk_none.py, gk_none_detail.py (validation copies of possession-v210-plan.json, condition none; after its decision)',
        'copies': json.loads((WORK / 'gk_none.json').read_text())['copies'],
        'note': 'gk_none.py calls a piece a goalkeeper when it is within 2.5 m of a goalkeeper; the piece of copy J03WR9|10111 listed as '
                '"goalkeeper with the right id" is the same outfield player as in J03WR9|10110 (gk_none_detail.py).',
        'outfield_pieces_moved_to_the_wrong_team': [
            {'copy': 'J03WR9|10110', 'frames': [142924, 146810], 'tracked_frames': 3496, 'distance_to_goal_m_10_50_90': [12.8, 13.4, 20.9],
             'far_frames': 418, 'nearest_in_far_frames': 336, 'goalkeeper_of_that_goal_tracked_share': 0.883},
            {'copy': 'J03WR9|10111', 'frames': [145117, 146810], 'tracked_frames': 1571, 'distance_to_goal_m_10_50_90': [12.9, 13.1, 13.3],
             'far_frames': 451, 'nearest_in_far_frames': 346, 'goalkeeper_of_that_goal_tracked_share': 0.797},
            {'copy': 'MET1|10120', 'frames': [49689, 50055], 'tracked_frames': 366, 'distance_to_goal_m_10_50_90': [25.4, 26.6, 26.9],
             'far_frames': 120, 'nearest_in_far_frames': 120, 'goalkeeper_of_that_goal_tracked_share': 0.773}]}
    out['development_on_training_matches'] = {
        'script': 'experiments/possession_v2/gk_far_dev.py (no model; one corrupted copy per training match, 46-slot layout; camera window = camera_view.py)',
        'keeper2 (v2.11)': jsonl(WORK / 'gk2/far_dev_keeper2_a.log') + jsonl(WORK / 'gk2/far_dev_keeper2_b.log'),
        'keeper (v2.10)': jsonl(WORK / 'gk2/far_dev_keeper_WOH.log') + jsonl(WORK / 'gk2/far_dev_keeper_WOY.log')}
    k003 = json.loads((P / 'rescore_k003.json').read_text())['bundle A']['delivered file of the K003 chain (possession-v2.9)']
    out['full_size_rehearsal'] = {
        'note': 'synthetic provided-like bundles (K003, experiments/possession_v2/prova_build.py); G1 and G2 are bundle A with the tracks of the '
                'four goalkeepers (Metrica game 3 and game 2 parts) under the other team\'s id, in the tactical tracking only (G1) or in both '
                'trackings (G2) (prova_gk.py). Wiring, size, time and memory; not accuracy on the provided match.',
        'labels': 'Metrica proxy labels in file order (K005); bundle A was re-scored, its first scores are in possession-rehearsal-results.json',
        'bundle_A_v2_9_chain_of_K003': {'spell_f1': k003['against_file_order_labels']['spell_f1_mean'], 'macro_f1': k003['against_file_order_labels']['macro_f1'],
                                        'as_first_recorded_against_the_degraded_labels': {'spell_f1': k003['as_recorded_in_K003']['spell_f1_mean'],
                                                                                         'macro_f1': k003['as_recorded_in_K003']['macro_f1']}},
        'bundle_A_v2_11': run('A', 'run211'),
        'bundle_A_chain_v2_11': chain('chain_A_v211.log', 'A', P / 'A' / 'private_v211' / 'teslim' / 'Prova.csv'),
        'bundle_G1_v2_11': run('G1', 'run211'),
        'bundle_G1_v2_9': run('G1', 'run29'),
        'bundle_G2_v2_11': run('G2', 'run211'),
        'bundle_G1_chain_v2_11': chain('chain_G1_v211.log', 'G1', P / 'G1' / 'private_chain' / 'teslim' / 'Prova.csv'),
        'bundle_A_chain_reserve_v2_11g': chain('chain_A_v211g.log', 'A', P / 'A' / 'private_v211g' / 'teslim' / 'Prova.csv'),
        'builds': {g: json.loads((P / g / 'build.json').read_text())['tactical'] | {'goalkeepers': json.loads((P / g / 'build.json').read_text())['goalkeepers']}
                   for g in ('G1', 'G2')},
    }
    out['provided_fixture_used'] = False
    (REPO / 'possession-v211-followup.json').write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    f = out['full_size_rehearsal']
    for k in ('bundle_A_v2_11', 'bundle_A_chain_v2_11', 'bundle_G1_v2_11', 'bundle_G1_v2_9', 'bundle_G2_v2_11', 'bundle_G1_chain_v2_11', 'bundle_A_chain_reserve_v2_11g'):
        v = f[k]
        print(k, v['spell_f1'], v['macro_f1'], v['seconds'], 's', v['peak_memory_gb'], 'GB', v.get('goalkeeper_correction', {}).get('moved_pieces', ''), v.get('result_line', ''))
    for r in out['reserved_metrica_game_3']['rows']:
        print(r['copy'], r['condition'], r['v2_9'][0], r['v2_11'][0], r.get('v2_10', [''])[0])


if __name__ == '__main__':
    main()
