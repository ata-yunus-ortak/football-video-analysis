"""Post-inference GSR training sample box coverage; labels never enter inference."""
import argparse
from collections import Counter
import json
from pathlib import Path

from development.vision_box_audit import match_boxes
from .metrica_data import external_output, sha256


def reference_rows(labels, image_id, names):
    rows = []
    for annotation in labels['annotations']:
        if annotation['image_id'] != image_id: continue
        name = names[annotation['category_id']]
        if name not in ('player', 'goalkeeper', 'referee', 'other', 'ball'): continue
        box = annotation['bbox_image']
        rows.append({'kind': 'sports ball' if name == 'ball' else 'person',
                     'role': name, 'box_xyxy': [box['x'], box['y'], box['x'] + box['w'], box['y'] + box['h']]})
    return rows


def run(sample, video_dir, observations, plan, out):
    sample, video_dir, observations, plan = map(Path, (sample, video_dir, observations, plan))
    acquisition = json.loads((sample / 'before-access.json').read_text())
    if acquisition['plan']['dataset'] != 'SoccerNet/SN-GSR-2024' or acquisition['plan']['archive'] != 'train.zip':
        raise ValueError('Only registered GSR training sample allowed')
    manifest = json.loads((video_dir / 'video-manifest.json').read_text())
    registration = json.loads((observations / 'registration.json').read_text())
    summary = json.loads((observations / 'summary.json').read_text())
    evaluation = json.loads(plan.read_text())
    if (registration['provided_fixture_used'] is not False or manifest['provided_fixture_used'] is not False
            or registration['config']['fixture']['id'] != 'soccernet-gsr-SNGS-060-first25'
            or registration['config']['fixture']['video_sha256'] != manifest['video_sha256']
            or summary['processed_frames'] != 25 or len(manifest['frames']) != 25
            or manifest['sample_manifest_sha256'] != sha256(sample / 'manifest.json')
            or sha256(manifest['video']) != manifest['video_sha256']):
        raise ValueError('Completed same-source 25-frame training predictions required')
    out = external_output(out)
    out.mkdir(parents=True, exist_ok=False)
    observation_path = observations / 'observations.jsonl'
    frozen_predictions = sha256(observation_path)
    (out / 'before-evaluation.json').write_text(json.dumps({
        'predictions_sha256': frozen_predictions, 'evaluation_plan_sha256': sha256(plan),
        'registration_sha256': sha256(observations / 'registration.json'),
        'source_sha256': {str(p): sha256(p) for p in (Path(__file__), Path(__file__).parents[1] / 'development/vision_box_audit.py')},
        'labels_used_as_inference_inputs': False}, indent=2))
    receipt = json.loads((sample / 'manifest.json').read_text())
    label_spec = next(r for r in receipt['acquired_files'] if r['member'].endswith('Labels-GameState.json'))
    label_path = sample / 'sample' / label_spec['member']
    if sha256(label_path) != label_spec['sha256']: raise ValueError('Reference changed')
    labels = json.loads(label_path.read_text())
    if labels['info']['version'] != '1.3' or labels['info']['frame_rate'] != manifest['fps']:
        raise ValueError('Unaudited reference version or clock mismatch')
    images = {r['file_name']: r for r in labels['images']}
    names = {r['id']: r['name'] for r in labels['categories']}
    predictions = [json.loads(line) for line in observation_path.read_text().splitlines()]
    if len(predictions) != 25: raise ValueError('Prediction frame count differs')
    totals = {kind: Counter() for kind in ('person', 'sports ball')}
    roles = Counter()
    for frame, mapping in zip(predictions, manifest['frames']):
        image = images[Path(mapping['member']).name]
        if (frame['source_frame'] != mapping['source_frame'] or image['is_labeled'] is not True
                or image['has_labeled_person'] is not True or image['ignore_regions_x'] or image['ignore_regions_y']
                or (frame['width'], frame['height']) != (image['width'], image['height'])):
            raise ValueError('Frame mapping, annotation coverage/ignore region or dimensions differ')
        references = reference_rows(labels, image['image_id'], names)
        roles.update(r['role'] for r in references)
        for kind in totals:
            result = match_boxes([r for r in frame['objects'] if r['kind'] == kind],
                                 [r for r in references if r['kind'] == kind], evaluation['iou_threshold'])
            totals[kind].update({key: value for key, value in result.items() if key != 'matches'})
            totals[kind]['matched_boxes'] += len(result['matches'])
    report = {'source_game_id': labels['info']['game_id'], 'sequence': labels['info']['name'],
        'frames': 25, 'reference_version': labels['info']['version'], 'source_metadata_fps': labels['info']['frame_rate'],
        'role_observations': dict(roles), 'iou_threshold': evaluation['iou_threshold'], 'boxes': {},
        'official_metric': False, 'independent_test': False, 'selected_release': False,
        'ball_audit': 'Exploratory schema-confirmed box coverage, not independent in-play-ball validation',
        'labels_used_as_inference_inputs': False, 'reference_sha256': sha256(label_path),
        'possession_evaluated': False, 'field_coordinates_evaluated': False, 'teams_evaluated': False,
        'runtime_s': summary['elapsed_s_including_model_load']}
    for kind, counts in totals.items():
        report['boxes'][kind] = dict(counts, annotated_box_recall=(counts['matched_boxes'] / counts['reference_count']
            if counts['reference_count'] else None))
    if sha256(observation_path) != frozen_predictions: raise ValueError('Predictions changed during audit')
    (out / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('sample', 'video-dir', 'observations', 'plan', 'out'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    run(args.sample, args.video_dir, args.observations, args.plan, args.out)
