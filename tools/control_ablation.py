"""Run the full pipeline and each component disabled, with independent references optional."""
import argparse
import json
from pathlib import Path
from development.transition_benchmark import validate_reference,evaluate_events
from tools.control_experiment import run as infer
from tools.ball_candidate_selection import write
from tools.metrica_data import external_output,sha256


def run(tactical_manifest,plan,out,broadcast_manifest=None,pair_alignment=None,tags_manifest=None,reference=None):
    spec=json.loads(Path(plan).read_text());out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    refs=None;reference_hash=None
    if reference:
        refs=validate_reference(json.loads(Path(reference).read_text()),spec)
        # Recheck remains locked in this development/ablation command.
        camera=json.loads(Path(tactical_manifest).read_text())
        registration=json.loads((Path(camera['analysis_path'])/'registration.json').read_text())
        if registration['fixture'].get('video_sha256')!=refs['video_sha256']:raise ValueError('Reference belongs to a different video')
        reference_hash=sha256(reference)
    reports={}
    for disabled in [None]+list(spec['components']):
        name='full' if disabled is None else 'without_'+disabled
        config={**spec,'components':dict(spec['components'])}
        if disabled:config['components'][disabled]=False
        path=out/(name+'-plan.json');write(path,config)
        reports[name]=infer(tactical_manifest,path,out/name,broadcast_manifest,pair_alignment,tags_manifest)
    # All predictions fixed before event scoring.
    write(out/'prediction-freeze.json',{k:v['events_sha256'] for k,v in reports.items()})
    for name,result in reports.items():
        if refs:
            path=out/name/'events.json'
            if sha256(path)!=result['events_sha256']:raise ValueError('Prediction changed before evaluation')
            result['event_metrics']=evaluate_events(json.loads(path.read_text()),refs)
        else:result['evaluation_status']='pending_independent_transition_reference'
    if reference and sha256(reference)!=reference_hash:raise ValueError('Reference changed')
    summary={'runs':reports,'provided_fixture_used':False,'selected_release':False,
        'reference_sha256':reference_hash,'reference_available':refs is not None,
        'accuracy_claim_allowed':False,'source_sha256':sha256(__file__)}
    write(out/'report.json',summary);return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('tactical-manifest','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='control-development-plan.json')
    for k in ('broadcast-manifest','pair-alignment','tags-manifest','reference'):p.add_argument('--'+k)
    a=p.parse_args();print(json.dumps(run(**vars(a)),indent=2))
