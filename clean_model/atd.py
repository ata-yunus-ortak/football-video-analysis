"""Strict EPTS x,y,speed reader. No labels, events, video or historical corrections."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np

def load(meta,raw,frames,fps,pitch):
    root=ET.parse(meta).getroot();ids=[t.get('id') for t in root.iter('Team')]
    if len(ids)!=2 or None in ids or len(set(ids))!=2:raise ValueError('Two distinct metadata teams required')
    roster=list(root.iter('Player'))
    if not roster or any(p.get('teamId') not in ids for p in roster):raise ValueError('Unknown team in ATD roster')
    teams=np.array([ids.index(p.get('teamId')) for p in roster],np.int8)
    players=np.full((frames,len(teams),2),np.nan);ball=np.full((frames,2),np.nan);scale=np.asarray(pitch,float)
    if frames<1 or not np.isfinite(fps) or fps<=0 or scale.shape!=(2,) or not np.all(np.isfinite(scale)&(scale>0)):raise ValueError('Invalid reference clock or pitch')
    count=0
    with Path(raw).open(encoding='utf-8-sig') as stream:
        for count,line in enumerate(stream,1):
            parts=line.strip().split(':')
            if len(parts)!=3 or int(parts[0])!=count or count>frames:raise ValueError('ATD IDs must be consecutive from one')
            groups=parts[1].split(';')
            if len(groups)!=len(teams):raise ValueError('Track slot count differs from metadata')
            for slot,group in enumerate(groups+[parts[2]]):
                fields=group.split(',')
                if len(fields)<2:raise ValueError('Malformed ATD coordinate group')
                xy=np.array([float(fields[0]),float(fields[1])])*scale
                if not np.isfinite(xy).all():continue
                if slot==len(teams):ball[count-1]=xy
                else:players[count-1,slot]=xy
    if count!=frames:raise ValueError('ATD count differs from video reference length')
    # The third raw field is SPEED, not HEIGHT. Never reinterpret it as z.
    # Raw ATD has no independent detection-confidence flag: finite means present
    # in the automatic export, not visually verified by this adapter.
    # No hand-labelled half/kickoff/stoppage times enter inference. Long gaps are
    # handled by the already frozen interpolation and possession-hold limits.
    return {'players':players,'ball':ball,'ball_observed':np.isfinite(ball).all(1),
        'player_detected':np.isfinite(players).all(2),'teams':teams,'period':np.ones(frames,np.int8),
        'frame':np.arange(frames),'fps':np.array(float(fps)),'pitch':scale}
