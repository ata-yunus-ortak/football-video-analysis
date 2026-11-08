"""Step 3: image motion evidence from validated automatic identities only."""
import math
import numpy as np


class EvidenceExtractor:
    def __init__(self,config):self.cfg=config;self.previous=None

    def consume(self,packet,view):
        cfg=self.cfg
        result={'frame':packet['source_frame'],'time_s':packet['video_time_s'],'fps':packet['fps'],
            'source_id':packet['source_id'],'epoch':packet['camera_epoch'],'period':packet.get('period',1),
            'measured':False,'candidate':None,'touch_candidate':None,'flight':False,'contested':False,
            'speed':None,'motion_valid':False,'reason':'unusable_view'}
        old=self.previous;self.previous=None
        if not view['view_eligible'] or view['ball'] is None or not view['ball']['measurement']:return result
        raw={r['detection_id']:r for r in packet['objects']}
        ball=raw.get(view['ball']['detection_id'])
        if not ball or ball['kind']!='ball_candidate' or ball['confidence']<cfg.confidence:return result
        track=view['ball']['track_id'];point=np.array(ball['image_xy_px'],float)
        players={}
        for p in view['players']:
            r=raw.get(p['detection_id'])
            if r is None or not p['motion_reliable']:continue
            h=r['box_xyxy_px'][3]-r['box_xyxy_px'][1]
            if h<=0:continue
            players[p['player_id']]={'point':np.array(p['image_xy_px'],float),'height':h,'team':p['team']}
        if not players:return result
        same=(old is not None and old['source_id']==result['source_id'] and old['epoch']==result['epoch']
              and old['period']==result['period'] and old['frame']+1==result['frame'] and old['track']==track
              and old['fps']==result['fps'] and .5/result['fps']<=result['time_s']-old['time_s']<=1.5/result['fps'])
        velocity=None;dt=result['time_s']-old['time_s'] if same else None
        common=set(players)&set(old['players']) if same else set()
        if len(common)>=2:
            translation=np.median([players[k]['point']-old['players'][k]['point'] for k in common],axis=0)
            scale=float(np.median([players[k]['height'] for k in common]))
            velocity=(point-old['point']-translation)/dt/scale
            result.update(speed=float(np.linalg.norm(velocity)),motion_valid=True)
        ranked=sorted((float(np.linalg.norm(point-p['point'])/p['height']),k) for k,p in players.items())
        distance,identity=ranked[0];p=players[identity]
        close=distance<=cfg.proximity_heights
        contested=close and len(ranked)>1 and ranked[1][0]-distance<cfg.separation_heights
        relative=None;approach=False;turn=False
        if same and identity in old['players']:
            prev=old['players'][identity]
            offset=(point-p['point'])/p['height'];previous=(old['point']-prev['point'])/prev['height']
            relative=float(np.linalg.norm(offset-previous)/dt)
            approach=float(np.linalg.norm(previous))>distance
        if velocity is not None and old.get('velocity') is not None:
            denominator=np.linalg.norm(velocity)*np.linalg.norm(old['velocity'])
            turn=denominator>1e-9 and float(velocity@old['velocity']/denominator)<=cfg.turn_cosine
        touch=close and not contested and approach and turn and relative is not None and relative<=cfg.relative_speed_heights_s
        comotion=close and relative is not None and relative<=cfg.relative_speed_heights_s
        flight=result['speed'] is not None and result['speed']>=cfg.flight_speed_heights_s and not comotion
        result.update(measured=True,contested=contested,flight=flight,reason='measured_image_evidence',
            touch_candidate=identity if touch else None,
            candidate={'owner_id':identity,'team':p['team']} if not contested and not flight and (comotion or touch) else None,
            comotion=comotion,approach=approach,turn=bool(turn))
        self.previous={**result,'point':point,'players':players,'track':track,'velocity':velocity}
        return result
