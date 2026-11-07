"""Fit/select dead-ball evidence exclusively on registered external fixtures."""
import argparse
from dataclasses import asdict
import itertools
import json
from pathlib import Path
import time
import numpy as np
from development import learned_dead_ball as dead
from development.sequence_possession import SequenceConfig, predict as team_predict
from development.state_metrics import evaluate
from tools.dead_ball_audit import _frozen_model
from tools.metrica_data import external_output, sha256
from tools.sequence_selection import write


def load(root, mid, registry):
    folder = root/mid
    report = json.loads((folder/'report.json').read_text())
    expected = next(e['sha256'] for e in registry['files'] if e['fixture_id']==mid and e['sha256'])
    if report['provided_fixture_used'] or report['raw_sha256']['tracking'] != expected:
        raise ValueError('Pinned external fixture required')
    for name,key in [('inputs.npz','inputs_sha256'),('targets.npz','targets_sha256')]:
        if sha256(folder/name)!=report[key]: raise ValueError('Prepared data integrity mismatch')
    with np.load(folder/'inputs.npz',allow_pickle=False) as z: x={k:z[k] for k in z.files}
    with np.load(folder/'targets.npz',allow_pickle=False) as z: y=z['labels']
    return x,y,report


def binary_metrics(y,state):
    known=np.isin(y,('H','A','D')); result={}
    for name, truth, predicted in [('dead',y=='D',state=='D'),('live',np.isin(y,('H','A')),state=='L')]:
        tp=int(np.sum(known & truth & predicted)); fp=int(np.sum(known & ~truth & predicted)); fn=int(np.sum(known & truth & ~predicted))
        result[name]={'precision':tp/max(1,tp+fp),'recall':tp/max(1,tp+fn),'f1':2*tp/max(1,2*tp+fp+fn)}
    result['macro_f1']=.5*(result['dead']['f1']+result['live']['f1'])
    return result


def combine(x,state,cfg):
    reset={**x,'period':np.where(state=='D',0,x['period'])}
    result=team_predict(reset,cfg)
    result[state=='D']='D'
    return result


def run(prepared, plan_path, out):
    repo=Path(__file__).resolve().parents[1]; prepared=Path(prepared)
    plan=json.loads(Path(plan_path).read_text()); registry=json.loads((repo/plan['data_plan']).read_text())
    if plan['provided_fixture_used'] or plan['test_access_allowed']: raise ValueError('External development study only')
    for split in ('train','validation'):
        expected={e['fixture_id'] for e in registry['files'] if e['split']==split}
        if set(plan[split])!=expected: raise ValueError('Registered fixture split required')
    baseline_hash=_frozen_model(repo)
    selected=json.loads((repo/'sequence-external-results.json').read_text())['study']
    if any(sha256(repo/p)!=h for p,h in selected['source_hashes'].items()): raise ValueError('Fixed team model changed')
    team_cfg=SequenceConfig(**selected['selected_config'])
    paths=['tools/dead_ball_selection.py','development/learned_dead_ball.py','development/state_metrics.py',
           'development/sequence_possession.py','development/dead_ball_features.py','development/continuity.py','tools/sportec_prepare.py']
    hashes={p:sha256(repo/p) for p in paths}
    out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    before={'version':plan['version'],'plan':plan,'plan_sha256':sha256(plan_path),
            'data_plan_sha256':sha256(repo/plan['data_plan']),'source_hashes':hashes,
            'baseline_model_sha256':baseline_hash,'team_config':asdict(team_cfg),
            'provided_fixture_used':False,'reserved_test_used':False}
    write(out/'before-access.json',before)
    raw_rows=[];labels=[];weights=[];records={};start=time.perf_counter()
    for number,mid in enumerate(plan['train']):
        x,y,record=load(prepared,mid,registry);records[mid]=record
        for mode in ('clean','dropout'):
            v=x if mode=='clean' else dead.corrupt(x,731+number)
            raw,usable=dead.features(v)
            select=usable & np.isin(y,('H','A','D')) & (np.arange(len(y))%5==0)
            if not select.any(): raise ValueError('No usable training rows')
            raw_rows.append(raw[select]);labels.append((y[select]=='D').astype(float))
            weights.append(np.full(np.sum(select),1/np.sum(select)))
        print(json.dumps({'external_training_features':mid}),flush=True)
    raw=np.vstack(raw_rows);target=np.concatenate(labels);weight=np.concatenate(weights)
    models=[]
    for l2 in plan['l2']:
        model=dead.fit(raw,target,weight,l2);models.append(model)
        print(json.dumps({'fit_l2':l2,'iterations':model['iterations']}),flush=True)
    del raw_rows,raw,labels,weights,target,weight
    write(out/'model-candidates.json',{'models':models,'before_validation':True,'training_sources':records})
    validation=[]
    for number,mid in enumerate(plan['validation']):
        x,y,record=load(prepared,mid,registry);records[mid]=record
        for mode in ('clean','dropout','stress'):
            v=x if mode=='clean' else dead.corrupt(x,(917 if mode=='dropout' else 1123)+number,ball_fraction=.2 if mode=='dropout' else .5)
            raw,usable=dead.features(v)
            probabilities=[dead.probability(raw,m) for m in models]
            validation.append({'id':mid,'mode':mode,'x':v,'y':y,'usable':usable,'p':probabilities,
                               'baseline':evaluate(y,team_predict(v,team_cfg),v['period'])})
        print(json.dumps({'external_validation_features':mid}),flush=True)
    results=[]
    for model_id,threshold,cost in itertools.product(range(len(models)),plan['dead_probability_thresholds'],plan['switch_cost_seconds']):
        games=[]
        for entry in validation:
            if entry['mode']=='stress': continue  # held for descriptive post-selection stress only
            x,y=entry['x'],entry['y']
            state=dead.classify(entry['p'][model_id],entry['usable'],x,threshold,cost)
            games.append({'id':entry['id'],'mode':entry['mode'],'binary':binary_metrics(y,state),
                          'boundary':dead.boundary_score(y,state,x['period'],float(x['fps'])),
                          'combined':evaluate(y,combine(x,state,team_cfg),x['period']),
                          'without_D':entry['baseline']})
        result={'model_id':model_id,'threshold':threshold,'switch_cost_s':cost,'games':games,
                'mean_binary_macro_f1':float(np.mean([g['binary']['macro_f1'] for g in games])),
                'mean_boundary_f1':float(np.mean([g['boundary']['f1'] for g in games])),
                'mean_combined_spell_f1':float(np.mean([g['combined']['external_spell_f1'] for g in games]))}
        results.append(result)
        if len(results)%8==0:print(json.dumps({'D_candidates':len(results),'seconds':round(time.perf_counter()-start,1)}),flush=True)
    results.sort(key=lambda r:(-r['mean_binary_macro_f1'],-r['mean_boundary_f1'],-r['mean_combined_spell_f1'],r['model_id'],r['threshold'],r['switch_cost_s']))
    write(out/'validation-results.json',{'candidates':results})
    best=results[0]
    clean=[g for g in best['games'] if g['mode']=='clean']; noisy=[g for g in best['games'] if g['mode']=='dropout']
    accepted=(all(g['binary']['dead']['precision']>=.8 and g['binary']['dead']['recall']>=.7 for g in clean)
              and np.mean([g['binary']['dead']['f1'] for g in noisy])>=.65
              and np.mean([g['combined']['external_spell_f1'] for g in clean])>np.mean([g['without_D']['external_spell_f1'] for g in clean]))
    # Freeze selection before scoring the registered, more severe dropout.
    freeze={**before,'model':models[best['model_id']],'threshold':best['threshold'],
            'switch_cost_s':best['switch_cost_s'],'accepted_external_candidate':bool(accepted),
            'candidate_count':len(results),'selected_validation':best,'prepared_sources':records,
            'combined_release_selected':False,'video_validated':False,'competition_score':False}
    write(out/'candidate-freeze.json',freeze)
    stress=[]
    for entry in validation:
        if entry['mode']!='stress': continue
        x,y=entry['x'],entry['y']
        state=dead.classify(entry['p'][best['model_id']],entry['usable'],x,best['threshold'],best['switch_cost_s'])
        stress.append({'id':entry['id'],'binary':binary_metrics(y,state),
                       'boundary':dead.boundary_score(y,state,x['period'],float(x['fps'])),
                       'combined':evaluate(y,combine(x,state,team_cfg),x['period'])})
    if _frozen_model(repo)!=baseline_hash or any(sha256(repo/p)!=h for p,h in hashes.items()): raise ValueError('Sources changed during experiment')
    report={'version':plan['version'],'accepted_external_candidate':bool(accepted),'selected_validation':best,
            'post_selection_stress':stress,'source_hashes':hashes,'freeze_sha256':sha256(out/'candidate-freeze.json'),
            'provided_fixture_used':False,'reserved_test_used':False,'human_ground_truth':False,
            'combined_release_selected':False,'video_validated':False,'competition_score':False,
            'elapsed_seconds':time.perf_counter()-start}
    write(out/'report.json',report)
    print(json.dumps(report),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepared',required=True)
    p.add_argument('--plan',default='dead-ball-selection-plan.json');p.add_argument('--out',required=True)
    a=p.parse_args();run(a.prepared,a.plan,a.out)
