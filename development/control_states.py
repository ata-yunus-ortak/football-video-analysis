"""Step 1: control state is separate from touch and team possession."""
from enum import Enum
from dataclasses import dataclass
import math


class State(str,Enum):
    CONTROL='control'
    FLIGHT='flight'
    CONTESTED='contested'
    UNKNOWN='unknown'
    DEAD='dead_ball'


@dataclass(frozen=True)
class ControlConfig:
    confirmation_s:float=.12
    proximity_heights:float=.35
    separation_heights:float=.12
    relative_speed_heights_s:float=2.
    flight_speed_heights_s:float=3.
    turn_cosine:float=0.
    confidence:float=.5
    max_flight_s:float=3.
    stationary_speed_heights_s:float=.1
    stationary_s:float=.4
    restart_speed_heights_s:float=1.

    def __post_init__(self):
        for k,v in vars(self).items():
            if not math.isfinite(v) or (k!='turn_cosine' and v<=0):raise ValueError('Finite positive control settings required')
        if not -1<=self.turn_cosine<=1 or self.confidence>1:raise ValueError('Bounded cosine/confidence required')


def empty(frame,reason):
    return {'frame':frame,'state':State.UNKNOWN.value,'team':'X','owner_id':None,
            'touch_candidate':None,'reason':reason,'confirmed_at_frame':None,
            'selected_release':False}
