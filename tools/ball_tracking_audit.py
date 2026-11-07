"""Post-freeze descriptive ball association audit on the registered GSR training gallery."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from development.vision_box_audit import match_boxes
from .metrica_data import external_output, sha256


def run(gallery, analysis, out):
    gallery, analysis, out = Path(gallery), Path(analysis), external_output(out)
    clips = json.loads(gallery.read_text())['clips']
    paths = [analysis / c['id'] / mode / 'frames.jsonl' for c in clips for mode in ('native','sliced')]
    frozen = {str(p): sha256(p) for p in paths}
    out.mkdir(parents=True, exist_ok=False)
    (out / 'before-evaluation.json').write_text(json.dumps({'predictions_sha256': frozen,
        'source_sha256': sha256(__file__), 'iou_threshold': .5, 'independent_test': False,
        'purpose': 'descriptive_previously_exposed_training_clip_association_audit'}, indent=2))
    reports = []
    for clip in clips:
        study = Path(clip['study']);sample = study / 'sample-v2'
        before = json.loads((sample / 'before-access.json').read_text())['plan']
        if before['dataset'] != 'SoccerNet/SN-GSR-2024' or before['archive'] != 'train.zip' or before['provided_fixture_used'] is not False:
            raise ValueError('Registered public training reference only')
        manifest = json.loads((sample / 'manifest.json').read_text())
        label_spec = next(r for r in manifest['acquired_files'] if r['member'].endswith('Labels-GameState.json'))
        label_path = sample / 'sample' / label_spec['member']
        if sha256(label_path) != label_spec['sha256']: raise ValueError('Reference changed')
        labels = json.loads(label_path.read_text());ball_id = next(r['id'] for r in labels['categories'] if r['name']=='ball')
        images = {r['file_name']: r['image_id'] for r in labels['images']};targets = defaultdict(list)
        for row in labels['annotations']:
            if row.get('category_id') == ball_id:
                b = row['bbox_image']
                targets[row['image_id']].append({'box_xyxy':[b['x'],b['y'],b['x']+b['w'],b['y']+b['h']], 'track_id':row['track_id']})
        mapping = json.loads((study / 'video-v1/video-manifest.json').read_text())['frames']
        for mode in ('native','sliced'):
            path = analysis / clip['id'] / mode / 'frames.jsonl'
            packets = [json.loads(line) for line in path.read_text().splitlines()]
            if len(packets) != len(mapping): raise ValueError('Frame mapping differs')
            counts, previous, fragments = Counter(), {}, 0
            for packet, source in zip(packets, mapping):
                if packet['source_frame'] != source['source_frame']: raise ValueError('Source frame differs')
                refs = targets[images[Path(source['member']).name]]
                raw = {r['detection_id']:r for r in packet['objects'] if r['kind']=='ball_candidate'}
                observed, identities, states = [], [], []
                for track in packet['ball_tracking']['tracks']:
                    if track['measurement']:
                        row = raw[track['detection_id']]
                        if row['image_xy_px'] != track['measured_position_px'] or track['predicted_position_px'] is not None:
                            raise ValueError('Measured/predicted coordinates conflated')
                        observed.append({'box_xyxy':row['box_xyxy_px'],'confidence':row['confidence']})
                        identities.append(track['track_id']);states.append(track['state'])
                    else:
                        if track['detection_id'] is not None or track['measured_position_px'] is not None:
                            raise ValueError('Estimated state fabricated a detection')
                        if track['state']=='predicted':
                            counts['forecast_observations'] += 1
                            p=track['predicted_position_px']
                            if refs:
                                counts['forecasts_with_reference'] += 1
                                counts['forecast_centres_inside_reference_box'] += any(
                                    b['box_xyxy'][0]<=p[0]<=b['box_xyxy'][2] and b['box_xyxy'][1]<=p[1]<=b['box_xyxy'][3] for b in refs)
                result = match_boxes(observed, refs, .5);now = {}
                counts['reference_ball_boxes'] += len(refs);counts['associated_measured_boxes'] += len(observed)
                counts['matched_reference_boxes'] += len(result['matches'])
                counts['unmatched_associated_boxes'] += result['unmatched_predictions']
                for pair in result['matches']:
                    identity=identities[pair['prediction']];target=refs[pair['reference']]['track_id'];now[target]=identity
                    counts['confirmed_matched_reference_boxes'] += states[pair['prediction']]=='observed'
                    if target not in previous or previous[target]!=identity: fragments+=1
                    if target in previous and previous[target]!=identity: counts['adjacent_matched_id_changes']+=1
                previous=now
            reports.append({'clip':clip['id'],'mode':mode,'frames':len(packets),
                            'counts':dict(counts),'matched_contiguous_id_fragments':fragments})
    if any(sha256(p)!=digest for p,digest in frozen.items()): raise ValueError('Predictions changed during audit')
    result={'runs':reports,'independent_test':False,'official_metric':False,'selected_release':False,
        'limitations':'Training-only short clips; reference-box coverage is not in-play ball selection, physical accuracy or HOTA. Forecasts scored separately from measured boxes.'}
    (out/'report.json').write_text(json.dumps(result,indent=2))
    print('Temporal association audit complete: '+str(len(reports))+' registered training runs.')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('gallery','analysis','out'):parser.add_argument('--'+key,required=True)
    args=parser.parse_args();run(args.gallery,args.analysis,args.out)
