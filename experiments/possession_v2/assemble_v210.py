"""Apply the four registered gates of possession-v210-plan.json to the rows of exp_v210.py, once, and write
possession-v210-results.json. Written before the validation finished; it only does what the plan says.
Usage: assemble_v210.py ROWS_JSON OUT_JSON [RESERVED_ROWS_JSON]"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import numpy as np

REPO = Path('/home/claude/sc')
WORK = Path('/home/claude/work')
CONDITIONS = ('none', 'gk_one', 'gk_both', 'gk_part')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(rows_json, out_json, reserved_json=None):
    plan_path = REPO / 'possession-v210-plan.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    unchanged = {'possession/keeper.py': sha(REPO / 'possession/keeper.py') == plan['hashes']['possession/keeper.py'],
                 'exp_v210.py': sha(WORK / 'exp_v210.py') == plan['hashes']['work/exp_v210.py'],
                 'possession/epts_export.py': sha(REPO / 'possession/epts_export.py') == plan['hashes']['possession/epts_export.py']}
    if not all(unchanged.values()):
        raise SystemExit(f'a registered file changed: {unchanged}')
    rows = json.loads(Path(rows_json).read_text())['rows']
    copies = sorted({r['copy'] for r in rows})
    if len(copies) != 8 or len(rows) != 32 or {(r['copy'], r['condition']) for r in rows} != {(c, k) for c in copies for k in CONDITIONS}:
        raise SystemExit(f'expected 8 copies x 4 conditions, found {len(copies)} copies and {len(rows)} rows')
    by = {(r['copy'], r['condition']): r for r in rows}
    spell = {k: {s: [by[c, k][s][0] for c in copies] for s in ('v2_9', 'v2_10')} for k in CONDITIONS}
    macro = {k: {s: [by[c, k][s][1] for c in copies] for s in ('v2_9', 'v2_10')} for k in CONDITIONS}
    mean = lambda v: float(np.mean(v))
    diff = {k: [round(b - a, 4) for a, b in zip(spell[k]['v2_9'], spell[k]['v2_10'])] for k in CONDITIONS}
    ref = mean(spell['none']['v2_9'])                      # mean(v2_9 under condition none)
    gates = {
        'G1 neutral with correct ids': {
            'mean_difference': round(mean(diff['none']), 4), 'worst_copy_difference': min(diff['none']),
            'pass': bool(mean(diff['none']) >= -0.002 and min(diff['none']) >= -0.005)},
        'G2 both goalkeepers': {
            'mean_v2_10': round(mean(spell['gk_both']['v2_10']), 4), 'needed': round(ref - 0.015, 4),
            'pass': bool(mean(spell['gk_both']['v2_10']) >= ref - 0.015)},
        'G3 one goalkeeper': {
            'mean_v2_10': round(mean(spell['gk_one']['v2_10']), 4), 'needed': round(ref - 0.010, 4),
            'mean_difference': round(mean(diff['gk_one']), 4), 'needed_difference': 0.008,
            'pass': bool(mean(spell['gk_one']['v2_10']) >= ref - 0.010 and mean(diff['gk_one']) >= 0.008)},
        'G4 part of the time': {
            'mean_v2_10': round(mean(spell['gk_part']['v2_10']), 4), 'needed': round(ref - 0.010, 4),
            'mean_difference': round(mean(diff['gk_part']), 4), 'needed_difference': 0.0,
            'pass': bool(mean(spell['gk_part']['v2_10']) >= ref - 0.010 and mean(diff['gk_part']) >= 0.0)},
    }
    passed = all(g['pass'] for g in gates.values())
    summary = {k: {'spell_f1': {s: round(mean(spell[k][s]), 4) for s in ('v2_9', 'v2_10')},
                   'macro_f1': {s: round(mean(macro[k][s]), 4) for s in ('v2_9', 'v2_10')},
                   'spell_f1_difference_per_copy': diff[k],
                   'copies_better_same_worse': [int(sum(d > 0 for d in diff[k])), int(sum(d == 0 for d in diff[k])), int(sum(d < 0 for d in diff[k]))],
                   'goalkeeper_positions_with_wrong_id_before_after': [round(mean([by[c, k]['goalkeeper_positions_with_wrong_id'][i] for c in copies]), 4) for i in (0, 1)],
                   'moved_pieces_per_copy': [by[c, k]['moved_pieces'] for c in copies],
                   'model_paths': sorted({by[c, k]['path'] for c in copies})}
               for k in CONDITIONS}
    out = {'version': 'possession-v2.10-results',
           'written_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
           'plan': 'possession-v210-plan.json', 'plan_sha256': sha(plan_path), 'plan_registered_at': plan['registered_at'],
           'registered_files_unchanged': unchanged,
           'reference_mean_v2_9_condition_none': round(ref, 4),
           'copies': copies, 'summary': summary, 'gates': gates,
           'decision': ('all four gates pass: possession-v2.10 becomes the release; possession-v2.9 is the next step of the technical ladder'
                        if passed else 'a gate fails: possession-v2.9 stays the release; the candidate is not selected'),
           'selected': 'possession-v2.10' if passed else 'possession-v2.9',
           'rows': rows}
    if reserved_json and Path(reserved_json).exists():
        res = json.loads(Path(reserved_json).read_text())['rows']
        out['reserved_metrica_game_3_reporting_only'] = {
            'note': 'one new copy (seed 30103), run once after the decision; not a gate and not used for any choice',
            'rows': res}
    out['limits'] = plan['limits']
    out['provided_fixture_used'] = False
    Path(out_json).write_text(json.dumps(out, indent=1), encoding='utf-8')
    print(json.dumps({'reference': out['reference_mean_v2_9_condition_none'], 'gates': gates, 'selected': out['selected']}, indent=1))
    for k in CONDITIONS:
        print(k, summary[k]['spell_f1'], summary[k]['copies_better_same_worse'], summary[k]['goalkeeper_positions_with_wrong_id_before_after'])


if __name__ == '__main__':
    main(*sys.argv[1:])
