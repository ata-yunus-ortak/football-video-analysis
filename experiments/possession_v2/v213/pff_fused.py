"""After the decision of possession-v213-plan.json, once: possession-v2.11, the fusion and the TCN alone on PFF FC World
Cup 2022 game 3839 as converted for K009 (experiments/possession_v2/pff_viewer/convert_pff.py), against the proxy built
from PFF's events (run_pff.reference). Reported, not a gate: the data has no published licence and is not used for
selection. Nothing is fitted or chosen here; v2.11's side is exactly run_pff.py (released bundles, no second camera).
Usage (from the folder that holds 3839_match.npz and raw/): /usr/bin/python3 /home/claude/work/v213/pff_fused.py 3839
Writes v213/pff_{game}_fused.json and {game}_labels_fused.npz (labels of the three systems, for the viewer)."""
import sys, json, hashlib
import numpy as np
sys.path.insert(0, '/home/claude/sc/experiments/possession_v2/pff_viewer')
import exp_v213 as E                      # sets the import paths; TCN helpers and released bundles
from run_pff import reference
from possession.noise import estimate_noise, choose_path
from possession.keeper2 import correct_goalkeepers
from possession.evaluate import score


def main(game):
    z = np.load(f'{game}_match.npz')
    match = {'fps': float(z['fps']), 'pitch': z['pitch'].astype(float), 'ball': z['ball'], 'players': z['players'],
             'team': z['team'].astype(np.int8), 'period': z['period'].astype(np.int8)}
    per = match['period']
    path, _ = choose_path(estimate_noise(match))
    fixed, keeper = correct_goalkeepers(match)
    lab11, pd_, ph = E.v2_released(path, fixed)
    fused, alone = E.tcn_labels(E.members('tcn_dfl6.npz'), fixed, per, pd_, ph)
    ref = reference(game, z['t_video'], per)
    play = per > 0
    out = {'game': game, 'path': path, 'goalkeeper_moved_pieces': keeper.get('moved_pieces'), 'tcn_weights': 'tcn_dfl6.npz',
           'fusion': {'weight': E.tfuse.WEIGHT, 'switch_cost': E.tfuse.SWITCH_COST},
           'ball_visible_in_play': round(float(np.isfinite(match['ball']).all(1)[play].mean()), 3),
           'note': 'agreement with an event-derived proxy built by us from PFF events; not ground truth, not a competition score, '
                   'not a gate; no published licence, reporting only'}
    for name, lab in (('v2_11', lab11), ('fused', fused), ('tcn_alone', alone)):
        s = score(ref, lab, per)
        out[name] = {'spell_f1': float(s['spell_f1_mean']), 'macro_f1': float(s['macro_f1']),
                     'frame_agreement_in_play': float(np.mean(lab[play] == ref[play])),
                     'label_shares_in_play': {k: round(float(np.mean(lab[play] == k)), 3) for k in 'HAD'}}
    out['frames_changed_v2_11_to_fused'] = int(np.sum(lab11 != fused))
    out['sha256'] = {'match_npz': hashlib.sha256(open(f'{game}_match.npz', 'rb').read()).hexdigest(),
                     'pff_fused.py': E.sha(E.V213 + 'pff_fused.py')}
    np.savez_compressed(f'{game}_labels_fused.npz', v2_11=lab11, fused=fused, tcn_alone=alone, pff=ref)
    json.dump(out, open(f'{E.V213}pff_{game}_fused.json', 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
