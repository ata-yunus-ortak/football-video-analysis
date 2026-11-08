"""Step 4: offline control confirmation with separately timestamped decisions."""
import math
from development.control_states import empty,State


def continuous(a,b):
    return (a['source_id']==b['source_id'] and a['epoch']==b['epoch'] and a['period']==b['period']
            and a['frame']+1==b['frame'] and a['fps']==b['fps']
            and .5/b['fps']<=b['time_s']-a['time_s']<=1.5/b['fps'])


def decode(rows,cfg,*,backdating=True,flight=True,dead=None):
    dead=[False]*len(rows) if dead is None else dead
    if len(dead)!=len(rows):raise ValueError('Aligned dead-ball evidence required')
    for r in rows:
        if not math.isfinite(r['fps']) or r['fps']<=0 or not math.isfinite(r['time_s']) or r['time_s']<0:raise ValueError('Valid image clock required')
        c=r['candidate']
        if c is not None and (not r['measured'] or r['contested'] or r['flight'] or c['team'] not in ('H','A') or not c['owner_id']):
            raise ValueError('Control requires unambiguous measured player evidence')
    result=[empty(r['frame'],'no_confirmed_control') for r in rows]
    for i,r in enumerate(rows):
        result[i].update(time_s=r['time_s'],touch_candidate=r['touch_candidate'])
        if dead[i]:result[i].update(state=State.DEAD.value,team='D',reason='tag_and_measured_stop')
        elif not r['measured']:result[i]['reason']='ball_unobserved'
        elif r['contested']:result[i].update(state=State.CONTESTED.value,reason='competing_control_evidence')
        elif r['flight']:result[i].update(state=State.FLIGHT.value,reason='observed_ball_flight')
    i=0
    while i<len(rows):
        candidate=rows[i]['candidate']
        if candidate is None or dead[i]:i+=1;continue
        j=i+1
        while j<len(rows) and not dead[j] and rows[j]['candidate']==candidate and continuous(rows[j-1],rows[j]):j+=1
        needed=max(2,math.ceil(cfg.confirmation_s*rows[i]['fps']-1e-9))
        if j-i>=needed:
            confirmation=i+needed-1
            for k in range(i if backdating else confirmation,j):
                result[k].update(state=State.CONTROL.value,team=candidate['team'],owner_id=candidate['owner_id'],
                    confirmed_at_frame=rows[max(k,confirmation)]['frame'],reason='confirmed_measured_control')
        i=j
    last=None;flight_start=None;events=[]
    for i,(r,out) in enumerate(zip(rows,result)):
        if r['measured'] and r['touch_candidate'] is not None and not dead[i]:
            events.append({'kind':'touch','time_s':r['time_s'],'frame':r['frame'],
                'team':r['candidate']['team'] if r['candidate'] else None,'owner_id':r['touch_candidate'],
                'confirmed_at_frame':r['frame'],'candidate_only':True})
        if i and not continuous(rows[i-1],r):last=None;flight_start=None
        if out['state']==State.CONTROL.value:
            if last is not None and last['owner_id']!=out['owner_id']:
                events.append({'kind':'pass' if last['team']==out['team'] else 'turnover','time_s':r['time_s'],
                    'frame':r['frame'],'team':out['team'],'owner_id':out['owner_id'],'from_owner_id':last['owner_id'],
                    'confirmed_at_frame':out['confirmed_at_frame'],'candidate_only':True})
            last=out;flight_start=None
        elif out['state']==State.FLIGHT.value and flight and last is not None:
            if flight_start is None:flight_start=r['time_s']
            if r['time_s']-flight_start<=cfg.max_flight_s:
                out.update(team=last['team'],reason='bounded_team_continuity_during_observed_flight')
            else:last=None;flight_start=None
        else:last=None;flight_start=None
    # Endpoints are inferred observed support, never an interpolated contact.
    for i,out in enumerate(result):
        if out['state']!=State.CONTROL.value:continue
        before=result[i-1] if i and continuous(rows[i-1],rows[i]) else None
        after=result[i+1] if i+1<len(rows) and continuous(rows[i],rows[i+1]) else None
        if before is None or before['owner_id']!=out['owner_id']:
            events.append({'kind':'control_start','time_s':out['time_s'],'frame':out['frame'],'team':out['team'],
                'owner_id':out['owner_id'],'confirmed_at_frame':out['confirmed_at_frame'],
                'left_censored':before is None or before['state']=='unknown','candidate_only':True})
        if after is None or after['owner_id']!=out['owner_id']:
            events.append({'kind':'control_end','time_s':out['time_s']+1/rows[i]['fps'],'frame':out['frame']+1,
                'team':out['team'],'owner_id':out['owner_id'],
                'confirmed_at_frame':max(out['confirmed_at_frame'],after['confirmed_at_frame'] or rows[i+1]['frame']) if after is not None else None,
                'right_censored':after is None or after['state']=='unknown','candidate_only':True})
    return result,sorted(events,key=lambda e:(e['time_s'],e['kind']))
