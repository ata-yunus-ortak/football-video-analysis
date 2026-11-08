"""External-only bounded-lookahead ball confirmation selection."""
import argparse
from collections import defaultdict
from dataclasses import replace,asdict
from itertools import product
import json
from pathlib import Path
from development.ball_tracking import BallTrackingConfig
from development.confirmed_ball_filter import filter_packets
from development.vision_box_audit import match_boxes
from tools.ball_candidate_selection import write,passes,rank
from tools.ball_detector_data import usable_boxes,safe_member
from tools.metrica_data import external_output,sha256


def load_inputs(clips,analysis,modes):
    runs=[]
    for clip in clips:
        study=Path(clip['study']);sample=study/'sample-v2'
        plan=json.loads((sample/'before-access.json').read_text())['plan']
        if plan['provided_fixture_used'] or plan['dataset']!='SoccerNet/SN-GSR-2024' or plan['archive']!='train.zip':
            raise ValueError('Registered external inputs required')
        mapping=json.loads((study/'video-v1/video-manifest.json').read_text())
        if not mapping['rgb_lossless_verified'] or mapping['sample_manifest_sha256']!=sha256(sample/'manifest.json'):
            raise ValueError('Unverified native mapping')
        native=[int(Path(r['member']).stem) for r in mapping['frames']]
        if any(b!=a+1 for a,b in zip(native,native[1:])):raise ValueError('Sparse frames cannot establish temporal confirmation')
        for mode in modes:
            path=analysis/clip['id']/mode/'frames.jsonl'
            packets=[json.loads(s) for s in path.read_text().splitlines()]
            if len(packets)!=len(native):raise ValueError('Frame count differs')
            for i,p in enumerate(packets):
                if (p['source_frame']!=mapping['frames'][i]['source_frame'] or p['fps']!=mapping['fps']
                    or p['image_size_px']!=[mapping['width'],mapping['height']]
                    or p['source_id'].split(':')[0]!=mapping['video_sha256']):raise ValueError('Native correspondence differs')
            runs.append({'clip':clip['id'],'game':str(clip['source_game_id']),'mode':mode,
                         'study':str(study),'packets':packets,'mapping':mapping['frames']})
    return runs


def references(run):
    sample=Path(run['study'])/'sample-v2'
    manifest=json.loads((sample/'manifest.json').read_text())
    spec=next(r for r in manifest['acquired_files'] if r['member'].endswith('Labels-GameState.json'))
    path=safe_member(sample/'sample',spec['member'])
    if sha256(path)!=spec['sha256']:raise ValueError('Reference changed')
    labels=json.loads(path.read_text());ball=next(c['id'] for c in labels['categories'] if c['name']=='ball')
    images={r['file_name']:r for r in labels['images']};annotations=defaultdict(list)
    for a in labels['annotations']:annotations[a['image_id']].append(a)
    refs=[]
    for item in run['mapping']:
        image=images[Path(item['member']).name]
        boxes,reason=usable_boxes(image,annotations[image['image_id']],ball)
        refs.append([{'box_xyxy':[x,y,x+w,y+h]} for x,y,w,h in boxes] if reason=='included' else None)
    return refs


def score(runs,predictions,targets):
    totals={}
    for run,rows,refs in zip(runs,predictions,targets):
        s=totals.setdefault(run['mode'],{'matched':0,'predicted':0,'reference':0,'evaluated_frames':0,'unknown_frames':0})
        for objects,ref in zip(rows,refs):
            if ref is None:s['unknown_frames']+=1;continue
            boxes=[{'box_xyxy':r['box_xyxy_px'],'confidence':r['confidence']} for r in objects]
            m=match_boxes(boxes,ref,.5)
            s['matched']+=len(m['matches']);s['predicted']+=len(boxes);s['reference']+=len(ref);s['evaluated_frames']+=1
    for s in totals.values():
        s['unmatched_predictions']=s['predicted']-s['matched']
        s['precision']=s['matched']/s['predicted'] if s['predicted'] else 0
        s['recall']=s['matched']/s['reference'] if s['reference'] else 0
    return totals


def run(gallery,analysis,plan_path,out):
    plan=json.loads(Path(plan_path).read_text());clips=json.loads(Path(gallery).read_text())['clips']
    groups=[set(plan[k]) for k in ('train_games','validation_games','recheck_games')]
    if plan['provided_fixture_used'] or any(groups[i]&groups[j] for i in range(3) for j in range(i)):
        raise ValueError('External disjoint game split required')
    if {str(c['source_game_id']) for c in clips}!=set.union(*groups):raise ValueError('Unexpected games')
    repo=Path(__file__).resolve().parents[1];analysis=Path(analysis);out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    sources=['tools/ball_temporal_selection.py','development/confirmed_ball_filter.py','development/ball_tracking.py',
             'development/vision_box_audit.py','tools/ball_detector_data.py','tools/ball_candidate_selection.py']
    hashes={p:sha256(repo/p) for p in sources}
    inputs={str(analysis/c['id']/m/'frames.jsonl'):sha256(analysis/c['id']/m/'frames.jsonl') for c in clips for m in plan['modes']}
    base_path=repo/plan['base_plan'];base=BallTrackingConfig(**json.loads(base_path.read_text())['parameters'])
    configs=[replace(base,confirmation_observations=n,match_radius_diagonal=r,ambiguity_margin=a)
             for n,r,a in product(plan['confirmation_observations'],plan['match_radius_diagonal'],plan['ambiguity_margin'])]
    write(out/'before-access.json',{'plan':plan,'source_hashes':hashes,'input_hashes':inputs,
        'base_plan_sha256':sha256(base_path),'plan_sha256':sha256(plan_path),'gallery_sha256':sha256(gallery)})
    selected=None;result={}
    for split,games in [('validation',groups[1]),('recheck',groups[2])]:
        runs=load_inputs([c for c in clips if str(c['source_game_id']) in games],analysis,plan['modes'])
        candidates=configs if split=='validation' else [configs[selected]]
        predictions=[[filter_packets(r['packets'],c) for r in runs] for c in candidates]
        raw=[[[o for o in p['objects'] if o['kind']=='ball_candidate'] for p in r['packets']] for r in runs]
        path=out/(split+'-predictions.json');write(path,predictions)
        write(out/(split+'-freeze.json'),{'prediction_sha256':sha256(path),'before_reference_access':True})
        targets=[references(r) for r in runs]
        baseline=score(runs,raw,targets);scores=[score(runs,p,targets) for p in predictions]
        if split=='validation':
            eligible=[i for i,s in enumerate(scores) if passes(s,baseline)]
            selected=max(eligible,key=lambda i:rank(scores[i])) if eligible else None
            write(out/'candidate-freeze.json',{'selected_index':selected,'parameters':asdict(configs[selected]) if selected is not None else None,
                'eligible':eligible,'scores':scores,'baseline':baseline,'before_recheck':True})
            result[split]={'baseline':baseline,'selected':scores[selected] if selected is not None else None,'eligible_candidates':len(eligible)}
            if selected is None:break
        else:result[split]={'baseline':baseline,'selected':scores[0],'accepted':passes(scores[0],baseline)}
    if any(sha256(repo/p)!=h for p,h in hashes.items()) or any(sha256(p)!=h for p,h in inputs.items()):raise ValueError('Frozen source/input changed')
    report={'version':plan['version'],'results':result,'parameters':asdict(configs[selected]) if selected is not None else None,
        'accepted_for_extended_validation':selected is not None and result['recheck']['accepted'],
        'provided_fixture_used':False,'selected_release':False,'independent_test':False,'possession_validated':False,
        'candidate_freeze_sha256':sha256(out/'candidate-freeze.json'),'source_hashes':hashes,'limits':plan['limits']}
    write(out/'report.json',report);print(json.dumps(report,indent=2));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('gallery','analysis','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='ball-temporal-selection-plan.json')
    a=p.parse_args();run(a.gallery,a.analysis,a.plan,a.out)
