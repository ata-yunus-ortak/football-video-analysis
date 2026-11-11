"""Build a prediction-blind local reference editor from a pinned external review pack."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import shutil
from tools.ball_candidate_selection import write
from tools.metrica_data import external_output,sha256


def run(review_pack,plan,out):
    import av
    root=Path(review_pack);spec=json.loads(Path(plan).read_text());report=json.loads((root/'report.json').read_text())
    if report['provided_fixture_used'] or report['reserved_images_used'] or spec['provided_fixture_used']:raise ValueError('External development pack required')
    out=external_output(out);out.mkdir(parents=True,exist_ok=False);clips=[]
    write(out/'before-build.json',{'review_report_sha256':sha256(root/'report.json'),'plan_sha256':sha256(plan),'source_sha256':sha256(__file__)})
    for clip in report['clips']:
        if clip['split']=='recheck' or clip['game_id'] not in spec['splits'][clip['split']]:raise ValueError('Reserved/wrong game split')
        directory=root/clip['sequence'];manifest=json.loads((directory/'video-manifest.json').read_text())
        video=Path(manifest['video'])
        if not manifest['rgb_lossless_verified'] or sha256(video)!=clip['video_sha256']:raise ValueError('Verified external source changed')
        fps=manifest['fps'];target=out/(clip['sequence']+'.mp4');count=0
        with av.open(str(video)) as reader,av.open(str(target),'w') as writer:
            source=reader.streams.video[0];encoder=writer.add_stream('libx264',rate=Fraction(str(fps)))
            encoder.width=manifest['width'];encoder.height=manifest['height'];encoder.pix_fmt='yuv420p'
            encoder.options={'crf':'12','preset':'fast'}
            for frame in reader.decode(source):
                frame.pts=count;frame.time_base=Fraction(1,1)/Fraction(str(fps))
                for packet in encoder.encode(frame):writer.mux(packet)
                count+=1
            for packet in encoder.encode():writer.mux(packet)
        if count!=len(manifest['frames']):raise ValueError('Frame count changed')
        with av.open(str(target)) as reader:
            times=[float(f.pts*f.time_base) for f in reader.decode(video=0)]
        if len(times)!=count or any(abs(t-i/fps)>1e-5 for i,t in enumerate(times)):raise ValueError('Review proxy clock changed')
        clips.append({**clip,'preview_file':target.name,'preview_sha256':sha256(target),'fps':fps,'duration_s':count/fps,
            'preview_is_lossless':False,'frame_count_and_clock_verified':True})
    write(out/'pack.json',{'clips':clips,'provided_fixture_used':False,'predictions_displayed':False,'references_created':False})
    data=json.dumps({'clips':clips},ensure_ascii=True).replace('<','\\u003c')
    (out/'pack.js').write_text('window.REVIEW_PACK='+data+';\n',encoding='utf-8')
    assets=Path(__file__).parent
    shutil.copyfile(assets/'control_reference.html',out/'index.html');shutil.copyfile(assets/'control_reference.js',out/'review.js')
    print(json.dumps({'workspace':str(out),'clips':len(clips),'references_created':False}));return clips


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('review-pack','out'):p.add_argument('--'+k,required=True)
    p.add_argument('--plan',default='control-development-plan.json')
    a=p.parse_args();run(a.review_pack,a.plan,a.out)
