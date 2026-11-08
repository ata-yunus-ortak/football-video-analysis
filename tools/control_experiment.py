"""Six-step experimental video ownership, with component ablations and provenance."""
import argparse
from collections import Counter
import json
from pathlib import Path
from development.visual_possession import VisualCamera,VisualPossessionConfig,choose_view
from development.control_states import ControlConfig
from development.control_evidence import EvidenceExtractor
from development.control_decoder import decode
from development.control_tag_gate import dead_candidates
from tools.visual_possession_experiment import load_camera
from tools.ball_support_experiment import indexed
from tools.ball_candidate_selection import write
from tools.metrica_data import external_output,sha256
from tools.dead_ball_audit import _frozen_model


def run(tactical_manifest,plan,out,broadcast_manifest=None,pair_alignment=None,tags_manifest=None):
    repo=Path(__file__).resolve().parents[1];plan=Path(plan);spec=json.loads(plan.read_text())
    if spec['provided_fixture_used'] or spec['selected_release'] or spec['parameters_origin']!='synthetic_engineering_checks_only':
        raise ValueError('Unselected external engineering plan required')
    if (broadcast_manifest is None)!=(pair_alignment is None):raise ValueError('Camera and mapping required together')
    cfg=ControlConfig(**spec['parameters']);components=spec['components']
    if set(components)!={'motion','backdating','flight','broadcast','tags'} or any(type(v) is not bool for v in components.values()):
        raise ValueError('Explicit component switches required')
    visual_path=repo/'visual-possession-plan.json'
    visual_cfg=VisualPossessionConfig(**json.loads(visual_path.read_text())['parameters'])
    ts,tactical,count,paths=load_camera(tactical_manifest)
    pairs={};broadcast=iter(());tags=[];signals=[];extra=[]
    if broadcast_manifest:
        bs,broadcast,_,bp=load_camera(broadcast_manifest)
        if ts['fixture_id']!=bs['fixture_id']:raise ValueError('Same fixture required')
        pairs=indexed(pair_alignment,'primary_frame');paths+=bp+[Path(pair_alignment)]
    if tags_manifest:
        m=json.loads(Path(tags_manifest).read_text())
        if m['provided_fixture_used'] or m['fixture_id']!=ts['fixture_id'] or m['origin']!='automatic_provider_tags':raise ValueError('Same external automatic tag source required')
        for role in ('tags','signals'):
            path=Path(m[role+'_path'])
            if sha256(path)!=m[role+'_sha256']:raise ValueError('Tag/signal source changed')
            extra.append(path)
        tags=json.loads(extra[0].read_text());signals=json.loads(extra[1].read_text());extra.append(Path(tags_manifest))
        if any(t.get('origin')!='automatic_provider_tags' or t['start_s']>t['end_s'] for t in tags):raise ValueError('Automatic ordered tag ranges required')
    sources=[repo/p for p in ('tools/control_experiment.py','development/control_states.py','development/control_evidence.py',
        'development/control_decoder.py','development/control_tag_gate.py','development/visual_possession.py','tools/visual_possession_experiment.py','development/set_piece_dead_ball.py')]
    paths+=sources+extra+[plan,visual_path];hashes={str(p.resolve()):sha256(p) for p in paths};baseline=_frozen_model(repo)
    out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    write(out/'registration.json',{'before_inference':True,'provided_fixture_used':False,'selected_release':False,
        'input_source_sha256':hashes,'plan':spec,'baseline_sha256':baseline,'reference_annotations_as_inputs':False})
    tv,bv=VisualCamera(visual_cfg),VisualCamera(visual_cfg);te,be=EvidenceExtractor(cfg),EvidenceExtractor(cfg)
    rows=[];trows=[];routing=[];cached=None;used=set();prior_pair=None
    for packet,context in tactical:
        t=tv.consume(packet,context);tr=te.consume(packet,t);b=None;br=None;pair=pairs.get(packet['source_frame'])
        if pair is not None:
            used.add(packet['source_frame']);target=pair['secondary_frame']
            if prior_pair is not None and (packet['source_frame']<=prior_pair[0] or target<=prior_pair[1]):raise ValueError('Reused/backward camera mapping')
            if prior_pair is not None and packet['source_frame']==prior_pair[0]+1 and target!=prior_pair[1]+1:pair={**pair,'verified':False}
            prior_pair=(packet['source_frame'],target)
            while cached is None or cached[0]['source_frame']<target:
                item=next(broadcast,None)
                if item is None:raise ValueError('Mapped broadcast frame absent')
                bp,bc=item;bview=bv.consume(bp,bc);cached=(bp,bview,be.consume(bp,bview))
            if cached[0]['source_frame']==target:b,br=cached[1:]
        routed=choose_view(t,b,pair,visual_cfg)
        use=components['broadcast'] and routed['decision_source']=='broadcast'
        chosen=dict(br if use else tr)
        chosen.update(frame=packet['source_frame'],time_s=packet['video_time_s'],fps=packet['fps'])
        if not components['motion']:
            # Ablation retains current image control from the existing spatial/identity path.
            view=b if use else t
            chosen.update(candidate={'owner_id':view['owner_id'],'team':view['label']} if view['label'] in ('H','A') else None,
                          touch_candidate=None,flight=False)
        rows.append(chosen);trows.append(tr);routing.append('broadcast' if use else 'tactical')
    for _ in broadcast:pass
    if len(rows)!=count or used!=set(pairs):raise ValueError('Incomplete camera/mapping coverage')
    dead,stops=dead_candidates(trows,tags,signals,cfg) if components['tags'] else ([False]*len(rows),[])
    output,events=decode(rows,cfg,backdating=components['backdating'],flight=components['flight'],dead=dead)
    with (out/'frames.jsonl').open('w',encoding='utf-8',newline='\n') as f:
        for r,e,source in zip(output,rows,routing):
            r.update(decision_source=source,evidence=e,tracking_ball_used=False,baseline_owner_used=False)
            f.write(json.dumps(r,allow_nan=False)+'\n')
    write(out/'events.json',sorted(events+stops,key=lambda e:(e['time_s'],e['kind'])))
    if _frozen_model(repo)!=baseline or any(sha256(p)!=h for p,h in hashes.items()):raise ValueError('Frozen inputs changed')
    summary={'frames':len(rows),'state_counts':dict(Counter(r['state'] for r in output)),
        'team_counts':dict(Counter(r['team'] for r in output)),'sources':dict(Counter(routing)),
        'components':components,'provided_fixture_used':False,'selected_release':False,'accuracy_evaluated':False,
        'output_sha256':sha256(out/'frames.jsonl'),'events_sha256':sha256(out/'events.json'),
        'player_identity_validated_by_external_truth':False,'independent_transition_truth_available':False}
    write(out/'summary.json',summary);return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('tactical-manifest','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='control-development-plan.json')
    for k in ('broadcast-manifest','pair-alignment','tags-manifest'):p.add_argument('--'+k)
    print(json.dumps(run(**vars(p.parse_args())),indent=2))
