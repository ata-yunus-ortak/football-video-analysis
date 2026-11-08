"""Fit external geometry and temporal evidence without discarding all singletons."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import numpy as np
from development.ball_tracking import BallTrackingConfig
from development import temporal_ball_features as model
from development.vision_box_audit import iou
from tools.ball_temporal_selection import load_inputs,references,score
from tools.ball_candidate_selection import write,passes,rank
from tools.metrica_data import external_output,sha256


def predict(runs,features,candidate):
    result=[]
    width=len(candidate['model']['feature_names'])
    for run,arrays in zip(runs,features):
        rows=[]
        for packet,raw in zip(run['packets'],arrays):
            balls=[r for r in packet['objects'] if r['kind']=='ball_candidate']
            probabilities=model.probability(raw[:,:width],candidate['model'])
            rows.append([r for r,p in zip(balls,probabilities) if p>=candidate['threshold']])
        result.append(rows)
    return result


def run(gallery,analysis,plan_path,out):
    plan=json.loads(Path(plan_path).read_text());clips=json.loads(Path(gallery).read_text())['clips']
    groups=[set(plan[k]) for k in ('train_games','validation_games','recheck_games')]
    if plan['provided_fixture_used'] or any(groups[i]&groups[j] for i in range(3) for j in range(i)):
        raise ValueError('Disjoint external games required')
    if {str(c['source_game_id']) for c in clips}!=set.union(*groups):raise ValueError('Unexpected games')
    repo=Path(__file__).resolve().parents[1];analysis=Path(analysis);out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    sources=['tools/ball_temporal_learned.py','development/temporal_ball_features.py','development/confirmed_ball_filter.py',
        'development/ball_tracking.py','development/ball_candidate_filter.py','development/learned_dead_ball.py',
        'tools/ball_temporal_selection.py','tools/ball_candidate_selection.py','tools/ball_detector_data.py','development/vision_box_audit.py']
    hashes={p:sha256(repo/p) for p in sources}
    inputs={str(analysis/c['id']/m/'frames.jsonl'):sha256(analysis/c['id']/m/'frames.jsonl') for c in clips for m in plan['modes']}
    base_path=repo/plan['base_plan'];base=BallTrackingConfig(**json.loads(base_path.read_text())['parameters'])
    write(out/'before-access.json',{'plan':plan,'plan_sha256':sha256(plan_path),'source_hashes':hashes,
        'input_hashes':inputs,'base_parameters':asdict(base),'gallery_sha256':sha256(gallery)})
    def load(games,split):
        runs=load_inputs([c for c in clips if str(c['source_game_id']) in games],analysis,plan['modes'])
        features=[model.extract(r['packets'],base) for r in runs]
        # Preserve NaNs in local numeric feature arrays, not JSON.
        path=out/(split+'-features.npz')
        np.savez(path,**{str(i):np.vstack(f) for i,f in enumerate(features)})
        write(out/(split+'-feature-freeze.json'),{'features_sha256':sha256(path),'before_reference_access':True})
        return runs,features
    runs,features=load(groups[0],'train');refs=[references(r) for r in runs]
    rows=[];targets=[];group_ids=[]
    for k,(r,arrays,rr) in enumerate(zip(runs,features,refs)):
        for packet,array,target in zip(r['packets'],arrays,rr):
            if target is None:continue
            balls=[o for o in packet['objects'] if o['kind']=='ball_candidate']
            for b,raw in zip(balls,array):
                overlap=max(iou(b['box_xyxy_px'],t['box_xyxy']) for t in target)
                if overlap>=.5 or overlap<=.1:
                    rows.append(raw);targets.append(int(overlap>=.5));group_ids.append(k)
    counts=Counter(group_ids);weights=np.array([1/counts[k] for k in group_ids]);raw=np.asarray(rows);targets=np.asarray(targets)
    candidates=[]
    for temporal in (False,True):
        for l2 in plan['l2']:
            learned=model.fit(raw if temporal else raw[:,:5],targets,weights,l2,temporal)
            candidates.extend({'model':learned,'threshold':t,'temporal':temporal} for t in plan['thresholds'])
    write(out/'trained-models.json',{'candidates':candidates,'training_rows':len(raw),'training_positives':int(targets.sum())})
    results={};selected=None
    for split,games in [('validation',groups[1]),('recheck',groups[2])]:
        runs,features=load(games,split);choices=candidates if split=='validation' else [candidates[selected]]
        predictions=[predict(runs,features,c) for c in choices]
        path=out/(split+'-predictions.json');write(path,predictions)
        write(out/(split+'-freeze.json'),{'predictions_sha256':sha256(path),'before_reference_access':True})
        refs=[references(r) for r in runs]
        baseline=score(runs,[[[o for o in p['objects'] if o['kind']=='ball_candidate'] for p in r['packets']] for r in runs],refs)
        scores=[score(runs,p,refs) for p in predictions]
        if split=='validation':
            eligible=[i for i,s in enumerate(scores) if candidates[i]['temporal'] and passes(s,baseline)]
            selected=max(eligible,key=lambda i:rank(scores[i])) if eligible else None
            ablation=max((i for i,c in enumerate(candidates) if not c['temporal']),key=lambda i:rank(scores[i]))
            write(out/'candidate-freeze.json',{'selected':candidates[selected] if selected is not None else None,
                'selected_index':selected,'eligible':eligible,'scores':scores,'baseline':baseline,'before_recheck':True})
            results[split]={'baseline':baseline,'selected':scores[selected] if selected is not None else None,
                'eligible_candidates':len(eligible),'best_geometry_only_by_f1':scores[ablation]}
            if selected is None:break
        else:results[split]={'baseline':baseline,'selected':scores[0],'accepted':passes(scores[0],baseline)}
    if any(sha256(repo/p)!=h for p,h in hashes.items()) or any(sha256(p)!=h for p,h in inputs.items()):raise ValueError('Study changed')
    report={'version':plan['version'],'results':results,'accepted_for_extended_validation':selected is not None and results['recheck']['accepted'],
        'provided_fixture_used':False,'selected_release':False,'independent_test':False,'possession_validated':False,
        'training_rows':len(raw),'training_positives':int(targets.sum()),'source_hashes':hashes,
        'candidate_freeze_sha256':sha256(out/'candidate-freeze.json'),'limits':plan['limits']}
    write(out/'report.json',report);print(json.dumps(report,indent=2));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('gallery','analysis','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='ball-temporal-learned-plan.json')
    a=p.parse_args();run(a.gallery,a.analysis,a.plan,a.out)
