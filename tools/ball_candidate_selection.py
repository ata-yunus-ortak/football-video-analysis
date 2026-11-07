"""Registered external ball proposal selection with game-separated recheck."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import numpy as np
from development import ball_candidate_filter as model
from development.vision_box_audit import iou, match_boxes
from tools.metrica_data import external_output, sha256


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def load_group(clips, games, analysis, modes):
    frames = []
    provenance = {}
    for clip in clips:
        if str(clip['source_game_id']) not in games:
            continue
        study = Path(clip['study']); sample = study/'sample-v2'
        plan = json.loads((sample/'before-access.json').read_text())['plan']
        if (plan['dataset'] != 'SoccerNet/SN-GSR-2024' or plan['archive'] != 'train.zip'
                or plan['provided_fixture_used'] is not False):
            raise ValueError('Registered external training data only')
        manifest = json.loads((sample/'manifest.json').read_text())
        spec = next(s for s in manifest['acquired_files'] if s['member'].endswith('Labels-GameState.json'))
        path = sample/'sample'/spec['member']
        if sha256(path) != spec['sha256']:
            raise ValueError('External reference changed')
        labels = json.loads(path.read_text())
        category = next(c['id'] for c in labels['categories'] if c['name'] == 'ball')
        images = {r['file_name']: r['image_id'] for r in labels['images']}
        targets = defaultdict(list)
        for r in labels['annotations']:
            if r.get('category_id') == category:
                b = r['bbox_image']
                targets[r['image_id']].append({'box_xyxy': [b['x'], b['y'], b['x']+b['w'], b['y']+b['h']]})
        mapping_path = study/'video-v1/video-manifest.json'
        mapping = json.loads(mapping_path.read_text())['frames']
        provenance[clip['id']] = {'reference_sha256': spec['sha256'],
                                  'mapping_sha256': sha256(mapping_path), 'analyses': {}}
        for mode in modes:
            path = analysis/clip['id']/mode/'frames.jsonl'
            packets = [json.loads(s) for s in path.read_text().splitlines()]
            provenance[clip['id']]['analyses'][mode] = sha256(path)
            if len(packets) != len(mapping):
                raise ValueError('Frame count mismatch')
            for packet, source in zip(packets, mapping):
                if packet['source_frame'] != source['source_frame']:
                    raise ValueError('Frame correspondence mismatch')
                refs = targets[images[Path(source['member']).name]]
                people = [r['box_xyxy_px'] for r in packet['objects'] if r['kind'] == 'person_candidate']
                balls = [r for r in packet['objects'] if r['kind'] == 'ball_candidate']
                predictions = [{'box_xyxy': r['box_xyxy_px'], 'confidence': r['confidence']} for r in balls]
                raw = np.asarray([model.features(r['box_xyxy_px'], r['confidence'], people,
                                                packet['image_size_px']) for r in balls]).reshape(-1, 5)
                frames.append({'clip': clip['id'], 'game': str(clip['source_game_id']),
                               'mode': mode, 'raw': raw, 'predictions': predictions, 'references': refs})
    if not frames:
        raise ValueError('Empty fixture group')
    return frames, provenance


def training_rows(frames):
    rows, targets, groups = [], [], []
    for frame in frames:
        if not frame['references']:
            continue
        for raw, pred in zip(frame['raw'], frame['predictions']):
            overlap = max(iou(pred['box_xyxy'], r['box_xyxy']) for r in frame['references'])
            if overlap >= .5 or overlap <= .1:
                rows.append(raw); targets.append(int(overlap >= .5))
                groups.append(frame['clip']+'/'+frame['mode'])
    counts = {g: groups.count(g) for g in set(groups)}
    return np.asarray(rows), np.asarray(targets), np.asarray([1/counts[g] for g in groups])


def evaluate(frames, candidate):
    result = {}
    for mode in sorted({f['mode'] for f in frames}):
        matched = predicted = reference = 0
        for f in frames:
            if f['mode'] != mode:
                continue
            pred = f['predictions']
            if len(pred) and candidate['kind'] != 'keep_all':
                scores = (f['raw'][:, 0] if candidate['kind'] == 'confidence'
                          else model.probability(f['raw'], candidate['model']))
                pred = [r for r, score in zip(pred, scores) if score >= candidate['threshold']]
            match = match_boxes(pred, f['references'], .5)
            matched += len(match['matches']); predicted += len(pred); reference += len(f['references'])
        result[mode] = {'matched': matched, 'predicted': predicted, 'reference': reference,
                        'unmatched_predictions': predicted-matched,
                        'precision': matched/predicted if predicted else 0.,
                        'recall': matched/reference if reference else 0.,
                        'f1': 2*matched/(predicted+reference) if predicted+reference else 0.}
    return result


def passes(scores, baseline):
    return all(baseline[m]['matched'] > 0 and baseline[m]['unmatched_predictions'] > 0
               and s['matched'] >= .95*baseline[m]['matched']
               and s['unmatched_predictions'] <= .8*baseline[m]['unmatched_predictions']
               for m, s in scores.items()) and set(scores) == set(baseline)


def rank(scores):
    tp = sum(s['matched'] for s in scores.values())
    total = sum(s['predicted']+s['reference'] for s in scores.values())
    return (2*tp/total if total else 0., tp, -sum(s['unmatched_predictions'] for s in scores.values()))


def run(gallery, analysis, plan_path, out):
    repo = Path(__file__).resolve().parents[1]
    plan = json.loads(Path(plan_path).read_text())
    if plan['provided_fixture_used'] or plan['dataset'] != 'SoccerNet/SN-GSR-2024':
        raise ValueError('External registered plan required')
    groups = [set(plan[k]) for k in ('train_games', 'validation_games', 'recheck_games')]
    if any(groups[i] & groups[j] for i in range(3) for j in range(i)):
        raise ValueError('Game partitions overlap')
    clips = json.loads(Path(gallery).read_text())['clips']
    if {str(c['source_game_id']) for c in clips} != set.union(*groups):
        raise ValueError('Gallery games differ from registered split')
    analysis = Path(analysis); out = external_output(out); out.mkdir(parents=True, exist_ok=False)
    sources = ['development/ball_candidate_filter.py', 'development/learned_dead_ball.py',
               'development/vision_box_audit.py', 'tools/ball_candidate_selection.py']
    freeze = {'source_hashes': {p: sha256(repo/p) for p in sources},
              'plan_sha256': sha256(plan_path), 'gallery_sha256': sha256(gallery),
              'analysis_hashes': {str(analysis/c['id']/m/'frames.jsonl'):
                  sha256(analysis/c['id']/m/'frames.jsonl') for c in clips for m in plan['modes']}}
    write(out/'before-access.json', {'plan': plan, **freeze})
    train, train_provenance = load_group(clips, groups[0], analysis, plan['modes'])
    raw, target, weights = training_rows(train)
    candidates = [{'kind': 'keep_all'}]
    candidates += [{'kind': 'confidence', 'threshold': t} for t in plan['confidence_thresholds']]
    for l2 in plan['l2']:
        learned = model.fit(raw, target, weights, l2)
        candidates += [{'kind': 'learned', 'model': learned, 'threshold': t} for t in plan['thresholds']]
    write(out/'trained-candidates.json', {'candidates': candidates,
        'training_rows': len(raw), 'training_positives': int(target.sum()), 'provenance': train_provenance})
    validation, vp = load_group(clips, groups[1], analysis, plan['modes'])
    scores = [evaluate(validation, c) for c in candidates]
    eligible = [i for i in range(1, len(candidates)) if passes(scores[i], scores[0])]
    # Keep a diagnostic best candidate even if no candidate qualifies; never promote it.
    selected = max(eligible or list(range(1, len(candidates))), key=lambda i: rank(scores[i]))
    write(out/'validation.json', {'scores': scores, 'eligible': eligible, 'selected': selected, 'provenance': vp})
    chosen = {'candidate': candidates[selected], 'selection_accepted': selected in eligible,
              'validation': scores[selected], 'validation_baseline': scores[0], **freeze}
    write(out/'candidate-freeze.json', chosen)
    recheck, rp = load_group(clips, groups[2], analysis, plan['modes'])
    check = evaluate(recheck, candidates[selected]); base = evaluate(recheck, candidates[0])
    accepted = selected in eligible and passes(check, base)
    if any(sha256(repo/p) != h for p, h in freeze['source_hashes'].items()):
        raise ValueError('Source changed during study')
    if any(sha256(p) != h for p, h in freeze['analysis_hashes'].items()):
        raise ValueError('Input changed during study')
    report = {'version': plan['version'], 'accepted': accepted, 'candidate_kind': candidates[selected]['kind'],
              'threshold': candidates[selected].get('threshold'), 'selection_accepted': selected in eligible,
              'validation': scores[selected], 'validation_baseline': scores[0],
              'recheck': check, 'recheck_baseline': base, 'recheck_provenance': rp,
              'candidate_sha256': sha256(out/'candidate-freeze.json'),
              'source_hashes': freeze['source_hashes'], 'training_rows': len(raw),
              'training_positives': int(target.sum()), 'provided_fixture_used': False,
              'independent_test': False, 'in_play_ball_validated': False, 'possession_validated': False,
              'limitation': plan['limits']}
    write(out/'report.json', report)
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('gallery', 'analysis', 'out'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--plan', default='ball-candidate-selection-plan.json')
    args = parser.parse_args()
    run(args.gallery, args.analysis, args.plan, args.out)
