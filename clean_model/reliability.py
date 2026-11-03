"""Two-sided tracking guards and uncertainty-aware acquisition, no labels input.

Height is an automatic provider estimate, not proof of contact or intent.
Interpolated points can describe a path but cannot supply new ownership votes.
"""
from dataclasses import dataclass
import numpy as np
from .decoder import distances

@dataclass(frozen=True)
class ReliabilityConfig:
    speed_limit:float
    corridor_radius:float
    maximum_detour_frames:int
    acceleration_scale:float
    interpolation_radius:float
    reachable_height:float
    suppress_airborne:bool=True
    reject_detours:bool=True
    interpolation_votes:bool=False
    require_detected_receiver:bool=False
    hold_fraction:float=1.
    def __post_init__(self):
        if any(not np.isfinite(v) or v<=0 for v in (self.speed_limit,self.corridor_radius,self.acceleration_scale,self.interpolation_radius,self.reachable_height,self.hold_fraction)):raise ValueError('Positive finite reliability scales required')
        if type(self.maximum_detour_frames) is not int or self.maximum_detour_frames<1:raise ValueError('Positive detour frame count required')
        if self.hold_fraction>1:raise ValueError('A reliability guard cannot extend the original hold')
        if any(type(v) is not bool for v in (self.suppress_airborne,self.reject_detours,self.interpolation_votes,self.require_detected_receiver)):raise ValueError('Guard switches must be booleans')

def supported_path(inputs,cfg,gap_frames):
    ball=np.asarray(inputs['ball'],float);period=np.asarray(inputs['period']);fps=float(inputs['fps']);n=len(ball)
    if ball.shape!=(n,2) or period.shape!=(n,) or np.asarray(inputs['ball_observed']).shape!=(n,) or not np.isfinite(fps) or fps<=0:raise ValueError('Aligned tracking and positive FPS required')
    real=np.asarray(inputs['ball_observed'],bool)&np.isfinite(ball).all(1)&np.isin(period,(1,2));filtered=real.copy();quarantine=np.zeros(n,bool)
    ids=np.flatnonzero(real)
    if cfg.reject_detours:
        for i in range(1,len(ids)-2):
            left,first=ids[i-1:i+1]
            if not filtered[first] or period[left]!=period[first] or np.linalg.norm(ball[first]-ball[left])*fps/(first-left)<=cfg.speed_limit:continue
            for k in range(i+1,len(ids)-1):
                right=ids[k];end=ids[k-1]
                if right-left>cfg.maximum_detour_frames+1 or not np.all(period[left:right+1]==period[left]):break
                if np.linalg.norm(ball[right]-ball[end])*fps/(right-end)<=cfg.speed_limit:continue
                bridge=(ball[right]-ball[left])*fps/(right-left)
                if np.linalg.norm(bridge)>cfg.speed_limit:continue
                before=ids[i-2] if i>=2 else None;after=ids[k+1]
                if before is None or period[before]!=period[left] or period[after]!=period[right]:continue
                incoming=(ball[left]-ball[before])*fps/(left-before);outgoing=(ball[after]-ball[right])*fps/(after-right)
                if max(np.linalg.norm(incoming-bridge),np.linalg.norm(outgoing-bridge))>cfg.acceleration_scale*(right-left)/fps:continue
                inside=ids[i:k];expected=ball[left]+(ball[right]-ball[left])*(inside-left)[:,None]/(right-left)
                if not len(inside) or np.any(np.linalg.norm(ball[inside]-expected,axis=1)<=cfg.corridor_radius):continue
                quarantine[inside]=True;filtered[inside]=False;break
    result=ball.copy();result[~filtered]=np.nan;estimated=np.zeros(n,bool);uncertainty=np.full(n,np.inf);uncertainty[filtered]=0.;ids=np.flatnonzero(filtered)
    for i in range(1,len(ids)-2):
        left,right=ids[i:i+2];width=right-left-1
        if width<1 or width>gap_frames or not np.all(period[left:right+1]==period[left]):continue
        before,after=ids[i-1],ids[i+2]
        if period[before]!=period[left] or period[after]!=period[left]:continue
        dt=(right-left)/fps;v=(ball[right]-ball[left])/dt
        if np.linalg.norm(v)>cfg.speed_limit:continue
        incoming=(ball[left]-ball[before])*fps/(left-before);outgoing=(ball[after]-ball[right])*fps/(after-right)
        t=np.arange(1,right-left)/fps
        # Endpoint velocity disagreement grows uncertainty through the gap.
        radius=np.minimum(t,dt-t)*max(np.linalg.norm(v-incoming),np.linalg.norm(v-outgoing))+cfg.acceleration_scale*t*(dt-t)/2
        good=radius<=cfg.interpolation_radius;f=np.arange(left+1,right)[good]
        result[f]=ball[left]+v*(f-left)[:,None]/fps;estimated[f]=True;uncertainty[f]=radius[good]
    return result,filtered,estimated,uncertainty,quarantine

def predict_reliable(inputs,base,cfg):
    ball,real,estimated,uncertainty,quarantine=supported_path(inputs,cfg,base.gap_frames);period=inputs['period'];n=len(ball);d,slots=distances(inputs,ball)
    finite=np.isfinite(d).all(1);candidate=np.where(d[:,0]<d[:,1],0,1);separation=np.zeros(n);np.subtract(d[:,0],d[:,1],out=separation,where=finite)
    usable=finite&(np.min(d,axis=1)<=base.radius)&(np.abs(separation)>=base.margin)&(real|(estimated if cfg.interpolation_votes else False))
    height=np.asarray(inputs.get('ball_height',np.full(n,np.nan)),float);airborne=np.zeros(n,bool)
    if cfg.suppress_airborne:airborne=real&np.isfinite(height)&(height>cfg.reachable_height);usable&=~airborne
    if cfg.require_detected_receiver:
        current=slots[np.arange(n),candidate];known=current>=0;detected=np.zeros(n,bool);detected[known]=inputs['player_detected'][np.flatnonzero(known),current[known]];usable&=detected
    labels=np.full(n,'X',dtype='<U1');reasons=np.full(n,'unknown_measurement',dtype='<U48');owner='X';pending=-1;pending_slot=-1;count=0;first=0;last_support=-10**9;previous=0;hold=max(1,round(base.hold_frames*cfg.hold_fraction));estimate_acquisitions=0;bridged_acquisitions=0;pending_votes=[]
    for f in range(n):
        if period[f] not in (1,2):owner='X';pending=-1;count=0;previous=0;continue
        if period[f]!=previous:owner='X';pending=-1;count=0;last_support=-10**9
        previous=period[f]
        if usable[f]:
            team=int(candidate[f]);slot=int(slots[f,team])
            if team!=pending or slot!=pending_slot:pending=team;pending_slot=slot;count=0;first=f;pending_votes=[]
            count+=1;pending_votes.append(f)
            if count>=base.confirmation_frames:
                new='H' if team==0 else 'A'
                if new!=owner:
                    estimate_acquisitions+=int(np.any(estimated[pending_votes]));bridged_acquisitions+=int(np.any(estimated[first:f+1]))
                owner=new;labels[first:f+1]=owner;reasons[first:f+1]='confirmed_supported_receiver';last_support=f
        elif not (estimated[f] and not airborne[f] and finite[f] and pending==candidate[f] and pending_slot==slots[f,pending] and d[f,pending]<=base.radius):pending=-1;count=0;pending_votes=[]
        if f-last_support>hold:owner='X'
        labels[f]=owner
        if reasons[f]=='unknown_measurement':reasons[f]='airborne_no_new_acquisition' if airborne[f] else 'quarantined_detour' if quarantine[f] else 'bounded_owner_hold' if owner!='X' else 'unknown_measurement'
    diagnostics={'quarantined_observed_points':int(quarantine.sum()),'bounded_interpolated_frames':int(estimated.sum()),'airborne_acquisition_veto_frames':int(airborne.sum()),
        'acquisitions_using_interpolation_votes':estimate_acquisitions,'acquisitions_spanning_estimated_gaps':bridged_acquisitions,'height_is_provider_estimate':True,'claims_hand_foot_or_head_contact':False}
    return labels,reasons,diagnostics

def learn_scales(training):
    speeds=[];accelerations=[];residuals=[];heights=[];gap_lengths=[]
    for x,target in training:
        b=x['ball'];real=x['ball_observed']&np.isfinite(b).all(1);period=x['period'];fps=float(x['fps']);ids=np.flatnonzero(real)
        adjacent=ids[1:]-ids[:-1]==1;same=period[ids[1:]]==period[ids[:-1]];step=ids[1:][adjacent&same];speeds.extend(np.linalg.norm(b[step]-b[step-1],axis=1)*fps)
        centres=ids[1:-1];good=(ids[1:-1]-ids[:-2]==1)&(ids[2:]-ids[1:-1]==1)&(period[ids[:-2]]==period[ids[2:]]);j=centres[good]
        residual=np.linalg.norm(b[j]-(b[j-1]+b[j+1])/2,axis=1);residuals.extend(residual);accelerations.extend(2*residual*fps*fps)
        if 'ball_height' in x:
            d,_=distances(x);own=np.where(target=='H',d[:,0],d[:,1]);eligible=real&np.isin(target,('H','A'))&np.isfinite(x['ball_height'])&np.isfinite(own)
            cutoff=np.quantile(own[eligible],.5) if np.any(eligible) else 0;heights.extend(x['ball_height'][eligible&(own<=cutoff)])
        gap_lengths.extend((ids[1:]-ids[:-1]-1)[(ids[1:]-ids[:-1]>1)&same])
    if not speeds or not residuals:raise ValueError('Insufficient measured external trajectories')
    return {'speed_limit':float(max(np.quantile(speeds,.995),1e-3)),'corridor_radius':float(max(np.quantile(residuals,.99)*2,1e-3)),
        'maximum_detour_frames':int(max(1,np.quantile(gap_lengths,.25))) if gap_lengths else 1,'acceleration_scale':float(max(np.quantile(accelerations,.75),1e-3)),
        'interpolation_radius':float(max(np.quantile(residuals,.99)*4,1e-3)),'reachable_height':float(max(np.quantile(heights,.95),1e-3)) if heights else float('1e6')}
