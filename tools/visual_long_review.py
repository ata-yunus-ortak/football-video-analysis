"""User-requested five-minute local viewer; same settings, no accuracy selection.

Rendered read-only review chunks are made available while processing continues.
Ownership is the existing assumption-view candidate, visibly not validated truth.
No forced nearest-player owner and no provider ball/old ownership input.
"""
import argparse
from fractions import Fraction
import json
import math
import pickle
from pathlib import Path
import statistics
import time

from development.ball_tracking import BallTrackingConfig
from development.homography import FrameHomographies
from development.image_analysis import ImageAnalysis
from development.vision import LocalVision, VisionConfig
from development.vision_measurements import SceneChangeConfig, SceneContinuity, VisionMeasurements
from development.visual_possession import VisualCamera, VisualPossessionConfig
from .dead_ball_audit import _frozen_model
from .metrica_data import external_output, sha256
from .vision_local_demo import external_settings
from .visual_local_review import assumption_context, annotate, player_window


def clock_start(path):
    observations=[]
    with Path(path).open(encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)
            if row.get('status')=='observed_clock' and row.get('clock_s') is not None:
                if row.get('human_annotated') is not False: raise ValueError('Automatic clock source required')
                observations.append(row['video_time_s']-row['clock_s'])
                if len(observations)==3:break
    if len(observations)!=3 or max(observations)-min(observations)>1:
        raise ValueError('Stable automatic initial clock observations required')
    return statistics.median(observations)


def status_file(out, data):
    temp=out/'status.tmp'
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(out/'status.json')


def mark_selected(image, packet, candidate, display, match_s):
    import cv2
    player=next((p for p in candidate['players'] if p['player_id']==candidate['owner_id']),None)
    if player is not None:
        person=next(r for r in packet['objects'] if r['detection_id']==player['detection_id'])
        x0,y0,x1,y1=[round(v) for v in person['box_xyxy_px']]
        cv2.rectangle(image,(x0-7,y0-7),(x1+7,y1+7),(80,255,100),5)
        cv2.arrowedLine(image,((x0+x1)//2,max(90,y0-70)),((x0+x1)//2,max(90,y0-10)),(80,255,100),4,tipLength=.35)
    # A large, fixed-position owner label remains readable during real-time play.
    text=('ALG SECIMI: '+('BARCELONA ' if candidate['label']=='H' else 'ATHLETIC ')+display.get(candidate['owner_id'],'?')) if player else 'ALG SECIMI: BELIRSIZ (X) - OYUNCU SECILMEDI'
    cv2.rectangle(image,(0,75),(image.shape[1],140),(10,18,24),-1)
    cv2.putText(image,text,(18,118),cv2.FONT_HERSHEY_SIMPLEX,1.05,(80,255,100) if player else (255,210,80),3,cv2.LINE_AA)
    cv2.putText(image,f'MATCH CLOCK APPROX {int(match_s)//60:02d}:{int(match_s)%60:02d} | CANDIDATE, NOT VERIFIED',
                (18,170),cv2.FONT_HERSHEY_SIMPLEX,.75,(240,245,250),2,cv2.LINE_AA)
    return image


def concatenate(chunks, out):
    import av
    offset=0.
    with av.open(str(out),'w',options={'movflags':'+faststart'}) as writer:
        output=None
        for path in chunks:
            with av.open(str(path)) as source:
                stream=source.streams.video[0]
                if output is None:output=writer.add_stream_from_template(stream)
                for packet in source.demux(stream):
                    if packet.dts is None:continue
                    shift=round(offset/float(packet.time_base))
                    packet.pts+=shift;packet.dts+=shift;packet.stream=output
                    writer.mux(packet)
                offset+=stream.frames/float(stream.average_rate)


def run(alignment, external_run, clock, ball_plan, owner_plan, out, device='cuda', local_review=False, resume=False):
    if not local_review:raise ValueError('Explicit user-requested local review required')
    import av
    import cv2
    import torch
    reg=external_settings(external_run)
    mapping=json.loads(Path(alignment).read_text());source=mapping['sources']['tactical']
    bp,op=json.loads(Path(ball_plan).read_text()),json.loads(Path(owner_plan).read_text())
    if (bp.get('provided_fixture_used') is not False or bp.get('selected_release') is not False
            or bp.get('parameters_origin')!='Fixed synthetic engineering checks, not football accuracy selection'
            or 'foot_context_parameters' in bp or op.get('provided_fixture_used') is not False
            or op.get('selected_release') is not False or op.get('parameters_origin')!='synthetic_engineering_checks_only'):
        raise ValueError('Existing plans required, no review-specific algorithm changes')
    if device=='cuda' and not torch.cuda.is_available():raise ValueError('Requested GPU unavailable')
    torch.set_num_threads(2)
    if device=='cuda':torch.backends.cuda.matmul.allow_tf32=False
    fps=float(source['fps']);origin_s=clock_start(clock);start=round(origin_s*fps);count=round(300*fps)
    wanted=set(range(start,start+count))
    video=Path(source['video'])
    if video.stat().st_size!=source['video_bytes'] or video.stat().st_mtime_ns!=source['video_mtime_ns']:
        raise ValueError('Registered video changed')
    for name in ('meta','tracking','homography'):
        if sha256(source[name])!=source[name+'_sha256']:raise ValueError('Automatic source changed')
    weights=Path(reg['config']['weights']['path'])
    if sha256(weights)!=reg['config']['weights']['sha256']:raise ValueError('Checkpoint changed')
    repo=Path(__file__).resolve().parents[1];baseline=_frozen_model(repo)
    files=[Path(alignment),Path(clock),Path(ball_plan),Path(owner_plan),weights,
           Path(external_run)/'registration.json',*[Path(source[k]) for k in ('meta','tracking','homography')]]
    files += [repo/p for p in ('tools/visual_long_review.py','tools/visual_local_review.py','development/visual_possession.py',
              'development/ball_tracking.py','development/image_analysis.py','development/vision.py',
              'development/vision_measurements.py','development/homography.py','tools/vision_preview.py','tools/vision_local_demo.py')]
    frozen={str(p.resolve()):sha256(p) for p in files}
    out=external_output(out);out.mkdir(parents=True,exist_ok=True)
    if not resume and any(out.iterdir()):raise ValueError('New empty local output directory required')
    receipt={'purpose':'user_requested_first_five_match_minutes_local_review_only','before_decode':True,
        'source_start_s':origin_s,'source_frames':[start,start+count-1],'source_fps':fps,
        'requested_duration_s':300,'all_source_frames_processed':True,'frame_sampling':False,
        'training':False,'threshold_selection':False,'accuracy_evaluated':False,'images_uploaded':0,
        'tracking_ball_used':False,'frame_predictions_exported':False,'strict_validation_overridden':False,
        'diagnostic_assumptions':'Separate nominal native-clock/provider-H/live candidate, always visibly unvalidated',
        'broadcast_fusion_enabled':False,'input_source_sha256':frozen,'baseline_model_sha256':baseline,
        'runtime':{'torch':torch.__version__,'device':device,'cuda':torch.version.cuda,
                   'gpu':torch.cuda.get_device_name() if device=='cuda' else None},
        'parameters':reg['config']['parameters']}
    if resume:
        previous_receipt=json.loads((out/'registration.json').read_text())
        if previous_receipt['input_source_sha256']!=frozen or previous_receipt['parameters']!=receipt['parameters']:
            raise ValueError('Resume must preserve registered source and settings')
        (out/'resume-runtime.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    else:
        (out/'registration.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    progress={'complete':False,'processed_frames':0,'total_frames':count,'ready_seconds':0,'chunks':[],
              'source_start_s':origin_s,'source_fps':fps,'broadcast_fusion_enabled':False}
    checkpoint=None
    if resume:
        progress=json.loads((out/'status.json').read_text())
        if not progress.get('paused_for_device_switch') or sha256(out/'checkpoint.pkl')!=progress['checkpoint_sha256']:
            raise ValueError('Intact self-generated paused checkpoint required')
        # Only this registered local process writes this path; never unpickle an uploaded artifact.
        with (out/'checkpoint.pkl').open('rb') as stream:checkpoint=pickle.load(stream)
        progress.pop('paused_for_device_switch',None)
    status_file(out,progress)
    # UI mappings are presentation candidates only, no broadcast ownership input.
    (out/'mapping.json').write_text(json.dumps({'source_start_s':origin_s,'segments':mapping['segments'],
        'usable_for_possession':False}),encoding='utf-8')
    players,display,pitch=player_window(source,wanted)
    geometry=FrameHomographies(source['homography'])
    engine=LocalVision(VisionConfig(**reg['config']['parameters']),weights,fps,device)
    engine.detector.inference(compile=True,dtype=torch.float32)
    scene=reg['config'].get('scene_change_parameters')
    continuity=SceneContinuity(fps,SceneChangeConfig(**scene) if scene else None)
    measurements=VisionMeasurements(fps)
    analysis=ImageAnalysis('local-five-minute-review',BallTrackingConfig(**bp['parameters']))
    cfg=VisualPossessionConfig(**op['parameters'])
    strict_engine,candidate_engine=VisualCamera(cfg),VisualCamera(cfg)
    chunk_frames=round(10*fps);writer,encoder=None,None;processed=0;chunk_count=0
    if checkpoint is not None:
        engine.tracker.__dict__.update(checkpoint['tracker_state'])
        continuity,measurements,analysis=checkpoint['continuity'],checkpoint['measurements'],checkpoint['analysis']
        strict_engine,candidate_engine=checkpoint['strict'],checkpoint['candidate']
        processed=progress['processed_frames']
    begin=time.perf_counter()
    try:
        with av.open(str(video)) as container:
            stream=container.streams.video[0];origin=float(stream.start_time*stream.time_base)
            container.seek(int((origin+(start+processed)/fps)/stream.time_base),stream=stream)
            for frame in container.decode(stream):
                timestamp=float(frame.pts*frame.time_base)-origin;index=round(timestamp*fps)
                if index<start+processed:continue
                if processed==count:break
                if index!=start+processed:raise ValueError('Unexpected native video frame sequence')
                rgb=frame.to_ndarray(format='rgb24');monitor=continuity.observe(rgb,index,timestamp)
                if monitor['continuity_reset']:engine.reset_tracking()
                rows,evidence=measurements.annotate(engine.process(rgb),index,timestamp,int(rgb.shape[1]),int(rgb.shape[0]),monitor)
                packet=analysis.consume({'source_frame':index,'video_time_s':timestamp,'fps':fps,
                    'width':int(rgb.shape[1]),'height':int(rgb.shape[0]),'objects':rows,'frame_evidence':evidence,'possession_inferred':False})
                matrix=geometry.matrices[index].tolist() if geometry.usable[index] else None
                context={k:packet[k] for k in ('source_id','source_frame','camera_epoch','video_time_s')}
                context.update(origin='automatic_player_tracking',tracking_sha256=source['tracking_sha256'],metadata_sha256=source['meta_sha256'],
                    homography_sha256=source['homography_sha256'],alignment_validated=False,clock_error_bound_s=0.,calibration_validated=False,
                    frame_kind='unknown',pitch_m=pitch,normalized_pitch_to_image=matrix,players=players[index])
                strict=strict_engine.consume(packet,context)
                candidate=candidate_engine.consume(packet,assumption_context(context))
                image=annotate(rgb,rows,packet,context,strict,candidate,display,'tactical',.4)
                image=mark_selected(image,packet,candidate,display,processed/fps)
                image=cv2.resize(image,(1280,720),interpolation=cv2.INTER_AREA)
                if writer is None:
                    chunk_path=out/f'part-{len(progress["chunks"]):03d}.mp4'
                    writer=av.open(str(chunk_path),'w',options={'movflags':'+faststart'})
                    encoder=writer.add_stream('libx264',rate=Fraction(str(fps)))
                    encoder.width,encoder.height,encoder.pix_fmt=1280,720,'yuv420p'
                    encoder.options={'crf':'20','preset':'veryfast'};chunk_count=0
                output=av.VideoFrame.from_ndarray(image,format='rgb24')
                output.pts,output.time_base=chunk_count,Fraction(1,1)/Fraction(str(fps))
                for encoded in encoder.encode(output):writer.mux(encoded)
                processed+=1;chunk_count+=1
                if chunk_count==chunk_frames or processed==count:
                    for encoded in encoder.encode():writer.mux(encoded)
                    writer.close();writer=None
                    progress['chunks'].append({'file':chunk_path.name,'duration_s':chunk_count/fps,'frames':chunk_count})
                    progress.update(processed_frames=processed,ready_seconds=processed/fps,
                                    elapsed_s=round(time.perf_counter()-begin,1))
                    status_file(out,progress)
                    if device=='cpu' and (out/'switch-to-gpu.request').exists() and processed<count:
                        if _frozen_model(repo)!=baseline or any(sha256(p)!=h for p,h in frozen.items()):
                            raise ValueError('Source/settings changed before checkpoint')
                        with (out/'checkpoint.pkl').open('wb') as stream:
                            pickle.dump({'tracker_state':engine.tracker.__dict__,'continuity':continuity,'measurements':measurements,
                                'analysis':analysis,'strict':strict_engine,'candidate':candidate_engine},stream)
                        progress.update(paused_for_device_switch=True,checkpoint_sha256=sha256(out/'checkpoint.pkl'))
                        status_file(out,progress)
                        print('Paused at closed chunk boundary for GPU continuation.',flush=True)
                        return progress
                if processed%100==0:
                    print(json.dumps({'processed':processed,'total':count,'ready_s':progress['ready_seconds'],
                        'elapsed_s':round(time.perf_counter()-begin,1)}),flush=True)
            if processed!=count:raise ValueError('Five-minute source interval incomplete')
        if _frozen_model(repo)!=baseline or any(sha256(p)!=h for p,h in frozen.items()):
            raise ValueError('Source, settings or baseline changed during review')
        full=out/'first-five-minutes.mp4'
        concatenate([out/c['file'] for c in progress['chunks']],full)
        with av.open(str(full)) as check:
            s=check.streams.video[0]
            if s.frames!=count or float(s.average_rate)!=fps:raise ValueError('Full clip frame count/FPS differs')
        progress.update(complete=True,processed_frames=processed,ready_seconds=300,full_video=full.name,
                        elapsed_s=round(time.perf_counter()-begin,1),output_sha256=sha256(full))
        status_file(out,progress)
        (out/'complete.json').write_text(json.dumps(progress,indent=2),encoding='utf-8')
        print('Five-minute local review complete: '+str(full),flush=True)
    except Exception as exc:
        if writer is not None:writer.close()
        progress.update(error=str(exc),processed_frames=processed,complete=False)
        status_file(out,progress)
        raise
    return progress


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('alignment','external-run','clock','ball-plan','owner-plan','out'):parser.add_argument('--'+key,required=True)
    parser.add_argument('--device',choices=('cpu','cuda'),default='cuda')
    parser.add_argument('--local-review',action='store_true')
    parser.add_argument('--resume',action='store_true')
    run(**vars(parser.parse_args()))
