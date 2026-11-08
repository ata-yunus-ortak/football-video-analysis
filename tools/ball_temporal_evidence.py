"""Attach frozen experimental ball evidence to registered external analysis.

Preserves raw detections, tracks and ownership. No reference annotations are read.
This is an offline diagnostic adapter, not a promoted possession input.
"""
import argparse
import json
from pathlib import Path
from development.ball_tracking import BallTrackingConfig
from development.temporal_ball_features import extract,probability
from tools.ball_candidate_selection import write
from tools.ball_temporal_selection import load_inputs
from tools.metrica_data import external_output,sha256


def attach(packets,base,candidate):
    arrays=extract(packets,base);output=[]
    for packet,features in zip(packets,arrays):
        balls=[r for r in packet['objects'] if r['kind']=='ball_candidate']
        values=probability(features,candidate['model'])
        evidence=[{'detection_id':r['detection_id'],'proposal_score':float(p),
                   'passes_experimental_filter':bool(p>=candidate['threshold'])}
                  for r,p in zip(balls,values)]
        output.append({**packet,'experimental_ball_evidence':{
            'schema':'temporal-ball-evidence-v1','detections':evidence,
            'reference_annotations_used':False,'max_future_frames':4,'offline_only':True,
            'scores_are_calibrated_probabilities':False,'selected_in_play_ball':False,
            'possession_eligible':False,'selected_release':False}})
    return output


def run(gallery,analysis,study,out):
    repo=Path(__file__).resolve().parents[1];study=Path(study);analysis=Path(analysis)
    report=json.loads((study/'report.json').read_text())
    if report['provided_fixture_used'] or report['version']!='external-ball-temporal-learned-v1':
        raise ValueError('Registered external temporal study required')
    if sha256(study/'candidate-freeze.json')!=report['candidate_freeze_sha256']:
        raise ValueError('Frozen candidate changed')
    if any(sha256(repo/p)!=h for p,h in report['source_hashes'].items()):
        raise ValueError('Study implementation changed')
    candidate=json.loads((study/'candidate-freeze.json').read_text())['selected']
    if candidate is None or not candidate['temporal']:raise ValueError('No frozen temporal candidate')
    before=json.loads((study/'before-access.json').read_text())
    if sha256(gallery)!=before['gallery_sha256']:raise ValueError('Gallery changed')
    if any(sha256(p)!=h for p,h in before['input_hashes'].items()):raise ValueError('Registered measurements changed')
    clips=json.loads(Path(gallery).read_text())['clips']
    for clip in clips:
        for mode in before['plan']['modes']:
            path=analysis/clip['id']/mode/'frames.jsonl'
            if before['input_hashes'].get(str(path))!=sha256(path):
                raise ValueError('Analysis path/content is not the registered input')
    runs=load_inputs(clips,analysis,before['plan']['modes'])
    out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    write(out/'registration.json',{'candidate_sha256':sha256(study/'candidate-freeze.json'),
        'source_sha256':sha256(__file__),'study_report_sha256':sha256(study/'report.json'),
        'provided_fixture_used':False,'selected_release':False,'reference_annotations_read':False})
    counts=[];base=BallTrackingConfig(**before['base_parameters'])
    for r in runs:
        packets=attach(r['packets'],base,candidate)
        dest=out/r['clip']/r['mode'];dest.mkdir(parents=True)
        path=dest/'frames.jsonl'
        with path.open('w',encoding='utf-8',newline='\n') as stream:
            for p in packets:stream.write(json.dumps(p,allow_nan=False)+'\n')
        evidence=[e for p in packets for e in p['experimental_ball_evidence']['detections']]
        counts.append({'clip':r['clip'],'mode':r['mode'],'frames':len(packets),'raw_candidates':len(evidence),
            'passing_candidates':sum(e['passes_experimental_filter'] for e in evidence),'output_sha256':sha256(path)})
    if any(sha256(p)!=h for p,h in before['input_hashes'].items()):raise ValueError('Input changed during integration')
    result={'runs':counts,'provided_fixture_used':False,'selected_release':False,'reference_annotations_read':False,
        'raw_detections_preserved':True,'existing_tracks_and_possession_preserved':True,
        'purpose':'Offline experimental evidence only; full promotion gate failed.'}
    write(out/'report.json',result);print(json.dumps(result,indent=2));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('gallery','analysis','study','out'):p.add_argument('--'+k,required=True)
    a=p.parse_args();run(a.gallery,a.analysis,a.study,a.out)
