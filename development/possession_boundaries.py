"""Exact observed ownership transitions and explicit gap uncertainty."""
import numpy as np


def transitions(labels,period,frame,fps):
    y,p,f=map(np.asarray,(labels,period,frame))
    if (y.ndim!=1 or p.shape!=y.shape or f.shape!=y.shape or not np.isin(y,('H','A','X')).all()
        or not np.isfinite(fps) or fps<=0 or f.dtype.kind not in 'iu'):
        raise ValueError('Aligned H/A/X and integer source clock required')
    exact=[];uncertain=[];last=None;block=0
    for i in range(len(y)):
        if i==0 or p[i]!=p[i-1] or f[i]!=f[i-1]+1:
            last=None;block+=1
        if p[i] not in (1,2) or y[i]=='X':continue
        if last is not None and y[i]!=y[last]:
            row={'direction':str(y[last]+y[i]),'block':block,'index':i,
                 'earliest_s':float((f[last]+1)/fps),'latest_s':float(f[i]/fps)}
            (exact if i==last+1 else uncertain).append(row)
        last=i
    return exact,uncertain


def match_times(reference,predicted,tolerance):
    """Ordered one-to-one maximum matches, then minimum absolute timing error."""
    if not np.isfinite(tolerance) or tolerance<0:raise ValueError('Nonnegative finite tolerance')
    n,m=len(reference),len(predicted)
    hits=np.zeros((n+1,m+1),int);cost=np.zeros((n+1,m+1));back=np.zeros((n+1,m+1),np.int8)
    for i in range(1,n+1):
        for j in range(1,m+1):
            choices=[(hits[i-1,j],-cost[i-1,j],1),(hits[i,j-1],-cost[i,j-1],2)]
            error=abs(predicted[j-1]-reference[i-1])
            if error<=tolerance+1e-9:choices.append((hits[i-1,j-1]+1,-cost[i-1,j-1]-error,3))
            h,c,k=max(choices);hits[i,j]=h;cost[i,j]=-c;back[i,j]=k
    errors=[];i,j=n,m
    while i and j:
        k=back[i,j]
        if k==3:errors.append(predicted[j-1]-reference[i-1]);i-=1;j-=1
        elif k==1:i-=1
        else:j-=1
    return errors


def evaluate(target,prediction,period,frame,fps,tolerances=(.2,.5,1.,2.)):
    y,p,period,frame=map(np.asarray,(target,prediction,period,frame))
    if p.shape!=y.shape:raise ValueError('Prediction length differs')
    transitions(y,period,frame,fps)
    transitions(p,period,frame,fps)
    # Unknown targets censor blocks; predictions cannot bridge them for credit.
    known=np.isin(y,('H','A')) & np.isin(period,(1,2))
    block=np.cumsum(np.r_[True,(known[1:]!=known[:-1])|(period[1:]!=period[:-1])|(np.diff(frame)!=1)]) if len(y) else np.array([],int)
    groups=[];uncertain_count=0
    for b in np.unique(block[known]):
        ids=np.flatnonzero((block==b)&known)
        truth,_=transitions(y[ids],period[ids],frame[ids],fps)
        pred,uncertain=transitions(p[ids],period[ids],frame[ids],fps);uncertain_count+=len(uncertain)
        for direction in ('HA','AH'):
            groups.append(([r['latest_s'] for r in truth if r['direction']==direction],
                           [r['latest_s'] for r in pred if r['direction']==direction]))
    nr=sum(len(a) for a,b in groups);npred=sum(len(b) for a,b in groups);scores={}
    for tol in tolerances:
        errors=[e for a,b in groups for e in match_times(a,b,tol)];tp=len(errors)
        scores[str(tol)]={'matched':tp,'reference':nr,'predicted':npred,'f1':2*tp/(nr+npred) if nr+npred else None,
            'precision':tp/npred if npred else None,'recall':tp/nr if nr else None,
            'mean_signed_error_s':float(np.mean(errors)) if errors else None,
            'p90_absolute_error_s':float(np.quantile(np.abs(errors),.9)) if errors else None}
    return {'tolerances_s':scores,'uncertain_predicted_changes':uncertain_count,
            'human_ground_truth':False,'provider_proxy_only':True,'D_boundaries_evaluated':False}


def timeline(labels,period,frame,fps):
    """Half-open known-team spells; unknowns never extend ownership."""
    exact,uncertain=transitions(labels,period,frame,fps)
    y,p,f=map(np.asarray,(labels,period,frame));spells=[]
    if len(y):
        cuts=np.r_[0,np.flatnonzero((y[1:]!=y[:-1])|(p[1:]!=p[:-1])|(np.diff(f)!=1))+1,len(y)]
        def adjacent(a,b):
            return 0<=a<len(y) and 0<=b<len(y) and p[a]==p[b] and f[b]==f[a]+1 and y[a] in ('H','A') and y[b] in ('H','A')
        for a,b in zip(cuts[:-1],cuts[1:]):
            if y[a] not in ('H','A') or p[a] not in (1,2):continue
            spells.append({'team':str(y[a]),'period':int(p[a]),'first_frame':int(f[a]),'end_frame_exclusive':int(f[b-1]+1),
                'start_s':float(f[a]/fps),'end_s_exclusive':float((f[b-1]+1)/fps),
                'start_censored':not adjacent(a-1,a),'end_censored':not adjacent(b-1,b)})
    return {'spells':spells,'exact_adjacent_label_changes':exact,'uncertain_change_intervals':uncertain,
            'inferred_not_ground_truth':True,'timestamps_are_source_frame_times':True,'unknown_is_dead_ball':False}
