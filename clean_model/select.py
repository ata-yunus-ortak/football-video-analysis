"""Remediation selection on registered external fixtures only; never loads BAR-ATH."""
import argparse,hashlib,json,time
from dataclasses import asdict
from pathlib import Path
import numpy as np
from .decoder import DecoderConfig,candidate_grid,predict
from .team_confirmation import TeamConfirmationConfig,predict_team
from .metrics import measure

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def sources():return {p.name:digest(p) for p in Path(__file__).parent.glob('*.py')}
def load(entry):
    root=Path(entry['folder']);assert digest(root/'inputs.npz')==entry['inputs_sha256'];assert digest(root/'provider-targets.npz')==entry['targets_sha256']
    with np.load(root/'inputs.npz',allow_pickle=False) as z:x={k:z[k] for k in z.files}
    assert not {'labels','truth','possession','manual_annotations'}.intersection(x)
    with np.load(root/'provider-targets.npz',allow_pickle=False) as z:y=z['labels']
    assert x['players'].shape[0]==len(y) and x['ball'].shape==(len(y),2)
    return x,y
def score(items):return {k:float(np.mean([m[k] for m in items])) for k in ('provider_team_spell_iou_f1','provider_macro_f1_HA','provider_frame_agreement')}
def infer(x,base,policy):
    if policy=='nearest':return predict(x,None)[0]
    if policy=='slot':return predict(x,base)[0]
    return predict_team(x,base,TeamConfirmationConfig(measured_votes_only=policy=='team_measured'))[0]
def run(plan_path,out):
    out=Path(out);out.mkdir(exist_ok=True);plan=json.loads(Path(plan_path).read_text());freeze=out/'model-freeze.json'
    if freeze.exists():raise ValueError('Selection is already frozen; do not select again after test access')
    assert plan['provided_fixture_used_for_selection'] is False
    assert all(v['game']['competition_id']==61 for v in plan['development_fixtures'].values())
    before=sources();(out/'selection-code-freeze.json').write_text(json.dumps({'files':before,'before_selection':True,'plan_sha256':digest(plan_path)},indent=2))
    train=[load(v) for v in plan['development_fixtures'].values() if v['split']=='train'];grid,calibration=candidate_grid(train);del train
    # Gap-free and externally calibrated interpolation are both selected outside.
    configs={}
    for base in grid:
        for gap in (0,base.gap_frames):
            new=DecoderConfig(**{**asdict(base),'gap_frames':gap});configs[tuple(asdict(new).values())]=new
    val=[load(v) for v in plan['development_fixtures'].values() if v['split']=='validation'];results=[];start=time.perf_counter();total=len(configs)*3+1
    baseline=score([measure(y,infer(x,None,'nearest'),x['period']) for x,y in val]);results.append({'policy':'nearest','config':None,'scores':baseline})
    for base in configs.values():
        for policy in ('slot','team_measured','team_estimated'):
            metrics=[measure(y,infer(x,base,policy),x['period']) for x,y in val];results.append({'policy':policy,'config':asdict(base),'scores':score(metrics)})
            if len(results)%12==0:print(json.dumps({'external_candidates':len(results),'total':total,'seconds':round(time.perf_counter()-start,1)}),flush=True)
    results.sort(key=lambda r:(-r['scores']['provider_team_spell_iou_f1'],-r['scores']['provider_macro_f1_HA'],json.dumps([r['policy'],r['config']],sort_keys=True)))
    selected=results[0];assert sources()==before
    model={'version':'remediated-external-v1','policy':selected['policy'],'base_config_at_10fps':selected['config'],'training_fps':10.,'selection_scores':selected['scores'],
        'source_hashes':before,'selection_plan_sha256':digest(plan_path),'external_provider_proxy_only':True,'provided_fixture_used_for_selection':False,
        'fresh_test_tracking_accessed_before_freeze':False,'not_official_competition_scores':True,'vision_and_dead_ball_branch':'not in this frozen release; independent selection evidence still required'}
    freeze.write_text(json.dumps(model,indent=2));(out/'validation-results.json').write_text(json.dumps({'calibration':calibration,'candidates':results,'known_previous_external_exposure':True},indent=2));print(json.dumps({'selected':selected,'candidate_count':len(results),'seconds':time.perf_counter()-start,'provided_fixture_used':False}));return model

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.plan,a.out)
