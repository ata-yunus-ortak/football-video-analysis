"""Explicit local-only dual-camera illustration, not a selected inference run.

Strict output keeps all validation gates. A separately labelled ASSUMPTION VIEW
illustrates identity/control candidates using nominal native time/provider H.
Assumptions never become verification or an eligible broadcast mapping. Only
rendered media/receipts are saved; no annotations or frame prediction export.
"""
import argparse
from collections import defaultdict
from fractions import Fraction
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from development.ball_tracking import BallTrackingConfig
from development.image_analysis import ImageAnalysis
from development.homography import FrameHomographies
from development.vision import LocalVision, VisionConfig
from development.vision_measurements import SceneChangeConfig, SceneContinuity, VisionMeasurements
from development.visual_possession import VisualCamera, VisualPossessionConfig, transform
from .dead_ball_audit import _frozen_model
from .metrica_data import external_output, sha256
from .vision_local_demo import draw_ball_tracks, external_settings
from .vision_preview import draw


def assumption_context(context):
    """For explicit diagnostic display only. Never pass this to released output."""
    return dict(context, alignment_validated=True, clock_error_bound_s=0.,
                calibration_validated=context['normalized_pitch_to_image'] is not None, frame_kind='live')


def player_window(source, wanted):
    xml = ET.parse(source['meta']).getroot()
    teams = [t.get('id') for t in xml.iter('Team')]
    roster = list(xml.iter('Player'))
    if len(teams) != 2 or not roster: raise ValueError('Two metadata teams and player slots required')
    canonical, display = [], {}
    for slot, p in enumerate(roster):
        team = 'H' if p.get('teamId') == teams[0] else 'A'
        shirt, name = p.findtext('ShirtNumber') or '?', p.findtext('Name') or ''
        # Metadata-only common ID, not an image identity claim.
        key = p.get('teamId') + ':' + name + ':' + shirt if name else source['video'] + ':slot:' + str(slot)
        canonical.append((key, team))
        display[key] = team + ' #' + shirt
    if len({p[0] for p in canonical}) != len(canonical):
        canonical = [(source['video'] + ':slot:' + str(i), t) for i, (_, t) in enumerate(canonical)]
        display = {key: t + ' slot ' + str(i+1) for i, (key, t) in enumerate(canonical)}
    result = {}
    with Path(source['tracking']).open(encoding='utf-8-sig') as stream:
        for index, line in enumerate(stream):
            if index > max(wanted): break
            if index not in wanted: continue
            # Read player segment only; ignore the tracking ball entirely.
            parts = line.split(':', 2)
            if len(parts) != 3 or int(parts[0]) != index + 1: raise ValueError('Native ATD row mismatch')
            groups = parts[1].split(';')
            if len(groups) != len(roster): raise ValueError('Tracking roster mismatch')
            players = []
            for group, (key, team) in zip(groups, canonical):
                xy = [float(x) for x in group.split(',')[:2]]
                if len(xy) == 2 and np.isfinite(xy).all():
                    players.append({'player_id': key, 'team': team, 'normalized_xy': xy})
            result[index] = players
    if set(result) != set(wanted): raise ValueError('Incomplete player window')
    pitch = [float(xml.findtext('.//FieldSize/Width')), float(xml.findtext('.//FieldSize/Height'))]
    return result, display, pitch


def annotate(rgb, rows, packet, context, strict, candidate, display, camera, error):
    import cv2
    image = draw(rgb, {'source_frame':packet['source_frame'], 'video_time_s':packet['video_time_s'], 'objects':rows},
                 5, 'LOCAL REVIEW ONLY | identity/control candidates NOT validated | no tuning')
    image = draw_ball_tracks(image, packet)
    for p in candidate['players']:
        x,y = [round(v) for v in p['image_xy_px']]
        color = (80,180,255) if p['team']=='H' else (255,150,80)
        cv2.putText(image, display.get(p['player_id'],'?')+' candidate', (max(0,x-35),max(90,y+24)),
                    cv2.FONT_HERSHEY_SIMPLEX,.65,color,2,cv2.LINE_AA)
    # Nominal tracking projections remain visually distinct from detector anchors.
    if context['normalized_pitch_to_image'] is not None:
        xy = transform([r['normalized_xy'] for r in context['players']], np.array(context['normalized_pitch_to_image']))
        for point in xy:
            if np.isfinite(point).all() and 0 <= point[0] < image.shape[1] and 90 <= point[1] < image.shape[0]-170:
                cv2.drawMarker(image,tuple(round(v) for v in point),(180,180,180),cv2.MARKER_CROSS,10,1)
    band = 170
    cv2.rectangle(image,(0,image.shape[0]-band),(image.shape[1],image.shape[0]),(10,18,24),-1)
    owner = display.get(candidate['owner_id'],'unknown')
    lines = [camera.upper() + ' | strict decision: '+strict['label']+' | '+strict['reason'],
             'ASSUMPTION VIEW: '+candidate['label']+' '+owner+' | '+candidate['reason'],
             'Nominal native clock + provider homography assumed ONLY for candidate illustration',
             f'Broadcast gate CLOSED: review mapping uncertainty +/-{error:.2f}s; not verified for ownership']
    for i,text in enumerate(lines):
        cv2.putText(image,text,(16,image.shape[0]-140+i*32),cv2.FONT_HERSHEY_SIMPLEX,.7,
                    (255,210,80) if i==1 else (225,235,245),2,cv2.LINE_AA)
    return image


def render_source(key, source, indices, reg, ball_plan, owner_plan, out, error):
    import av
    import cv2
    fps = float(source['fps'])
    wanted = set(range(min(indices),max(indices)+1))
    players, display, pitch = player_window(source,wanted)
    geometry = FrameHomographies(source['homography'])
    engine = LocalVision(VisionConfig(**reg['config']['parameters']), Path(reg['config']['weights']['path']), fps, 'cpu')
    scene = reg['config'].get('scene_change_parameters')
    continuity = SceneContinuity(fps, SceneChangeConfig(**scene) if scene else None)
    measurements = VisionMeasurements(fps)
    analysis = ImageAnalysis('local-review-'+key,BallTrackingConfig(**ball_plan['parameters']))
    strict_engine, assumption_engine = VisualCamera(VisualPossessionConfig(**owner_plan['parameters'])), VisualCamera(VisualPossessionConfig(**owner_plan['parameters']))
    repetitions = defaultdict(int)
    for f in indices: repetitions[f] += 1
    target = out/(key+'.mp4'); encoded,processed = 0,0
    with av.open(source['video']) as container, av.open(str(target),'w') as writer:
        stream = container.streams.video[0]
        origin = float(stream.start_time * stream.time_base)
        container.seek(int((origin+min(indices)/fps)/stream.time_base),stream=stream)
        encoder = writer.add_stream('libx264',rate=Fraction(str(fps))/5)
        encoder.width,encoder.height,encoder.pix_fmt=1280,720,'yuv420p'
        encoder.options={'crf':'18','preset':'veryfast'}
        for frame in container.decode(stream):
            time = float(frame.pts*frame.time_base)-origin; index=round(time*fps)
            if index < min(indices):continue
            if index > max(indices):break
            if index != min(indices)+processed:raise ValueError('Native video sequence gap')
            rgb=frame.to_ndarray(format='rgb24');monitor=continuity.observe(rgb,index,time)
            if monitor['continuity_reset']:engine.reset_tracking()
            rows,evidence=measurements.annotate(engine.process(rgb),index,time,int(rgb.shape[1]),int(rgb.shape[0]),monitor)
            packet=analysis.consume({'source_frame':index,'video_time_s':time,'fps':fps,'width':int(rgb.shape[1]),
                'height':int(rgb.shape[0]),'objects':rows,'frame_evidence':evidence,'possession_inferred':False})
            h=geometry.matrices[index].tolist() if index<len(geometry.matrices) and geometry.usable[index] else None
            context={k:packet[k] for k in ('source_id','source_frame','camera_epoch','video_time_s')}
            context.update(origin='automatic_player_tracking',tracking_sha256=source['tracking_sha256'],metadata_sha256=source['meta_sha256'],
                homography_sha256=source['homography_sha256'],alignment_validated=False,clock_error_bound_s=error,
                calibration_validated=False,frame_kind='unknown',pitch_m=pitch,normalized_pitch_to_image=h,players=players[index])
            strict=strict_engine.consume(packet,context)
            # Separate diagnostic state; these outputs cannot become strict ownership.
            candidate=assumption_engine.consume(packet,assumption_context(context))
            if repetitions[index]:
                image=annotate(rgb,rows,packet,context,strict,candidate,display,key,error)
                image=cv2.resize(image,(1280,720),interpolation=cv2.INTER_AREA)
                for _ in range(repetitions[index]):
                    output=av.VideoFrame.from_ndarray(image,format='rgb24')
                    output.pts,output.time_base=encoded,Fraction(5,1)/Fraction(str(fps))
                    for encoded_packet in encoder.encode(output):writer.mux(encoded_packet)
                    encoded+=1
            processed+=1
            if processed%10==0:print(key+': '+str(processed)+' native frames',flush=True)
        if processed!=len(wanted) or encoded!=len(indices):raise ValueError('Incomplete local camera rendering')
        for encoded_packet in encoder.encode():writer.mux(encoded_packet)
    return target


def run(alignment, external_run, ball_plan, owner_plan, out, local_review=False):
    if not local_review: raise ValueError('Explicit local review request required')
    reg=external_settings(external_run)
    alignment_path=Path(alignment);mapping=json.loads(alignment_path.read_text())
    bp,op=json.loads(Path(ball_plan).read_text()),json.loads(Path(owner_plan).read_text())
    if (bp.get('provided_fixture_used') is not False or bp.get('selected_release') is not False
            or bp.get('parameters_origin')!='Fixed synthetic engineering checks, not football accuracy selection'
            or 'foot_context_parameters' in bp or op.get('provided_fixture_used') is not False
            or op.get('selected_release') is not False or op.get('parameters_origin')!='synthetic_engineering_checks_only'):
        raise ValueError('Unchanged external/synthetic plans required')
    segment=next(s for s in mapping['segments'] if s['status']=='clock_and_tracking_candidate' and s['t1']-s['t0']>=2.1)
    tactical=mapping['sources']['tactical'];broadcast=mapping['sources']['broadcast']
    start=math.ceil(segment['t0']*tactical['fps']);indices=list(range(start,start+50))
    times=[i/tactical['fps'] for i in indices]
    b_indices=[round((segment['b0']+(t-segment['t0'])*(segment['b1']-segment['b0'])/(segment['t1']-segment['t0']))*broadcast['fps']) for t in times]
    paths=[alignment_path,Path(ball_plan),Path(owner_plan),Path(external_run)/'registration.json']
    for source in (tactical,broadcast):
        video=Path(source['video'])
        if video.stat().st_size!=source['video_bytes'] or video.stat().st_mtime_ns!=source['video_mtime_ns']:
            raise ValueError('Video fingerprint changed')
        for name in ('meta','tracking','homography'):
            p=Path(source[name])
            if sha256(p)!=source[name+'_sha256']:raise ValueError('Automatic source changed')
            paths.append(p)
    weights=Path(reg['config']['weights']['path'])
    if sha256(weights)!=reg['config']['weights']['sha256']:raise ValueError('Checkpoint changed')
    paths.append(weights)
    repo=Path(__file__).resolve().parents[1];baseline=_frozen_model(repo)
    modules=['tools/visual_local_review.py','tools/vision_local_demo.py','tools/vision_preview.py',
             'development/visual_possession.py','development/image_analysis.py','development/ball_tracking.py',
             'development/vision.py','development/vision_measurements.py','development/homography.py']
    paths += [repo/name for name in modules]
    hashes={str(p.resolve()):sha256(p) for p in paths}
    out=external_output(out);out.mkdir(parents=True,exist_ok=False)
    (out/'registration.json').write_text(json.dumps({'purpose':'explicit_user_requested_local_review_only',
        'before_decode':True,'training':False,'threshold_selection':False,'accuracy_evaluation':False,
        'images_uploaded':False,'frame_predictions_exported':False,'tracking_ball_used':False,
        'strict_validation_overridden':False,'diagnostic_assumptions':'Separate displayed hypothetical native-time/provider-homography/live view only; not verified output',
        'broadcast_fusion_enabled':False,'mapping_uncertainty_s':segment['uncertainty_s'],
        'source_frame_windows':{'tactical':[min(indices),max(indices)],'broadcast':[min(b_indices),max(b_indices)]},
        'input_source_sha256':hashes,'baseline_model_sha256':baseline},indent=2),encoding='utf-8')
    results={}
    for key,source,native in [('tactical',tactical,indices),('broadcast',broadcast,b_indices)]:
        path=render_source(key,source,native,reg,bp,op,out,segment['uncertainty_s'])
        results[key]={'path':str(path),'sha256':sha256(path),'display_frames':len(native)}
    if _frozen_model(repo)!=baseline or any(sha256(p)!=h for p,h in hashes.items()):raise ValueError('Model/source/input changed')
    (out/'complete.json').write_text(json.dumps({'complete':True,'videos':results,'images_uploaded':0,
        'accuracy_evaluated':False,'strict_broadcast_fusion_enabled':False},indent=2),encoding='utf-8')
    print('Dual-camera local review complete: '+str(out),flush=True)
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('alignment','external-run','ball-plan','owner-plan','out'):parser.add_argument('--'+key,required=True)
    parser.add_argument('--local-review',action='store_true')
    print(json.dumps(run(**vars(parser.parse_args())),indent=2))
