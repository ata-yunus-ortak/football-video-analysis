"""Prepare local external videos and blank interval-reference templates, not fake truth."""
import argparse
import json
from pathlib import Path
from tools.metrica_data import external_output,sha256
from tools.ball_candidate_selection import write
from tools.soccernet_video import run as make_video


def run(acquisition,plan,out):
    root=Path(acquisition);spec=json.loads(Path(plan).read_text());gallery=json.loads((root/'gallery.json').read_text())
    receipt=json.loads((root/'before-access.json').read_text())
    if receipt['plan_sha256']!=sha256(plan) or spec['provided_fixture_used']:raise ValueError('Registered external acquisition required')
    out=external_output(out);out.mkdir(parents=True,exist_ok=False);records=[]
    for clip in gallery['clips']:
        game=clip['source_game_id']
        if game in spec['reserved_game_ids']:raise ValueError('Reserved game is locked')
        split=next(k for k,v in spec['splits'].items() if game in v)
        sample=Path(clip['study'])/'sample-v2';dst=out/clip['id'];make_video(sample,dst,25)
        video=json.loads((dst/'video-manifest.json').read_text())
        template={'provided_fixture_used':False,'source_kind':'permitted_external_video','reference_origin':None,
            'split':split,'game_id':game,'video_sha256':video['video_sha256'],'coverage_s':[],'events':[],
            'status':'unannotated_not_evaluable','allowed_event_kinds':['control_start','control_end','touch','pass','turnover','stop','restart'],
            'event_template':{'id':None,'kind':None,'earliest_s':None,'latest_s':None,'team':None,'owner_id':None},
            'instructions':'Record independently reviewed intervals only. Set coverage only where all specified event kinds are exhaustively reviewed. Never copy algorithm predictions as reference.'}
        write(dst/'reference-template.json',template)
        records.append({'sequence':clip['id'],'game_id':game,'split':split,'frames':len(video['frames']),
            'video_sha256':video['video_sha256'],'rgb_lossless_verified':True,'reference_ready':False})
    report={'clips':records,'provided_fixture_used':False,'reserved_images_used':False,'reference_truth_created':False,
        'source_sha256':sha256(__file__),'video_adapter_sha256':sha256(Path(__file__).parent/'soccernet_video.py')}
    write(out/'report.json',report);return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('acquisition','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='control-external-acquisition-plan.json')
    a=p.parse_args();print(json.dumps(run(a.acquisition,a.plan,a.out),indent=2))
