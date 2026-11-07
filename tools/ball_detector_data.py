"""Manifest-verified external ball-only COCO export; supplied fixtures rejected."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path, PurePosixPath
import shutil
from tools.metrica_data import external_output, sha256
from tools.ball_candidate_selection import write


def safe_member(root, member):
    p = PurePosixPath(member)
    if p.is_absolute() or '..' in p.parts or ':' in member or '\\' in member:
        raise ValueError('Unsafe manifest member')
    path = (root/Path(*p.parts)).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Manifest member outside source')
    return path


def usable_boxes(image, annotations, ball_id):
    if not image.get('is_labeled') or image.get('ignore_regions_x') or image.get('ignore_regions_y'):
        return [], 'unknown_or_ignore'
    boxes = []
    for a in annotations:
        if a.get('category_id') != ball_id:
            continue
        b = a['bbox_image']; x, y, w, h = (b[k] for k in ('x', 'y', 'w', 'h'))
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x,y,w,h)):
            return [], 'invalid_box'
        if w <= 0 or h <= 0 or x < 0 or y < 0 or x+w > image['width'] or y+h > image['height']:
            return [], 'invalid_box'
        boxes.append([x,y,w,h])
    return (boxes, 'included') if boxes else ([], 'unknown_ball')


def export(gallery_path, plan_path, out):
    plan = json.loads(Path(plan_path).read_text()); gallery = json.loads(Path(gallery_path).read_text())
    if plan['provided_fixture_used'] or plan['dataset'] != 'SoccerNet/SN-GSR-2024' or plan['archive'] != 'train.zip':
        raise ValueError('External training plan required')
    lookup = {}
    for split, games in plan['splits'].items():
        if split not in ('train', 'valid', 'test'):
            raise ValueError('Unknown split')
        for game in games:
            if game in lookup:
                raise ValueError('Game split overlap')
            lookup[game] = split
    if set(lookup) != {str(c['source_game_id']) for c in gallery['clips']}:
        raise ValueError('Gallery differs from registered games')
    out = external_output(out); out.mkdir(parents=True, exist_ok=False)
    write(out/'before-access.json', {'plan': plan, 'plan_sha256': sha256(plan_path),
        'gallery_sha256': sha256(gallery_path), 'source_sha256': sha256(__file__)})
    datasets = {s: {'images': [], 'annotations': [], 'categories': [
        {'id': 1, 'name': 'ball', 'supercategory': 'object'}],
        'info': {'description': 'External research ball annotations; not competition data'}} for s in plan['splits']}
    counts = Counter(); receipts = []; seen_hashes = {}
    for clip in gallery['clips']:
        split = lookup[str(clip['source_game_id'])]; source = Path(clip['study'])/'sample-v2'
        registered = json.loads((source/'before-access.json').read_text())['plan']
        if any(registered[k] != plan[k] for k in ('dataset', 'archive', 'provided_fixture_used')):
            raise ValueError('Source registration differs')
        manifest = json.loads((source/'manifest.json').read_text())
        if not manifest['complete']:
            raise ValueError('Incomplete acquisition')
        specs = manifest['acquired_files']
        label = next(s for s in specs if s['member'].endswith('Labels-GameState.json'))
        path = safe_member(source/'sample', label['member'])
        if sha256(path) != label['sha256']:
            raise ValueError('Changed label file')
        labels = json.loads(path.read_text())
        ball = next(c['id'] for c in labels['categories'] if c['name'] == 'ball')
        images = {i['file_name']: i for i in labels['images']}; anns = defaultdict(list)
        for a in labels['annotations']:
            anns[a['image_id']].append(a)
        for spec in specs:
            if not spec['member'].lower().endswith('.jpg'):
                continue
            path = safe_member(source/'sample', spec['member'])
            if sha256(path) != spec['sha256']:
                raise ValueError('Changed image file')
            image = images[path.name]; boxes, reason = usable_boxes(image, anns[image['image_id']], ball)
            counts[split+'/'+reason] += 1
            if not boxes:
                continue
            if spec['sha256'] in seen_hashes:
                raise ValueError('Duplicate image content across exported samples')
            seen_hashes[spec['sha256']] = split
            destination = out/split/(clip['id']+'_'+path.name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            if sha256(destination) != spec['sha256']:
                raise ValueError('Copy changed image bytes')
            data = datasets[split]; image_id = len(data['images'])+1
            data['images'].append({'id': image_id, 'file_name': destination.name,
                                   'width': image['width'], 'height': image['height']})
            for b in boxes:
                data['annotations'].append({'id': len(data['annotations'])+1, 'image_id': image_id,
                    'category_id': 1, 'bbox': b, 'area': b[2]*b[3], 'iscrowd': 0})
            receipts.append({'split': split, 'game': str(clip['source_game_id']), 'clip': clip['id'],
                             'file': str(destination.relative_to(out)).replace('\\','/'),
                             'sha256': spec['sha256'], 'reference_sha256': label['sha256']})
    annotation_hashes = {}
    for split, data in datasets.items():
        if not data['images']:
            raise ValueError('Empty split')
        path = out/split/'_annotations.coco.json'; write(path, data)
        annotation_hashes[split] = sha256(path)
    report = {'version': plan['version'], 'provided_fixture_used': False,
        'splits': {s: {'games': plan['splits'][s], 'images': len(d['images']),
                      'ball_boxes': len(d['annotations'])} for s, d in datasets.items()},
        'counts': dict(counts), 'annotation_sha256': annotation_hashes,
        'images': receipts, 'redistribute_raw_data': False, 'independent_test': False}
    write(out/'manifest.json', report)
    print(json.dumps({'splits': report['splits'], 'counts': report['counts']}))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('gallery', 'out'):
        p.add_argument('--'+k, required=True)
    p.add_argument('--plan', default='ball-detector-training-plan.json')
    a = p.parse_args(); export(a.gallery, a.plan, a.out)
