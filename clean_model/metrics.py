"""Teacher agreement metrics. These are NOT the competition evaluation score."""
import numpy as np

def spans(labels,period,team):
    valid=(labels==team)&np.isin(period,(1,2));changes=np.r_[0,np.flatnonzero((valid[1:]!=valid[:-1])|(period[1:]!=period[:-1]))+1,len(labels)]
    return [(int(a),int(b),int(period[a])) for a,b in zip(changes,changes[1:]) if valid[a]]

def measure(target,pred,period):
    known=np.isin(target,('H','A'))&np.isin(period,(1,2));f1=[]
    for t in ('H','A'):
        tp=np.sum(known&(target==t)&(pred==t));fp=np.sum(known&(target!=t)&(pred==t));fn=np.sum(known&(target==t)&(pred!=t));f1.append(float(2*tp/max(1,2*tp+fp+fn)))
    # Known teacher gaps break spans; they are not invented dead-ball labels.
    p=pred.copy();p[~known]='X';truth=target.copy();truth[~known]='X';fs=[]
    for threshold in (.3,.4,.5,.6,.7):
        hits=ng=npred=0
        for t in ('H','A'):
            gt=spans(truth,period,t);ps=spans(p,period,t);ng+=len(gt);npred+=len(ps);pairs=[]
            # Ordered intervals permit a linear sweep of overlapping candidates.
            i=j=0
            while i<len(gt) and j<len(ps):
                a,b,half=gt[i];c,d,ph=ps[j]
                if half==ph:
                    overlap=max(0,min(b,d)-max(a,c));iou=overlap/(max(b,d)-min(a,c))
                    if iou>=threshold:pairs.append((iou,i,j))
                if b<=d:i+=1
                else:j+=1
            used_g=set();used_p=set()
            for score,i,j in sorted(pairs,reverse=True):
                if i not in used_g and j not in used_p:used_g.add(i);used_p.add(j);hits+=1
        fs.append(2*hits/max(1,ng+npred))
    return {'provider_frame_agreement':float(np.mean(target[known]==pred[known])) if np.any(known) else None,'provider_macro_f1_HA':float(np.mean(f1)),
        'provider_team_spell_iou_f1':float(np.mean(fs)),'known_teacher_frames':int(known.sum()),'human_ground_truth':False,'competition_score':False}
