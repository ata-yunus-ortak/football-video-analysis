"""Generic measurement decoder with external-data configuration, no target input."""
from dataclasses import dataclass,asdict
import numpy as np

@dataclass(frozen=True)
class DecoderConfig:
    radius:float
    margin:float
    confirmation_frames:int
    gap_frames:int
    hold_frames:int
    def __post_init__(self):
        if not np.isfinite(self.radius) or self.radius<=0 or not np.isfinite(self.margin) or self.margin<0:raise ValueError('Invalid distance configuration')
        if any(type(v) is not int or v<0 for v in (self.confirmation_frames,self.gap_frames,self.hold_frames)) or self.confirmation_frames<1:raise ValueError('Invalid frame configuration')

def bounded_fill(ball,observed,period,gap_frames):
    result=np.array(ball,float,copy=True);result[~observed]=np.nan;estimated=np.zeros(len(ball),bool);ids=np.flatnonzero(observed&np.isfinite(ball).all(1))
    for a,b in zip(ids,ids[1:]):
        if 1<b-a<=gap_frames+1 and period[a] in (1,2) and np.all(period[a:b+1]==period[a]):
            f=np.arange(a+1,b);result[f]=ball[a]+(ball[b]-ball[a])*(f-a)[:,None]/(b-a);estimated[f]=True
    return result,estimated

def distances(inputs,ball=None):
    ball=inputs['ball'] if ball is None else ball;d=np.linalg.norm(inputs['players']-ball[:,None,:],axis=2);d[~np.isfinite(d)]=np.inf
    nearest=np.full((len(ball),2),np.inf);slot=np.full((len(ball),2),-1,int)
    for team in (0,1):
        ids=np.flatnonzero(inputs['teams']==team)
        if len(ids):
            k=d[:,ids].argmin(1);nearest[:,team]=d[np.arange(len(ball)),ids[k]];slot[:,team]=ids[k]
    return nearest,slot

def predict(inputs,config=None):
    period=inputs['period'];observed=inputs['ball_observed'];n=len(period)
    ball,estimated=bounded_fill(inputs['ball'],observed,period,0 if config is None else config.gap_frames);d,slots=distances(inputs,ball)
    finite=np.isfinite(d).all(1);candidate=np.where(d[:,0]<d[:,1],0,1);labels=np.full(n,'X',dtype='<U1');usable=finite&np.isin(period,(1,2));reasons=np.full(n,'missing_measurement',dtype='<U40')
    if config is None:
        labels[usable]=np.where(candidate[usable]==0,'H','A');reasons[usable]='nearest_team_baseline';return labels,reasons,estimated
    separation=np.zeros(n);np.subtract(d[:,0],d[:,1],out=separation,where=finite)
    usable&=(np.min(d,axis=1)<=config.radius)&(np.abs(separation)>=config.margin)
    owner='X';pending=-1;pending_slot=-1;count=0;first=0;last_support=-10**9;previous_period=0
    for f in range(n):
        if period[f] not in (1,2):owner='X';pending=-1;count=0;previous_period=0;continue
        if period[f]!=previous_period:owner='X';pending=-1;count=0;last_support=-10**9
        previous_period=period[f]
        if usable[f]:
            team=int(candidate[f]);slot=int(slots[f,team])
            if team!=pending or slot!=pending_slot:pending=team;pending_slot=slot;count=0;first=f
            count+=1
            if count>=config.confirmation_frames:
                owner='H' if team==0 else 'A';labels[first:f+1]=owner;reasons[first:f+1]='later_confirmed_continuous_receiver';last_support=f
        else:pending=-1;count=0
        if f-last_support>config.hold_frames:owner='X'
        labels[f]=owner
        if reasons[f]=='missing_measurement' and owner!='X':reasons[f]='bounded_team_continuity'
    return labels,reasons,estimated

def candidate_grid(training):
    radii=[];margins=[];durations=[];gaps=[]
    for inputs,target in training:
        d,_=distances(inputs);known=np.isin(target,('H','A'))&inputs['ball_observed']&np.isfinite(d).all(1)
        own=np.where(target=='H',d[:,0],d[:,1]);other=np.where(target=='H',d[:,1],d[:,0]);radii.extend(own[known].tolist());margins.extend(np.maximum(0,other[known]-own[known]).tolist())
        changes=np.r_[0,np.flatnonzero(target[1:]!=target[:-1])+1,len(target)]
        durations.extend([b-a for a,b in zip(changes,changes[1:]) if target[a] in ('H','A')])
        valid=inputs['ball_observed'];edges=np.r_[0,np.flatnonzero(valid[1:]!=valid[:-1])+1,len(valid)]
        gaps.extend([b-a for a,b in zip(edges,edges[1:]) if not valid[a] and a>0 and b<len(valid)])
    if not radii or not durations:raise ValueError('Insufficient external training targets')
    rs=np.maximum(.01,np.quantile(radii,[.5,.75,.9]));ms=np.maximum(0,np.quantile(margins,[0,.25,.5]));dur=max(1,int(np.quantile(durations,.1)));gap=max(1,int(np.quantile(gaps,.5))) if gaps else 0
    # Fractions of external possession/missing-run lengths, not fixture clocks.
    confirmations=sorted({1,max(1,round(dur*.1)),max(1,round(dur*.25))});holds=sorted({max(1,round(dur*.5)),dur})
    configs=[DecoderConfig(float(r),float(m),int(c),int(gap),int(h)) for r in rs for m in ms for c in confirmations for h in holds]
    unique={tuple(asdict(c).values()):c for c in configs}
    return list(unique.values()),{'radius_quantiles':rs.tolist(),'margin_quantiles':ms.tolist(),'external_short_spell_frames':dur,'external_median_gap_frames':gap,'target_kind':'provider_automatic_proxy'}
