import copy
import unittest
from development.transition_benchmark import evaluate_events,validate_reference


class ReferenceScopeTests(unittest.TestCase):
    def doc(self):
        return {'provided_fixture_used':False,'source_kind':'permitted_external_video','reference_origin':'external_human_review',
            'split':'train','game_id':'2','video_sha256':'a'*64,'coverage_s':[[0,1],[1.1,2]],'reviewed_event_kinds':['touch'],
            'events':[{'id':'a','kind':'touch','earliest_s':1.15,'latest_s':1.15,'team':None}]}

    def test_tolerance_cannot_bridge_unreviewed_gap(self):
        r=evaluate_events([{'kind':'touch','time_s':.95}],self.doc(),.5)
        self.assertEqual((r['matched'],r['missed'],r['extra']),(0,1,1))

    def test_unreviewed_kinds_are_not_false_positives(self):
        r=evaluate_events([{'kind':'pass','time_s':.5}],self.doc())
        self.assertEqual(r['extra'],0);self.assertEqual(r['unscored_predictions'],1)

    def test_empty_or_inconsistent_review_scope_rejected(self):
        plan={'splits':{'train':['2'],'validation':['3'],'recheck':['5']}}
        for mutate in (lambda d:d.update(coverage_s=[]),lambda d:d.update(reviewed_event_kinds=[]),
                       lambda d:d['events'][0].update(earliest_s=2,latest_s=2),
                       lambda d:d.update(reviewed_event_kinds=['pass'])):
            doc=self.doc();mutate(doc)
            with self.assertRaises(ValueError):validate_reference(doc,plan)
