import copy
import json
from pathlib import Path
import unittest
from development.ball_foot_context import BallFootContext, FootContextConfig
from development.ball_tracking import TemporalBallTracker, BallTrackingConfig

PLAN=json.loads((Path(__file__).resolve().parents[1]/'ball-foot-context-plan.json').read_text())
FOOT=FootContextConfig(**PLAN['foot_context_parameters'])
BALL=BallTrackingConfig(**PLAN['parameters'])


def packet(frame, y=95, elongated=True, moving=True, epoch=0):
    dx=4*frame if moving else 0;x=45+dx
    return {'source_frame':frame,'video_time_s':frame/25,'fps':25,'image_size_px':[1000,500],
        'camera_epoch':epoch,'objects':[
        {'kind':'person_candidate','image_track_id':'person','box_xyxy_px':[dx,0,100+dx,100]},
        {'kind':'ball_candidate','detection_id':f'b{frame}','image_xy_px':[x,y],
         'box_xyxy_px':[x-(6 if elongated else 2),y-2,x+(6 if elongated else 2),y+2],'confidence':.9}]}


class FootContextTests(unittest.TestCase):
    def test_moving_attached_elongated_candidate_is_withheld_but_raw_box_kept(self):
        context,tracker=BallFootContext(FOOT),TemporalBallTracker('source',BALL,FOOT)
        for frame in range(4):
            sample=packet(frame);original=copy.deepcopy(sample['objects'][1]['box_xyxy_px'])
            context.annotate(sample);result=tracker.consume(sample)
        self.assertTrue(sample['objects'][1]['ball_context']['withhold_unprotected_track'])
        self.assertEqual(sample['objects'][1]['box_xyxy_px'],original)
        self.assertFalse(any(r['state']=='predicted' for r in result['tracks']))
        self.assertTrue(any(r['reason']=='suspected_foot_attachment' for r in result['tracks']))

    def test_round_ball_at_feet_is_not_rejected_by_proximity(self):
        context,tracker=BallFootContext(FOOT),TemporalBallTracker('source',BALL,FOOT)
        for frame in range(10):
            sample=packet(frame,elongated=False);context.annotate(sample);result=tracker.consume(sample)
            self.assertFalse(sample['objects'][1]['ball_context']['withhold_unprotected_track'])
        self.assertEqual(result['tracks'][0]['state'],'observed')

    def test_stationary_ambiguous_ball_or_foot_is_not_claimed_to_be_a_foot(self):
        context=BallFootContext(FOOT)
        for frame in range(10):
            sample=packet(frame,moving=False);context.annotate(sample)
            self.assertFalse(sample['objects'][1]['ball_context']['withhold_unprotected_track'])

    def test_previously_independent_ball_can_enter_foot_zone_and_keep_id(self):
        context,tracker=BallFootContext(FOOT),TemporalBallTracker('source',BALL,FOOT)
        identity=None
        for frame in range(6):
            sample=packet(frame,y=68 if frame<2 else 95)
            context.annotate(sample);result=tracker.consume(sample)
            current=next(r for r in result['tracks'] if r['measurement'])
            if identity is None:identity=current['track_id']
            self.assertEqual(current['track_id'],identity)
        self.assertTrue(sample['objects'][1]['ball_context']['withhold_unprotected_track'])
        self.assertEqual(sample['objects'][1]['ball_context']['tracking_decision'],'retained_independent_track')

    def test_camera_cut_and_missing_person_identity_clear_attachment(self):
        context=BallFootContext(FOOT)
        for frame in range(4):context.annotate(packet(frame))
        sample=packet(4,epoch=1);context.annotate(sample)
        self.assertEqual(sample['objects'][1]['ball_context']['attached_observations'],1)
        sample=packet(5,epoch=1);sample['objects'][0]['image_track_id']=None
        context.annotate(sample)
        self.assertFalse(sample['objects'][1]['ball_context']['context_evaluable'])
        self.assertFalse(sample['objects'][1]['ball_context']['withhold_unprotected_track'])
