"""Descriptive localization sensitivity; never selects detector thresholds."""
import argparse
import json
from pathlib import Path
import numpy as np
from development.vision_box_audit import iou, match_boxes
from tools.ball_candidate_selection import load_group, write
from tools.metrica_data import external_output, sha256


def describe(frames):
    result = {}
    for mode in sorted({f['mode'] for f in frames}):
        counts = {str(t): 0 for t in (.1, .25, .5, .75)}
        best_overlap = []; centres = []; diagonal_errors = []
        no_overlap = near_miss = duplicate = total = refs_count = empty_predictions = 0
        for f in frames:
            if f['mode'] != mode:
                continue
            preds, refs = f['predictions'], f['references']
            total += len(preds); refs_count += len(refs)
            if not refs:
                empty_predictions += len(preds)
            for threshold in counts:
                counts[threshold] += len(match_boxes(preds, refs, float(threshold))['matches'])
            maximum = [max((iou(p['box_xyxy'], r['box_xyxy']) for r in refs), default=0.) for p in preds]
            # Unannotated frames cannot establish that a candidate is a false positive.
            no_overlap += sum(v < .1 for v in maximum) if refs else 0
            near_miss += sum(.1 <= v < .5 for v in maximum)
            duplicate += sum(v >= .5 for v in maximum)-len(match_boxes(preds, refs, .5)['matches'])
            for ref in refs:
                b = np.asarray(ref['box_xyxy']); centre = (b[:2]+b[2:])/2
                diagonal = float(np.linalg.norm(b[2:]-b[:2]))
                best_overlap.append(max((iou(p['box_xyxy'], b) for p in preds), default=0.))
                if preds:
                    errors = [float(np.linalg.norm((np.asarray(p['box_xyxy'])[:2]+
                        np.asarray(p['box_xyxy'])[2:])/2-centre)) for p in preds]
                    centres.append(min(errors)); diagonal_errors.append(min(errors)/diagonal)
        def quantiles(values):
            return np.quantile(values, [.25, .5, .75, .9]).tolist() if values else None
        result[mode] = {'reference_boxes': refs_count, 'predicted_boxes': total,
            'one_to_one_matches_by_iou': counts, 'reference_best_iou_quartiles_and_p90': quantiles(best_overlap),
            'nearest_centre_error_px_quartiles_and_p90': quantiles(centres),
            'nearest_centre_error_reference_diagonals_quartiles_and_p90': quantiles(diagonal_errors),
            'centre_error_scored_references': len(centres),
            'predictions_iou_below_0_1_on_annotated_frames': no_overlap,
            'predictions_iou_0_1_to_0_5': near_miss, 'duplicate_high_overlap_predictions': duplicate,
            'predictions_on_unannotated_ball_frames': empty_predictions}
    return result


def run(gallery, analysis, out):
    clips = json.loads(Path(gallery).read_text())['clips']
    out = external_output(out); out.mkdir(parents=True, exist_ok=False)
    write(out/'before-access.json', {'source_sha256': sha256(__file__),
        'gallery_sha256': sha256(gallery), 'thresholds': [.1, .25, .5, .75],
        'purpose': 'descriptive_only_no_model_or_threshold_selection', 'provided_fixture_used': False})
    frames, provenance = load_group(clips, {str(c['source_game_id']) for c in clips},
                                   Path(analysis), ['native', 'sliced'])
    report = {'counts': describe(frames), 'provenance': provenance,
        'provided_fixture_used': False, 'model_changed': False, 'independent_test': False,
        'limitations': 'Nearest centre can belong to a false candidate; distances are pixel diagnostics, not physical ball accuracy. Empty ball annotations are not certified negatives. Sensitivity thresholds are not replacement acceptance criteria.'}
    write(out/'report.json', report)
    print(json.dumps(report['counts'], indent=2))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('gallery', 'analysis', 'out'):
        p.add_argument('--'+k, required=True)
    a = p.parse_args(); run(a.gallery, a.analysis, a.out)
