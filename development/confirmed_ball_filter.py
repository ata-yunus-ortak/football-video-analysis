"""Offline, bounded-lookahead confirmation of real ball detections only."""
from development.ball_tracking import TemporalBallTracker


def filter_packets(packets, config):
    if not packets:return []
    source=packets[0]['source_id']
    tracker=TemporalBallTracker(source,config)
    measured=[];confirmed=set();first={}
    for index,packet in enumerate(packets):
        if packet['source_id']!=source:raise ValueError('Mixed image sources')
        raw={r['detection_id']:r for r in packet['objects'] if r['kind']=='ball_candidate'}
        if len(raw)!=sum(r['kind']=='ball_candidate' for r in packet['objects']):
            raise ValueError('Duplicate detection identity')
        events=tracker.consume(packet)
        rows=[]
        for track in events['tracks']:
            if not track['measurement']:continue
            row=raw[track['detection_id']]
            if track['predicted_position_px'] is not None or row['image_xy_px']!=track['measured_position_px']:
                raise ValueError('Forecast cannot become a measurement')
            key=track['track_id'];first.setdefault(key,index)
            if track['state']=='observed':
                if key not in confirmed and index-first[key]>config.confirmation_observations-1:
                    raise ValueError('Confirmation lookahead exceeded')
                confirmed.add(key)
            rows.append((key,row))
        measured.append(rows)
    return [[{**row,'confirmation_track_id':key,'temporal_confirmation':'bounded_lookahead',
              'confirmation_max_future_frames':config.confirmation_observations-1}
             for key,row in rows if key in confirmed] for rows in measured]
