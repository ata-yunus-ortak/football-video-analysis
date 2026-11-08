"""Step 6: tags constrain search; measured stop signal is independently required."""
from development.control_decoder import continuous
from development.set_piece_dead_ball import restart_kind


def dead_candidates(rows,tags,signals,cfg):
    index={}
    for s in signals:
        if s.get('origin')!='automatic_image_measurement' or s.get('measurement') is not True or s.get('verified') is not True:
            raise ValueError('Verified measured image stop signal required')
        if s['kind'] not in ('ball_exit','referee_stop'):raise ValueError('Unsupported stop evidence')
        key=(s['source_id'],s['epoch'],s['frame'])
        if key in index:raise ValueError('Duplicate stop signal')
        index[key]=s
    mask=[False]*len(rows);start=None;confirmed=False;motion_start=None;events=[]
    for i,r in enumerate(rows):
        active=any(t['source_id']==r['source_id'] and t['epoch']==r['epoch'] and
            t['start_s']<=r['time_s']<=t['end_s'] and restart_kind(t) is not None for t in tags)
        if not active or not r['measured'] or not r['motion_valid'] or (i and not continuous(rows[i-1],r)):
            start=None;confirmed=False;motion_start=None;continue
        if (r['source_id'],r['epoch'],r['frame']) in index:
            start=i;confirmed=False;motion_start=None
        if start is None:continue
        if not confirmed:
            if r['speed']>cfg.stationary_speed_heights_s:start=None;continue
            if r['time_s']-rows[start]['time_s']+1/r['fps']>=cfg.stationary_s-1e-9:
                confirmed=True
                for k in range(start,i+1):mask[k]=True
                events.append({'kind':'stop','time_s':rows[start]['time_s'],'frame':rows[start]['frame'],
                    'team':None,'owner_id':None,'confirmed_at_frame':r['frame'],'candidate_only':True})
        else:
            if r['speed']>=cfg.restart_speed_heights_s:
                if motion_start is None:motion_start=i
                if r['time_s']-rows[motion_start]['time_s']+1/r['fps']>=cfg.confirmation_s-1e-9:
                    events.append({'kind':'restart','time_s':rows[motion_start]['time_s'],'frame':rows[motion_start]['frame'],
                        'team':None,'owner_id':None,'confirmed_at_frame':r['frame'],'candidate_only':True})
                    start=None;confirmed=False;motion_start=None
            elif motion_start is not None:
                # Ambiguous moving frames remain unknown, not retrospectively dead.
                start=None;confirmed=False;motion_start=None
            else:mask[i]=True
    return mask,events
