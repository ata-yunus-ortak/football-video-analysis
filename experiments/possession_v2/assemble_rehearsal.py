"""Collect the full-size rehearsal and the slot / duplicate diagnostic into possession-rehearsal-results.json.
Usage: assemble_rehearsal.py OUT_JSON   (reads the scratch folders of the cloud session; aggregates only)"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

P = Path('/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova')
SC = Path('/home/claude/sc')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def status_lines(log):
    text = Path(log).read_text()
    lines = [re.sub(r'\s*\.{2,}\s*', ': ', l[5:]) for l in text.splitlines() if re.match(r'^\[\s*\d+\]', l)]
    lines = [re.sub(r'\(Linux[^)]*\)', '(Linux, Python 3.10.20, numpy 1.26.4, scipy 1.11.4, pandas 2.1.4)', l) for l in lines]
    end = [l for l in text.splitlines() if l.startswith('SONUC')]
    m = re.search(r'\[exit (\d+); (\d+) s; peak child RSS ([\d.]+) GB\]', text)
    return {'status_lines': lines, 'result_line': end[0] if end else None,
            'exit_code': int(m.group(1)), 'seconds': int(m.group(2)), 'peak_memory_gb': float(m.group(3))}


def scores(path):
    d = json.loads(Path(path).read_text())
    g = d['graded windows (as the organisers grade)']
    out = {'spell_f1': g['spell_f1_mean'], 'macro_f1': g['macro_f1'], 'f1_H': g['f1_H'], 'f1_A': g['f1_A'], 'f1_D': g['f1_D'],
           'label_possessions': g['gt_spells'], 'predicted_possessions': g['pred_spells'],
           'play_only_spell_f1': d['play only (kick-off to end of each half)']['spell_f1_mean'],
           'labels_written_before_the_second_half_kick_off': d['lead-in labels']}
    return out


def run_facts(private):
    runs = sorted(Path(private).glob('possession-run-*'))
    r = json.loads((runs[0] / 'run.json').read_text())
    f = r['fusion']
    return {'system': r['system'], 'model_path': r['path'], 'measured_noise_m': {k: round(v, 3) for k, v in r['gate']['measured_noise'].items() if k.endswith('_m')},
            'play_blocks': r['period_source'], 'broadcast_fill_used': r['broadcast_fill_used'], 'alignment_mode': f.get('alignment_mode'),
            'alignment_lags_frames': [[h['lag_min'], h['lag_max']] for h in f['alignment']['halves']],
            'registration': f.get('registration'),
            'accuracy_gate': {k: f.get(k) for k in ('median_distance_m', 'threshold_median_m', 'used', 'filled', 'ball_visible_graded_before', 'ball_visible_graded_after')},
            'runs': len(runs),
            'all_runs_same_bytes': len({json.loads((x / 'run.json').read_text())['submission_sha256'] for x in runs}) == 1}


def bundle(name, with_reserve):
    b = json.loads((P / name / 'build.json').read_text())
    out = {'seed': b['seed'], 'tactical_corruption': b['degrade_params'],
           'broadcast_quality': {k: b['broadcast_quality'][k] for k in ('bias_sd', 'b_sd', 'p_sd', 'ball_frac', 'hx', 'hy')},
           'content': b['sources'],
           'tactical_file': {'records': 199319, 'slots': 46, 'tracklets': b['tactical']['tracklets'], 'duplicated_tracks': b['tactical']['duplicated_tracks'],
                             'mean_tracked_on_graded': b['tactical']['mean_tracked_on_graded'],
                             'share_of_graded_frames_above_22': b['tactical']['share_of_graded_frames_above_22'],
                             'ball_frames_graded': b['tactical']['ball']['graded'], 'ball_frames_total': b['tactical']['ball']['total']},
           'broadcast_file': {k: b['broadcast'][k] for k in ('frames', 'valid_share', 'ball_share', 'invalid_stretches', 'published_invalid_stretches',
                                                             'longest_invalid_s', 'replays', 'studio_gap_frames')} | {'slots': 51},
           'external_labels_on_graded_frames': b['labels_on_graded'],
           'chain': status_lines(P / 'logs' / f'chain_{name}.log'),
           'delivered_run': run_facts(P / name / 'private'),
           'scores_external_labels': {
               'delivered file (release, both cameras)': scores(P / name / ('v29_score.json' if (P / name / 'v29_score.json').exists() else 'chain_score.json')),
               'tactical camera only, entry point possession.run25c on the same files': scores(P / name / 'r3_score.json'),
               'same corrupted content before duplicated tracks and slot packing, in memory, tactical only': scores(P / name / 'r1_score.json')}}
    if with_reserve:
        out['reserve_configuration'] = {'chain': status_lines(P / 'logs' / f'chain_{name}g.log'), 'delivered_run': run_facts(P / name / 'private_g'),
                                        'scores_external_labels': scores(P / name / 'v29g_score.json')}
    return out


if __name__ == '__main__':
    stress = json.loads(Path('/home/claude/work/stress_slots.json').read_text())['rows']
    names = sorted({r['match'] for r in stress})
    variants = ('base', 'sticky', 'lru', 'swap', 'dup1', 'dup5')
    table = {v: {m: next(r['spell_f1'] for r in stress if r['match'] == m and r['variant'] == v) for m in names} for v in variants}
    mean = {v: round(sum(table[v].values()) / len(names), 4) for v in variants}
    scripts = {n: sha(p) for n, p in (('prova_build.py', P / 'prova_build.py'), ('score_prova.py', P / 'score_prova.py'), ('r1.py', P / 'r1.py'),
                                      ('rss_run.py', P / 'rss_run.py'), ('after_A.sh', P / 'after_A.sh'), ('after_B.sh', P / 'after_B.sh'),
                                      ('controls.py', P / 'controls.py'), ('stress_slots.py', '/home/claude/work/stress_slots.py'), ('assemble_rehearsal.py', P / 'assemble_rehearsal.py'))}
    out = {
        'record': 'K003 full-size rehearsal of the delivery chain and slot / duplicate diagnostic',
        'written_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
        'purpose': ('Pipeline correctness at the real size and robustness to two documented properties of the provided tracking. '
                    'Reporting only: nothing was selected, tuned or gated with these numbers.'),
        'provided_fixture_used': False,
        'not_a_competition_score': True,
        'data': ('Metrica sample games 1-3 (external, public). The rehearsal bundles carry the file names, record counts and slot counts of the '
                 'provided match and are trimmed to the aggregate facts published in DATA.md; their content is game 3 with pieces of game 2 '
                 'appended, everything outside play is synthetic.'),
        'release_manifest_sha256': {n: sha(SC / n) for n in ('possession-v29-release.json', 'possession-v25c-release.json', 'possession-v25-release.json',
                                                             'possession-v29g-release.json')},
        'organisers_repository_commit': 'f8f2629',
        'scripts_sha256': scripts,
        'rehearsal': {'A (corruption inside the training range, accurate broadcast)': bundle('A', True),
                      'B (player noise above the gate threshold, broadcast with a larger calibration error)': bundle('B', False)},
        'organisers_scorer_cross_check': json.loads((P / 'A' / 'orgscore.json').read_text()),
        'negative_controls_bundle_A': json.loads((P / 'A' / 'controls.json').read_text()),
        'slot_and_duplicate_diagnostic': {
            'design': [l.rstrip() for l in Path('/home/claude/work/stress_slots.py').read_text().split('"""')[1].strip().splitlines()[:-1]],
            'copies': [{'match': m, 'seed': next(r['seed'] for r in stress if r['match'] == m), 'model_path': next(r['path'] for r in stress if r['match'] == m)} for m in names],
            'spell_f1': table, 'mean_spell_f1': mean,
            'difference_to_base': {v: round(mean[v] - mean['base'], 4) for v in variants if v != 'base'},
            'model_path_changed_by_a_variant': len({(r['match'], r['path']) for r in stress}) != len(names),
            'duplicated_share_of_tracked_positions': {v: round(sum(r['duplicated_share_of_tracked_positions'] for r in stress if r['variant'] == v) / len(names), 4)
                                                      for v in ('dup1', 'dup5')},
            'rows': stress},
        'notes': ['Chain A and the reserve chain ran with the first version of possession/inputs_check.py (16 checks). The check was then extended '
                  'to 26 (syntax facts read without the release reader, reader error class); bundle A passes all 26 (24 s, 1.55 GB) and chain B '
                  'ran with that version.',
                  'Timings are from a 2-CPU cloud container; they include the synthetic tests in chain A only; no OCR and no fresh clone.'],
        'limits': ['Simulated streams and synthetic periods outside play; previously accessed fixtures; one copy per match.',
                   'The rehearsal bundles follow the published aggregates, not the unknown details of the provided files '
                   '(for example 188 unusable broadcast stretches in bundle A where DATA.md reports 122).',
                   'What the models do before a kick-off was exercised on an invented segment only.'],
    }
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    print('written', sys.argv[1])
