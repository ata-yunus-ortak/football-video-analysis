"""Deterministic crop geometry; no resize or invented negative ball labels."""
import math


def tile_windows(width,height,size,overlap):
    if any(type(v) is not int or v<1 for v in (width,height,size)) or size>min(width,height):
        raise ValueError('Positive dimensions and fitting tile required')
    if not math.isfinite(overlap) or not 0<=overlap<1:raise ValueError('Overlap in [0,1) required')
    step=size-int(size*overlap)
    def starts(length):
        values=[0]
        while values[-1]+size<length:
            values.append(min(values[-1]+step,length-size))
        return values
    return [(x,y,x+size,y+size) for y in starts(height) for x in starts(width)]


def crop_boxes(boxes,window):
    x0,y0,x1,y1=window;out=[]
    for x,y,w,h in boxes:
        a,b=max(x,x0),max(y,y0);c,d=min(x+w,x1),min(y+h,y1)
        if c>a and d>b:out.append([a-x0,b-y0,c-a,d-b])
    return out


def positive_window(box,width,height,size,rng):
    x,y,w,h=box
    if not all(math.isfinite(v) for v in box) or min(w,h)<=0:
        raise ValueError('Finite positive reference box required')
    lo_x=max(0,math.ceil(x+w-size));hi_x=min(width-size,math.floor(x))
    lo_y=max(0,math.ceil(y+h-size));hi_y=min(height-size,math.floor(y))
    if lo_x>hi_x or lo_y>hi_y:raise ValueError('Reference does not fit an in-image crop')
    a=int(rng.integers(lo_x,hi_x+1));b=int(rng.integers(lo_y,hi_y+1))
    return a,b,a+size,b+size
