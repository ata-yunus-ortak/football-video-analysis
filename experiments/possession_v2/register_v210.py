"""Write possession-v210-plan.json (registered before any result of the candidate on a validation match)."""
import hashlib, json, subprocess
from pathlib import Path
SC = Path('/home/claude/sc'); W = Path('/home/claude/work')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
roles = json.loads((W / 'stress_roles.json').read_text())['rows']
table = {v: {r['match']: r['spell_f1'] for r in roles if r['variant'] == v} for v in ('base', 'gk_one', 'gk_both', 'gk_part', 'ref_home', 'ref_mixed')}
plan = {
    'version': 'possession-v2.10-plan',
    'registered_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
    'motivation': ('DATA.md: "You get positions and team membership, nothing more". The team of a track is decided by the tracker, and a '
                   'goalkeeper wears another kit than his team-mates. A reporting-only diagnostic (experiments/possession_v2/stress_roles.py, '
                   '11 Nov 13:04-13:33; Metrica games 1-3, one corrupted copy each, frozen release logic) measured what happens IF goalkeeper '
                   'tracks carry the other team\'s id: see diagnostic_spell_f1. With both goalkeepers affected the attack directions that '
                   'possession/features.py derives from the mean x of each team are inverted. Whether the provided tracking has this error is '
                   'not known and is not looked at.'),
    'diagnostic_spell_f1': table,
    'candidate': ('possession-v2.10 = possession-v2.9 with possession/keeper.py applied to the tactical tracking that the models see. '
                  'The noise gate, the broadcast alignment, the registration and the 0.50 m gate keep using the tracking as given, exactly as '
                  'in v2.9. Goalkeeper track pieces are found from positions and track continuity (nearest tracked player to a goal while play '
                  'is in the other half; continuation of such a piece) and moved to the team that defends that goal; nothing changes when no '
                  'piece is found in a slot of the wrong team.'),
    'development': ('Rule and constants were developed on the four DFL training matches (J03WOH, J03WOY, J03WPY, J03WQQ; corrupted copies with '
                    'simulated errors, four slot layouts) by counting goalkeeper and other positions with a wrong team id before and after the '
                    'correction, without running a model (work/gk/gk_stats.py, gk_dev.py, gk_diag.py, gk_false.py), and one model check on '
                    'J03WOH, which is in the training set (gk_check.py: ids correct 0.7392 -> 0.7392, both goalkeepers wrong 0.3251 -> 0.7328).'),
    'seen_before_registration': ('The diagnostic rows above (they include validation matches MET1 and MET2 and reserved MET3, release logic WITHOUT '
                                 'the correction) and the development numbers on training matches. No result of the candidate on a validation '
                                 'or reserved match.'),
    'validation': {
        'script': 'experiments/possession_v2/exp_v210.py',
        'matches': ['J03WN1', 'J03WR9', 'MET1', 'MET2'],
        'copies': '8 new corrupted copies: possession.degrade, v2 profile (RANGES), seed 10100 + 10 * match_index + j, j = 0, 1',
        'conditions': {'none': 'team ids as corrupted (degrade moves players to the other team for 1-6 s at random)',
                       'gk_one': "the home goalkeeper's track carries the away team's id for the whole match",
                       'gk_both': "both goalkeepers carry the other team's id for the whole match",
                       'gk_part': "each goalkeeper carries the other team's id during random stretches of 30-300 s covering 30% of the match "
                                  '(seed 20100 + 100 * condition_index + copy_index)'},
        'layout': 'tracks packed into 46 anonymous slots, 23 per team; a track lost for at most 25 frames returns to its slot (possession/epts_export.pack)',
        'systems': {'v2_9': 'noise gate, then the v2.1 or v2.3 path (tactical camera only)',
                    'v2_10': 'the same after possession.keeper.correct_goalkeepers; the noise gate is decided on the tracking as given'},
        'models': 'the validation models (trained on the four training matches only), work/exp_v25.run_path, as in every earlier validation',
        'metric': "spellF1 (organisers' possession_metrics) on the provider / proxy labels",
        'runs': '8 copies x 4 conditions x 2 systems; when the correction moves nothing the two systems are the same run',
        'seeds_checked_unused': '10100-10131, 20100-20407 and 30103 occur in no earlier plan, results file, document or script (searched on registration)',
    },
    'gates': {
        'G1 neutral with correct ids': 'condition none: mean(v2_10 - v2_9) >= -0.002 and no copy below -0.005',
        'G2 both goalkeepers': 'condition gk_both: mean(v2_10) >= mean(v2_9 under condition none) - 0.015',
        'G3 one goalkeeper': 'condition gk_one: mean(v2_10) >= mean(v2_9 under none) - 0.010 and mean(v2_10 - v2_9) >= +0.008',
        'G4 part of the time': 'condition gk_part: mean(v2_10) >= mean(v2_9 under none) - 0.010 and mean(v2_10 - v2_9) >= 0',
    },
    'decision_rule': ('All four gates pass: possession-v2.10 becomes the release (entry point possession.run210, new manifest; possession-v2.9 '
                      'stays as the next step of the technical ladder). Any gate fails: possession-v2.9 stays the release and the candidate is '
                      'reported as not selected. The gates are applied once, to all rows.'),
    'reported_alongside': ['every row; share of goalkeeper positions with a wrong id before and after the correction',
                           'reserved Metrica game 3, one new copy (seed 30103), the four conditions, once, after the decision (not a gate)',
                           'a full-size rehearsal of the entry point on the synthetic provided-like bundle with both goalkeepers exchanged (wiring, not a gate)'],
    'limits': ['The errors are simulated by us; the provided tracking may have none of them or a different kind. The candidate is a safeguard, '
               'not a measured improvement on the provided match.',
               'The correction is validated with the tactical camera only; the broadcast path is unchanged by construction.',
               'A goalkeeper who is not tracked at all cannot be corrected.',
               'Fixtures accessed before; the validation matches have been used for every earlier selection.'],
    'hashes': {'possession/keeper.py': sha(SC / 'possession' / 'keeper.py'), 'work/exp_v210.py': sha(W / 'exp_v210.py'),
               'possession/epts_export.py': sha(SC / 'possession' / 'epts_export.py'), 'possession-v29-release.json': sha(SC / 'possession-v29-release.json'),
               'work/stress_roles.py': sha(W / 'stress_roles.py'), 'work/stress_roles.json': sha(W / 'stress_roles.json')},
    'provided_fixture_used': False,
}
(SC / 'possession-v210-plan.json').write_text(json.dumps(plan, indent=1) + '\n', encoding='utf-8')
print('registered', plan['registered_at'])
