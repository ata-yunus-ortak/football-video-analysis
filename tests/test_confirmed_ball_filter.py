from dataclasses import replace
import unittest
from test_ball_tracking import CONFIG,packet
from development.confirmed_ball_filter import filter_packets


def frames(points):
    return [{**packet(i,p),'source_id':'A'} for i,p in enumerate(points)]


class ConfirmedFilterTests(unittest.TestCase):
    def test_confirmed_track_keeps_initial_measurements_without_forecasts(self):
        data=frames([[(100,100)],[(105,100)],[(110,100)],[],[(120,100)]])
        out=filter_packets(data,CONFIG)
        self.assertEqual([len(r) for r in out],[1,1,1,0,1])
        self.assertEqual(out[0][0]['box_xyxy_px'],data[0]['objects'][0]['box_xyxy_px'])
        self.assertNotIn('temporal_confirmation',data[0]['objects'][0])

    def test_single_frame_false_candidate_and_unconfirmed_gap_are_removed(self):
        data=frames([[(100,100)],[],[(100,100)],[(105,100)]])
        self.assertEqual(filter_packets(data,CONFIG),[[],[],[],[]])

    def test_camera_cut_cannot_confirm_old_candidate(self):
        data=frames([[(100,100)],[(105,100)],[(110,100)]])
        data[-1]['camera_epoch']=1
        self.assertEqual(filter_packets(data,CONFIG),[[],[],[]])

    def test_mixed_sources_and_duplicate_ids_rejected(self):
        data=frames([[(100,100)],[(105,100)]])
        data[1]['source_id']='B'
        with self.assertRaises(ValueError):filter_packets(data,CONFIG)
        data=frames([[(100,100)]])
        data[0]['objects']*=2
        with self.assertRaises(ValueError):filter_packets(data,CONFIG)
