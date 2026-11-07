"""Frozen player-only D check on partial external Metrica event proxies.

No X-to-D conversion, no exhaustive D truth claim, no timing-boundary score
on partial masks, and no model selection or parameter changes in this tool.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from development import player_dead_ball as dead
from development.metrica import load_events
from tools.metrica_data import external_output,sha256,verify_file,validate_plan
from tools.sequence_selection import write
from tools.dead_ball_selection import binary_metrics


def partial_targets(inputs,intervals,events):
    n=len(inputs['frame']);source=inputs['source_frame'];period=inputs['period']
    d=np.zeros(n,bool);live=np.zeros(n,bool)
    for interval in intervals:
        d[interval['start_index']:interval['stop_index_exclusive']]=True
    for event in events:
        if event['type']!='PASS' or event['end']<event['start']:continue
        a=np.searchsorted(source,event['start']);b=np.searchsorted(source,event['end'],side='right')
        if (a>=b or b>n or source[a]!=event['start'] or source[b-1]!=event['end']
                or not np.all(period[a:b]==event['period'])):continue
        live[a:b]=True
    y=np.full(n,'X',dtype='<U1');y[live & ~d]='H';y[d & ~live]='D'
    return y,{'partial_dead_frames':int(np.sum(y=='D')),'partial_pass_live_frames':int(np.sum(y=='H')),
              'conflicting_frames_withheld':int(np.sum(live & d)),'unknown_frames':int(np.sum(y=='X'))}


def run(candidate_path,audit_dir,data_dir,out):
    repo=Path(__file__).resolve().parents[1];audit_dir=Path(audit_dir);data_dir=Path(data_dir)
    candidate=json.loads(Path(candidate_path).read_text())
    if candidate['provided_fixture_used'] or candidate['model'].get('model_family')!='player-only-dead-live-v1':
        raise ValueError('Frozen external player-only model required')
    if any(sha256(repo/p)!=h for p,h in candidate['source_hashes'].items()):raise ValueError('Candidate source freeze mismatch')
    plan=json.loads((data_dir/'plan.json').read_text());validate_plan(plan)
    audit=json.loads((audit_dir/'report.json').read_text())
    if audit['provided_fixture_used']:raise ValueError('External audit only')
    out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    before={'candidate_sha256':sha256(candidate_path),'audit_report_sha256':sha256(audit_dir/'report.json'),
            'source_sha256':sha256(__file__),'provided_fixture_used':False,'model_selection':False,
            'target_kind':'partial_event_paired_dead_and_pass_interval_live_proxy','exhaustive_truth':False,
            'independent_new_test':False,'before_predictions':True}
    write(out/'before-access.json',before);frozen={};inputs={}
    for fixture in audit['fixtures']:
        mid=fixture['id'];path=audit_dir/mid/'inputs.npz'
        if sha256(path)!=fixture['prepared_sha256']['inputs.npz']:raise ValueError('External measurements changed')
        with np.load(path,allow_pickle=False) as z:x={k:z[k] for k in z.files}
        inputs[mid]=x
        feature_input=dict(x);feature_input.pop('source_frame')
        raw,usable=dead.features(feature_input)
        p=dead.probability(raw,candidate['model'])
        state=dead.classify(p,usable,feature_input,candidate['threshold'],candidate['switch_cost_s'])
        dest=out/(mid+'.npy');np.save(dest,state,allow_pickle=False);frozen[mid]=sha256(dest)
    write(out/'prediction-freeze.json',{'predictions':frozen,'before_event_target_scoring':True})
    results=[]
    for fixture in audit['fixtures']:
        mid=fixture['id'];path=audit_dir/mid/'candidate-stoppages.json'
        if sha256(path)!=fixture['prepared_sha256']['candidate-stoppages.json']:raise ValueError('Proxy intervals changed')
        intervals=json.loads(path.read_text())['intervals']
        spec=next(f for f in plan['fixtures'] if f['id']==mid)['files']['events']
        event_path=data_dir/'raw'/mid/'events.csv';verify_file(event_path,spec)
        y,coverage=partial_targets(inputs[mid],intervals,load_events(event_path))
        dest=out/(mid+'.npy')
        if sha256(dest)!=frozen[mid]:raise ValueError('Predictions changed before scoring')
        state=np.load(dest,allow_pickle=False)
        results.append({'fixture':mid,'coverage':coverage,'binary_partial_proxy':binary_metrics(y,state)})
    if sha256(candidate_path)!=before['candidate_sha256']:raise ValueError('Candidate changed')
    report={**before,'results':results,'model_changed':False,
            'limitation':'Pass-only live negatives are not representative of all live play; paired stoppages have uncertain boundary semantics. This cannot certify full D precision or timing.'}
    write(out/'report.json',report);print(json.dumps(report),flush=True);return report


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('candidate','audit','data','out'):p.add_argument('--'+k,required=True)
    a=p.parse_args();run(a.candidate,a.audit,a.data,a.out)
