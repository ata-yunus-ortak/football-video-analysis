"""Boundary-aware external sequence comparison; no supplied match inputs."""
import argparse
from dataclasses import replace,asdict
import json
from pathlib import Path
import numpy as np
from development.sequence_possession import SequenceConfig,measurements,evidence,decode
from development.sequence_metrics import evaluate as spell_metrics
from development.possession_boundaries import evaluate,timeline
from tools.ball_candidate_selection import write
from tools.metrica_data import external_output,sha256
from tools.dead_ball_audit import _frozen_model


def mean_scores(games):
    values=[g['boundaries']['tolerances_s']['0.5']['f1'] for g in games]
    return {'boundary_f1_05':float(np.mean(values)) if all(v is not None for v in values) else None,
        'spell_f1':float(np.mean([g['spells']['provider_filled_spell_f1'] for g in games])),
        'macro_f1':float(np.mean([g['spells']['provider_macro_f1_HA'] for g in games]))}


def passes(s,b):
    return (s['boundary_f1_05'] is not None and b['boundary_f1_05'] is not None
            and s['boundary_f1_05']>=b['boundary_f1_05']+.03
            and s['spell_f1']>=.99*b['spell_f1'] and s['macro_f1']>=b['macro_f1']-.005)


def run(study,recheck,plan_path,out):
    repo=Path(__file__).resolve().parents[1];study=Path(study);recheck=Path(recheck)
    plan=json.loads(Path(plan_path).read_text());old=json.loads((study/'result.json').read_text())
    before=json.loads((study/'before-access.json').read_text());registry=json.loads((repo/'external-selection.json').read_text())
    if plan['provided_fixture_used'] or old['provided_fixture_used'] or before['provided_fixture_used']:
        raise ValueError('External study only')
    if before['data_registry_sha256']!=sha256(repo/'external-selection.json') or any(sha256(repo/p)!=h for p,h in old['source_hashes'].items()):
        raise ValueError('Original external source freeze differs')
    entries={k:v for k,v in before['entries'].items() if v['split']=='validation'}
    if set(entries)!={k for k,v in registry['development_fixtures'].items() if v['split']=='validation'}:raise ValueError('Validation split differs')
    base=SequenceConfig(**old['selected_config']);configs=[base]+[replace(base,switch_cost_s=s) for s in plan['switch_cost_seconds'] if s!=base.switch_cost_s]
    out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    hashes={p:sha256(repo/p) for p in ['tools/possession_boundary_study.py','development/possession_boundaries.py','development/sequence_possession.py','development/sequence_metrics.py']}
    baseline_hash=_frozen_model(repo)
    write(out/'before-access.json',{'plan':plan,'source_hashes':hashes,'baseline_sha256':baseline_hash,
        'old_candidate_sha256':sha256(study/'result.json'),'configs':[asdict(c) for c in configs]})
    def assess(entries,configs,phase):
        data={};frozen={}
        for mid,entry in entries.items():
            folder=Path(entry['folder'])
            if sha256(folder/'inputs.npz')!=entry['inputs_sha256']:raise ValueError('Measurements changed')
            with np.load(folder/'inputs.npz',allow_pickle=False) as z:x={k:z[k] for k in z.files}
            d,v,u=measurements(x);data[mid]=x
            for i,cfg in enumerate(configs):
                pred=decode(evidence(d,v,u,cfg),u,x['period'],x['frame'],float(x['fps']),cfg)
                path=out/f'{phase}-{mid}-{i}.npy';np.save(path,pred,allow_pickle=False);frozen[path.name]=sha256(path)
                write(out/f'{phase}-{mid}-{i}-boundaries.json',timeline(pred,x['period'],x['frame'],float(x['fps'])))
            print(f'{phase} {mid}: predictions frozen',flush=True)
        write(out/(phase+'-prediction-freeze.json'),{'hashes':frozen,'before_target_access':True})
        games=[[] for c in configs]
        for mid,entry in entries.items():
            folder=Path(entry['folder']);x=data[mid]
            if sha256(folder/'provider-targets.npz')!=entry['targets_sha256']:raise ValueError('Targets changed')
            with np.load(folder/'provider-targets.npz',allow_pickle=False) as z:y=z['labels']
            for i in range(len(configs)):
                path=out/f'{phase}-{mid}-{i}.npy'
                if sha256(path)!=frozen[path.name]:raise ValueError('Prediction changed')
                p=np.load(path,allow_pickle=False)
                games[i].append({'id':mid,'boundaries':evaluate(y,p,x['period'],x['frame'],float(x['fps']),plan['tolerances_s']),
                                 'spells':spell_metrics(y,p,x['period'])})
        return [{'config':asdict(c),'games':g,'mean':mean_scores(g)} for c,g in zip(configs,games)]
    validation=assess(entries,configs,'validation');eligible=[i for i,s in enumerate(validation) if i and passes(s['mean'],validation[0]['mean'])]
    chosen=max(eligible,key=lambda i:(validation[i]['mean']['boundary_f1_05'],validation[i]['mean']['spell_f1'])) if eligible else None
    write(out/'candidate-freeze.json',{'selected_index':chosen,'selected':asdict(configs[chosen]) if chosen is not None else None,'before_recheck':True})
    check=None
    if chosen is not None:
        previous=json.loads((recheck/'before-access.json').read_text())
        if previous['provided_fixture_used']:raise ValueError('External recheck required')
        entries=json.loads((recheck/'prediction-freeze.json').read_text())['prepared']
        if set(entries)!={str(g['id']) for g in registry['fresh_test_fixtures']}:raise ValueError('Recheck fixtures differ')
        check=assess(entries,[base,configs[chosen]],'recheck')
    if _frozen_model(repo)!=baseline_hash or any(sha256(repo/p)!=h for p,h in hashes.items()):raise ValueError('Source changed')
    report={'version':plan['version'],'validation':validation,'selected_index':chosen,'recheck':check,
        'accepted_for_extended_validation':check is not None and passes(check[1]['mean'],check[0]['mean']),
        'provided_fixture_used':False,'selected_release':False,'independent_test':False,'human_ground_truth':False,
        'source_hashes':hashes,'limits':plan['limits']}
    write(out/'report.json',report);print(json.dumps({'means':[v['mean'] for v in validation],'selected_index':chosen,'accepted':report['accepted_for_extended_validation']}),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('study','recheck','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='possession-boundary-plan.json')
    a=p.parse_args();run(a.study,a.recheck,a.plan,a.out)
