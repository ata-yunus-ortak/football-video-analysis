"""Measured geometry plus bounded-lookahead confirmation, no reference inputs."""
from dataclasses import replace
import numpy as np
from development.ball_candidate_filter import features,FEATURE_NAMES as GEOMETRY
from development.confirmed_ball_filter import filter_packets
from development import learned_dead_ball as logistic

FEATURE_NAMES=GEOMETRY+['confirmed_2','confirmed_3','confirmed_5']


def extract(packets,base):
    confirmed=[filter_packets(packets,replace(base,confirmation_observations=n)) for n in (2,3,5)]
    result=[]
    for i,packet in enumerate(packets):
        ids=[{r['detection_id'] for r in rows[i]} for rows in confirmed]
        people=[r['box_xyxy_px'] for r in packet['objects'] if r['kind']=='person_candidate']
        balls=[r for r in packet['objects'] if r['kind']=='ball_candidate']
        result.append(np.asarray([features(r['box_xyxy_px'],r['confidence'],people,packet['image_size_px'])+
            [float(r['detection_id'] in s) for s in ids] for r in balls]).reshape(-1,len(FEATURE_NAMES)))
    return result


def fit(raw,target,weights,l2,temporal=True):
    names=FEATURE_NAMES if temporal else GEOMETRY
    if np.asarray(raw).ndim!=2 or raw.shape[1]!=len(names) or set(np.asarray(target).tolist())!={0,1}:
        raise ValueError('Feature schema and both training classes required')
    model=logistic.fit(raw,target,weights,l2)
    return {**model,'feature_names':names,'model_family':'temporal-ball-filter-v1'}


def probability(raw,model):
    names=model['feature_names']
    if model['model_family']!='temporal-ball-filter-v1' or names not in (FEATURE_NAMES,GEOMETRY):
        raise ValueError('Temporal feature schema required')
    raw=np.asarray(raw)
    if raw.ndim!=2 or raw.shape[1]!=len(names):raise ValueError('Feature width differs')
    return logistic.sigmoid(logistic.design(raw,np.asarray(model['median']),np.asarray(model['scale']))@np.asarray(model['coefficients']))
