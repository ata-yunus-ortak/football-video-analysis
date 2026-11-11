"""Apply the six registered gates of possession-v211-plan.json to the rows of exp_v211.py (both parts), once, and
write possession-v211-results.json. Written before the validation finished; it only does what the plan says.
Usage: assemble_v211.py OUT_JSON [RESERVED_ROWS_JSON]"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import numpy as np

REPO = Path('/home/claude/sc')
WORK = Path('/home/claude/work')
CONDITIONS = ('none', 'gk_one', 'gk_both', 'gk_part', 'view42_none', 'view35_none', 'view42_gk_both')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(out_json, reserved_json=None):
    plan_path = REPO / 'possession-v211-plan.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    unchanged = {k: sha((REPO if k.startswith('possession') else WORK) / k.replace('work/', '')) == v for k, v in plan['hashes'].items()
                 if k in ('possession/keeper2.py', 'possession/keeper.py', 'work/exp_v211.py', 'work/camera_view.py', 'work/exp_v210.py', 'possession/epts_export.py')}
    if not all(unchanged.values()):
        raise SystemExit(f'a registered file changed: {unchanged}')
    rows = [r for part in (0, 1) for r in json.loads((WORK / f'exp_v211_{part}.json').read_text())['rows']]
    copies = sorted({r['copy'] for r in rows})
    if len(copies) != 8 or len(rows) != 56 or {(r['copy'], r['condition']) for r in rows} != {(c, k) for c in copies for k in CONDITIONS}:
        raise SystemExit(f'expected 8 copies x 7 conditions, found {len(copies)} copies and {len(rows)} rows')
    by = {(r['copy'], r['condition']): r for r in rows}
    mean = lambda v: float(np.mean(v))
    spell = lambda k, s: [by[c, k][s][0] for c in copies]
    diff = {k: [round(b - a, 4) for a, b in zip(spell(k, 'v2_9'), spell(k, 'v2_11'))] for k in CONDITIONS}
    ref = mean(spell('none', 'v2_9'))                      # mean(v2_9 under condition none)

    def neutral(k):
        return {'mean_difference': round(mean(diff[k]), 4), 'worst_copy_difference': min(diff[k]),
                'pass': bool(mean(diff[k]) >= -0.002 and min(diff[k]) >= -0.005)}
    gates = {
        'G1 neutral with correct ids': neutral('none'),
        'G2 both goalkeepers': {'mean_v2_11': round(mean(spell('gk_both', 'v2_11')), 4), 'needed': round(ref - 0.015, 4),
                                'pass': bool(mean(spell('gk_both', 'v2_11')) >= ref - 0.015)},
        'G3 one goalkeeper': {'mean_v2_11': round(mean(spell('gk_one', 'v2_11')), 4), 'needed': round(ref - 0.010, 4),
                              'mean_difference': round(mean(diff['gk_one']), 4), 'needed_difference': 0.008,
                              'pass': bool(mean(spell('gk_one', 'v2_11')) >= ref - 0.010 and mean(diff['gk_one']) >= 0.008)},
        'G4 part of the time': {'mean_v2_11': round(mean(spell('gk_part', 'v2_11')), 4), 'needed': round(ref - 0.010, 4),
                                'mean_difference': round(mean(diff['gk_part']), 4), 'needed_difference': 0.0,
                                'pass': bool(mean(spell('gk_part', 'v2_11')) >= ref - 0.010 and mean(diff['gk_part']) >= 0.0)},
        'G5 neutral when the far goalkeeper is often out of view': neutral('view42_none'),
        'G6 neutral when the far goalkeeper is mostly out of view': neutral('view35_none'),
    }
    passed = all(g['pass'] for g in gates.values())
    summary = {}
    for k in CONDITIONS:
        s = {'spell_f1': {'v2_9': round(mean(spell(k, 'v2_9')), 4), 'v2_11': round(mean(spell(k, 'v2_11')), 4)},
             'macro_f1': {t: round(mean([by[c, k][t][1] for c in copies]), 4) for t in ('v2_9', 'v2_11')},
             'spell_f1_difference_per_copy': diff[k],
             'copies_better_same_worse': [int(sum(d > 0 for d in diff[k])), int(sum(d == 0 for d in diff[k])), int(sum(d < 0 for d in diff[k]))],
             'goalkeeper_positions_with_wrong_id_before_after': [
                 round(mean([by[c, k]['v2_11_moved']['goalkeeper_positions_with_wrong_id_before_after'][i] for c in copies]), 4) for i in (0, 1)],
             'outfield_positions_moved_to_the_wrong_team_per_copy': [by[c, k]['v2_11_moved']['outfield_positions_moved_to_the_wrong_team'] for c in copies],
             'moved_pieces_per_copy': [by[c, k]['v2_11_moved']['pieces'] for c in copies],
             'mean_tracked_in_play': round(mean([by[c, k]['mean_tracked_in_play'] for c in copies]), 2),
             'model_paths': sorted({by[c, k]['path'] for c in copies})}
        if 'goalkeeper_in_view_share' in by[copies[0], k]:
            s['goalkeeper_in_view_share'] = round(mean([by[c, k]['goalkeeper_in_view_share'] for c in copies]), 3)
        if 'v2_10' in by[copies[0], k]:
            d10 = [round(by[c, k]['v2_10'][0] - by[c, k]['v2_9'][0], 4) for c in copies]
            s['v2_10_reported_only'] = {'spell_f1': round(mean([by[c, k]['v2_10'][0] for c in copies]), 4), 'spell_f1_difference_per_copy': d10,
                                        'mean_difference': round(mean(d10), 4), 'worst_copy_difference': min(d10),
                                        'outfield_positions_moved_to_the_wrong_team_per_copy': [
                                            by[c, k]['v2_10_moved']['outfield_positions_moved_to_the_wrong_team'] for c in copies]}
        summary[k] = s
    out = {'version': 'possession-v2.11-results',
           'written_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
           'plan': 'possession-v211-plan.json', 'plan_sha256': sha(plan_path), 'plan_registered_at': plan['registered_at'],
           'registered_files_unchanged': unchanged,
           'reference_mean_v2_9_condition_none': round(ref, 4),
           'copies': copies, 'summary': summary, 'gates': gates,
           'decision': ('all six gates pass: possession-v2.11 becomes the release; possession-v2.9 is the next step of the technical ladder; '
                        'possession-v2.10 is not released' if passed else
                        'a gate fails: possession-v2.9 stays the release; neither possession-v2.11 nor possession-v2.10 is released'),
           'selected': 'possession-v2.11' if passed else 'possession-v2.9',
           'rows': rows}
    if reserved_json and Path(reserved_json).exists():
        out['reserved_metrica_game_3_reporting_only'] = {
            'note': 'one new copy (seed 31103), run once after the decision; not a gate and not used for any choice',
            'rows': json.loads(Path(reserved_json).read_text())['rows']}
    out['limits'] = plan['limits']
    out['provided_fixture_used'] = False
    Path(out_json).write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'reference': out['reference_mean_v2_9_condition_none'], 'gates': gates, 'selected': out['selected']}, indent=1))
    for k in CONDITIONS:
        print(k, summary[k]['spell_f1'], summary[k]['copies_better_same_worse'], summary[k]['goalkeeper_positions_with_wrong_id_before_after'],
              'false', summary[k]['outfield_positions_moved_to_the_wrong_team_per_copy'], summary[k].get('v2_10_reported_only', ''))


if __name__ == '__main__':
    main(*sys.argv[1:])
