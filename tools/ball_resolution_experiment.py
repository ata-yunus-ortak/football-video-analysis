"""Fixed external resolution ablation; labels are read only after prediction freeze."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from development.vision import LocalVision, VisionConfig
from development.vision_box_audit import match_boxes
from tools.ball_candidate_selection import write
from tools.ball_detector_data import safe_member
from tools.metrica_data import external_output, sha256


def registered_jobs(gallery, plan):
    clips = json.loads(Path(gallery).read_text())['clips']
    games = plan['development_games']+plan['fixed_recheck_games']
    if len(set(games)) != len(games) or set(games) != {str(c['source_game_id']) for c in clips}:
        raise ValueError('Disjoint registered game groups required')
    if type(plan['frame_stride']) is not int or plan['frame_stride'] < 1:
        raise ValueError('Positive integer sampling stride required')
    jobs = []; provenance = {}
    for c in clips:
        study = Path(c['study']); sample = study/'sample-v2'
        registration = json.loads((sample/'before-access.json').read_text())['plan']
        if any(registration[k] != plan[k] for k in ('dataset','archive','provided_fixture_used')):
            raise ValueError('Only registered external frames allowed')
        manifest = json.loads((sample/'manifest.json').read_text())
        mapping = json.loads((study/'video-v1/video-manifest.json').read_text())
        if not manifest['complete'] or not mapping['rgb_lossless_verified'] or mapping['provided_fixture_used']:
            raise ValueError('Verified external pixel correspondence required')
        specs = {r['member']: r for r in manifest['acquired_files']}
        provenance[c['id']] = {'manifest_sha256': sha256(sample/'manifest.json'),
            'mapping_sha256': sha256(study/'video-v1/video-manifest.json')}
        for source in mapping['frames'][::plan['frame_stride']]:
            spec = specs[source['member']]
            path = safe_member(sample/'sample', source['member'])
            if sha256(path) != spec['sha256']:
                raise ValueError('Image changed')
            jobs.append({'clip': c['id'], 'game': str(c['source_game_id']),
                'source_frame': source['source_frame'], 'member': source['member'],
                'path': str(path), 'sha256': spec['sha256'], 'rgb_sha256': source['rgb_sha256']})
    return clips, jobs, provenance


def box_summary(rows):
    result = {}
    for game in sorted({r['game'] for r in rows}):
        counts = {'frames': 0, 'references': 0, 'predictions': 0, 'matched': 0,
                  'unmatched_predictions': 0, 'predictions_on_unannotated_frames': 0}
        for r in rows:
            if r['game'] != game:
                continue
            match = match_boxes(r['predictions'], r['references'], .5)
            counts['frames'] += 1; counts['references'] += len(r['references'])
            counts['predictions'] += len(r['predictions']); counts['matched'] += len(match['matches'])
            counts['unmatched_predictions'] += match['unmatched_predictions']
            if not r['references']:
                counts['predictions_on_unannotated_frames'] += len(r['predictions'])
        counts['precision_proxy'] = counts['matched']/counts['predictions'] if counts['predictions'] else 0.
        counts['recall'] = counts['matched']/counts['references'] if counts['references'] else 0.
        result[game] = counts
    return result


def gate(base, candidate):
    return (set(base) == set(candidate) and bool(base) and all(
        b['references'] > 0 and b['matched'] > 0
        and candidate[g]['matched'] >= 1.2*b['matched']
        and candidate[g]['unmatched_predictions'] <= 1.25*b['unmatched_predictions']
        for g,b in base.items()))


def score(clips, jobs, out, plan):
    freeze = json.loads((out/'prediction-freeze.json').read_text())
    if any(sha256(out/p) != h for p,h in freeze['files'].items()):
        raise ValueError('Prediction freeze mismatch')
    refs = {}; provenance = {}
    for c in clips:
        sample = Path(c['study'])/'sample-v2'
        manifest = json.loads((sample/'manifest.json').read_text())
        spec = next(s for s in manifest['acquired_files'] if s['member'].endswith('Labels-GameState.json'))
        path = safe_member(sample/'sample', spec['member'])
        if sha256(path) != spec['sha256']:
            raise ValueError('Reference changed')
        data = json.loads(path.read_text()); provenance[c['id']] = spec['sha256']
        ball_id = next(cat['id'] for cat in data['categories'] if cat['name']=='ball')
        by_id = defaultdict(list)
        for a in data['annotations']:
            if a.get('category_id') == ball_id:
                b = a['bbox_image']
                by_id[a['image_id']].append({'box_xyxy':[b['x'],b['y'],b['x']+b['w'],b['y']+b['h']]})
        for image in data['images']:
            refs[c['id'], image['file_name']] = by_id[image['image_id']]
    summaries = {}
    for mode in plan['modes']:
        predictions = [json.loads(line) for line in (out/(mode+'.jsonl')).read_text().splitlines()]
        if len(predictions) != len(jobs):
            raise ValueError('Incomplete prediction list')
        for row, job in zip(predictions, jobs):
            if (row['clip'], row['source_frame'], row['rgb_sha256']) != (job['clip'],job['source_frame'],job['rgb_sha256']):
                raise ValueError('Prediction correspondence changed')
            row['references'] = refs[job['clip'],Path(job['member']).name]
        summaries[mode] = box_summary(predictions)
    accepted = gate(summaries['baseline'], summaries['native_scale_tiles'])
    report = {'version': plan['version'], 'accepted_for_extended_validation': accepted,
        'selected_release': False, 'provided_fixture_used': False, 'independent_test': False,
        'summaries': summaries, 'reference_sha256': provenance,
        'prediction_freeze_sha256': sha256(out/'prediction-freeze.json'),
        'elapsed_seconds': freeze['elapsed_seconds'], 'limits': plan['limits']}
    write(out/'report.json', report); print(json.dumps(report, indent=2), flush=True)
    return report


def run(gallery, plan_path, weights, out):
    plan = json.loads(Path(plan_path).read_text())
    if plan['provided_fixture_used'] or plan['dataset'] != 'SoccerNet/SN-GSR-2024' or plan['archive'] != 'train.zip':
        raise ValueError('External registered data only')
    if sha256(weights) != plan['initial_weights_sha256']:
        raise ValueError('Official registered Nano weights required')
    out = external_output(out); out.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parents[1]
    source_files = ['tools/ball_resolution_experiment.py','development/vision.py','development/vision_box_audit.py']
    before = {'plan':plan, 'source_hashes':{p:sha256(repo/p) for p in source_files},
              'plan_sha256':sha256(plan_path), 'gallery_sha256':sha256(gallery), 'labels_read':False}
    write(out/'before-inference.json', before)
    clips, jobs, provenance = registered_jobs(gallery, plan)
    write(out/'input-freeze.json', {'jobs':jobs, 'provenance':provenance})
    from PIL import Image
    import torch
    from importlib.metadata import version
    write(out/'runtime.json', {p:version(p) for p in ('rfdetr','torch','torchvision','sahi','numpy')})
    durations = {}; outputs = {}
    for mode, tile in plan['modes'].items():
        cfg = VisionConfig('nano',plan['threshold'],True,tile['height'],tile['width'],
                           plan['overlap_ratio'],.3,.8,1.,1)
        engine = LocalVision(cfg, Path(weights), 25/plan['frame_stride'], 'cuda')
        start = time.perf_counter(); path = out/(mode+'.jsonl')
        with path.open('w', encoding='utf-8', newline='\n') as stream:
            for i,job in enumerate(jobs):
                if sha256(job['path']) != job['sha256']:
                    raise ValueError('Image changed after freeze')
                with Image.open(job['path']) as im:
                    rgb = np.asarray(im.convert('RGB'))
                if hashlib.sha256(rgb.tobytes()).hexdigest() != job['rgb_sha256']:
                    raise ValueError('Decoded pixel correspondence differs')
                # People are only used internally by the unchanged adapter;
                # no person/tracking/reference feature influences these ball boxes.
                objects = engine.process(rgb)
                predictions = [{'box_xyxy':r['box_xyxy'], 'confidence':r['confidence']}
                               for r in objects if r['kind']=='sports ball']
                stream.write(json.dumps({k:job[k] for k in ('clip','game','source_frame','rgb_sha256')}
                                        | {'predictions':predictions})+'\n')
                if (i+1)%15 == 0:
                    print(f'{mode}: {i+1}/{len(jobs)} frames', flush=True)
        durations[mode] = time.perf_counter()-start; outputs[path.name] = sha256(path)
        del engine; torch.cuda.empty_cache()
    if any(sha256(repo/p)!=h for p,h in before['source_hashes'].items()):
        raise ValueError('Experiment source changed')
    write(out/'prediction-freeze.json', {'files':outputs,'elapsed_seconds':durations,'before_reference_scoring':True})
    return score(clips,jobs,out,plan)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('gallery','weights','out'):
        p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='ball-resolution-plan.json')
    a=p.parse_args(); run(a.gallery,a.plan,a.weights,a.out)
