"""Team-level temporal evidence independent of specific kit, fixture or clock."""
from dataclasses import dataclass
import numpy as np
from .decoder import bounded_fill,distances
from .reliability import ReliabilityConfig,supported_path

@dataclass(frozen=True)
class TeamConfirmationConfig:
    measured_votes_only:bool
    height_ceiling:float|None=None
    uncertainty_path:bool=False
    def __post_init__(self):
        if type(self.measured_votes_only) is not bool or type(self.uncertainty_path) is not bool:raise ValueError('Boolean evidence switches required')
        if self.height_ceiling is not None and (not np.isfinite(self.height_ceiling) or self.height_ceiling<=0):raise ValueError('Positive finite automatic height ceiling required')

def predict_team(inputs,base,cfg,scales=None):
    n=len(inputs['period']);period=inputs['period'];real=inputs['ball_observed'];quarantine=np.zeros(n,bool)
    if cfg.uncertainty_path:
        if scales is None:raise ValueError('External training scales required for uncertainty path')
        ball,real,estimated,uncertainty,quarantine=supported_path(inputs,ReliabilityConfig(**scales),base.gap_frames)
    else:ball,estimated=bounded_fill(inputs['ball'],real,period,base.gap_frames)
    d,slots=distances(inputs,ball);finite=np.isfinite(d).all(1);candidate=np.argmin(d,axis=1);margin=np.zeros(n);np.subtract(d[:,0],d[:,1],out=margin,where=finite)
    usable=finite&(np.min(d,axis=1)<=base.radius)&(np.abs(margin)>=base.margin);height=np.asarray(inputs.get('ball_height',np.full(n,np.nan)),float)
    airborne=(real&np.isfinite(height)&(height>cfg.height_ceiling)) if cfg.height_ceiling is not None else np.zeros(n,bool);usable&=~airborne
    labels=np.full(n,'X',dtype='<U1');reasons=np.full(n,'unresolved_team',dtype='<U48');owner='X';pending=-1;first=0;count=0;previous=0;last=-10**9;estimated_votes=0;bridges=0;slots_seen=set();multi_actor_confirmations=0;used_estimate=False
    for f in range(n):
        if period[f] not in (1,2):owner='X';pending=-1;count=0;previous=0;continue
        if period[f]!=previous:owner='X';pending=-1;count=0;last=-10**9
        previous=period[f]
        if usable[f]:
            team=int(candidate[f])
            if pending!=team:pending=team;first=f;count=0;slots_seen=set();used_estimate=False
            # Identity changes inside the same team do not restart the team vote.
            if real[f] or not cfg.measured_votes_only:
                if count==0:first=f
                count+=1;slots_seen.add(int(slots[f,team]));used_estimate|=bool(estimated[f])
            if count>=base.confirmation_frames:
                new='H' if team==0 else 'A'
                if new!=owner:estimated_votes+=int(used_estimate);bridges+=int(np.any(estimated[first:f+1]));multi_actor_confirmations+=int(len(slots_seen)>1)
                owner=new;labels[first:f+1]=owner;reasons[first:f+1]='confirmed_team_temporal_evidence';last=f if real[f] else last
        else:pending=-1;count=0
        if f-last>base.hold_frames:owner='X'
        labels[f]=owner
        if reasons[f]=='unresolved_team':reasons[f]='airborne_team_vote_veto' if airborne[f] else 'bounded_team_hold' if owner!='X' else 'unresolved_team'
    return labels,reasons,{'new_team_acquisitions_with_estimated_votes':estimated_votes,'new_team_acquisitions_spanning_estimated_gaps':bridges,'multi_actor_team_confirmations':multi_actor_confirmations,
        'height_vote_veto_frames':int(airborne.sum()),'quarantined_points':int(quarantine.sum()),'contact_verified':False,'height_is_automatic_estimate':True}
