"""Automatic person-box context for foot-like ball candidates, not a foot classifier.

Only persistent, elongated, person-attached candidates can be withheld. Merely
being near feet is never enough. References, roles and teams are not inputs.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class FootContextConfig:
    lower_body_fraction: float
    minimum_box_containment: float
    elongation_ratio: float
    relative_position_tolerance: float
    relative_motion_tolerance: float
    minimum_person_step_fraction: float
    attached_observations: int
    independent_observations: int

    def __post_init__(self):
        for name,value in vars(self).items():
            if name.endswith('observations'):
                if type(value) is not int or value < 2: raise ValueError('Multiple context observations required')
            elif not math.isfinite(value) or value<=0: raise ValueError('Positive explicit context parameters required')
        if not 0<self.lower_body_fraction<1 or self.minimum_box_containment>1 or self.elongation_ratio<=1:
            raise ValueError('Valid lower body, containment and elongation parameters required')


class BallFootContext:
    def __init__(self, config):
        self.cfg,self.previous,self.history=config,None,{}

    def annotate(self, packet, reset=False):
        frame,time,epoch=packet['source_frame'],packet['video_time_s'],packet['camera_epoch']
        signature=(packet['fps'],tuple(packet['image_size_px']),epoch)
        if self.previous is None or reset or self.previous[0]+1!=frame or time<=self.previous[1] or time-self.previous[1]>1.5/packet['fps'] or signature!=self.previous[2]:
            self.history={}
        people=[r for r in packet['objects'] if r['kind']=='person_candidate' and r.get('image_track_id')]
        person_counts={p['image_track_id']:sum(q['image_track_id']==p['image_track_id'] for q in people) for p in people}
        people=[p for p in people if person_counts[p['image_track_id']]==1]
        next_history={};suspicious=0
        for ball in packet['objects']:
            if ball['kind']!='ball_candidate':continue
            bx,by,br,bb=ball['box_xyxy_px'];x,y=ball['image_xy_px'];area=(br-bx)*(bb-by)
            elongation=max((br-bx)/(bb-by),(bb-by)/(br-bx));matches=[]
            for person in people:
                px,py,pr,pb=person['box_xyxy_px'];w,h=pr-px,pb-py;lower=py+self.cfg.lower_body_fraction*h
                contained=max(0,min(br,pr)-max(bx,px))*max(0,min(bb,pb)-max(by,lower))/area
                if contained>=self.cfg.minimum_box_containment:
                    matches.append((person,[(x-px)/w,(y-py)/h],[(px+pr)/2,pb],h))
            context={'foot_zone_overlap':bool(matches),'context_evaluable':bool(people),
                     'foot_like_suspected':False,'withhold_unprotected_track':False,
                     'independent_motion_evidence':bool(people) and not matches,
                     'attached_observations':0,'reason':'proximity_alone_does_not_reject'}
            if len(matches)==1:
                person,relative,foot,height=matches[0];key=person['image_track_id'];old=self.history.get(key,[])
                nearby=sorted((math.dist(relative,r['relative']),i,r) for i,r in enumerate(old))
                # Do not combine the histories of two candidates around one person's feet.
                unique=bool(nearby) and (len(nearby)==1 or nearby[1][0]-nearby[0][0]>self.cfg.relative_position_tolerance)
                attached=1
                if unique and nearby[0][0]<=self.cfg.relative_position_tolerance:
                    prior=nearby[0][2]
                    residual=math.dist([x-prior['point'][0],y-prior['point'][1]],
                                       [foot[0]-prior['foot'][0],foot[1]-prior['foot'][1]])/height
                    moving=math.dist(foot,prior['foot'])/height>=self.cfg.minimum_person_step_fraction
                    if residual<=self.cfg.relative_motion_tolerance and moving:
                        attached=prior['attached']+1
                    elif residual>self.cfg.relative_motion_tolerance:
                        context['independent_motion_evidence']=True
                context.update(person_track_id=key,attached_observations=attached,
                    foot_like_suspected=elongation>=self.cfg.elongation_ratio,
                    withhold_unprotected_track=(elongation>=self.cfg.elongation_ratio and attached>=self.cfg.attached_observations))
                if context['withhold_unprotected_track']:
                    context['reason']='persistent_elongated_person_attached_candidate';suspicious+=1
                next_history.setdefault(key,[]).append({'relative':relative,'point':[x,y],'foot':foot,'attached':attached})
            elif len(matches)>1:context['reason']='overlapping_people_context_ambiguous'
            ball['ball_context']=context
        self.previous=(frame,time,signature);self.history=next_history
        return {'schema':'ball-foot-context-v1','withheld_candidates':suspicious,'foot_classification_validated':False}
