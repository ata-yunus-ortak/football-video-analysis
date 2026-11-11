"""Validate exported external review against registered video, split and coverage."""
import argparse
import json
from pathlib import Path
from development.transition_benchmark import validate_reference
from tools.metrica_data import external_output,sha256
from tools.ball_candidate_selection import write


def check(doc,pack,plan):
    validate_reference(doc,plan)
    if doc['reference_origin']!='external_human_review' or doc.get('review_attestation') is not True:
        raise ValueError('Explicit independent human review attestation required')
    if pack.get('provided_fixture_used') is not False or pack.get('predictions_displayed') is not False:
        raise ValueError('Registered prediction-blind external workspace required')
    matches=[r for r in pack['clips'] if r['video_sha256']==doc['video_sha256']]
    if len(matches)!=1:raise ValueError('Reference video not uniquely registered')
    clip=matches[0]
    if any(doc[k]!=clip[k] for k in ('game_id','split','preview_sha256')):raise ValueError('Reference identity/preview changed')
    if any(b>clip['duration_s'] for a,b in doc['coverage_s']):raise ValueError('Coverage exceeds source duration')
    return {'sequence':clip['sequence'],'split':doc['split'],'events':len(doc['events']),
        'reviewed_seconds':sum(b-a for a,b in doc['coverage_s']),'reviewed_event_kinds':doc['reviewed_event_kinds'],
        'uncertain_events':sum(e['earliest_s']!=e['latest_s'] for e in doc['events']),
        'schema_and_provenance_valid':True,'independent_accuracy_certified':False,'provided_fixture_used':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('reference','workspace','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='control-development-plan.json');a=p.parse_args()
    reference=Path(a.reference);pack=Path(a.workspace)/'pack.json'
    result=check(json.loads(reference.read_text(encoding='utf-8')),json.loads(pack.read_text()),json.loads(Path(a.plan).read_text()))
    result.update(reference_sha256=sha256(reference),workspace_sha256=sha256(pack),plan_sha256=sha256(a.plan))
    out=external_output(a.out);out.mkdir(parents=True,exist_ok=False);write(out/'report.json',result);print(json.dumps(result,indent=2))
