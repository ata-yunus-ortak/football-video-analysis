import unittest
from tools.control_reference_check import check


class ReferenceCheckTests(unittest.TestCase):
    def inputs(self):
        doc={'provided_fixture_used':False,'source_kind':'permitted_external_video','reference_origin':'external_human_review',
             'review_attestation':True,'game_id':'2','split':'train','video_sha256':'a'*64,'preview_sha256':'b'*64,
             'reviewed_event_kinds':['touch'],'coverage_s':[[0,1]],'events':[]}
        pack={'provided_fixture_used':False,'predictions_displayed':False,'clips':[{'sequence':'external','game_id':'2','split':'train',
            'video_sha256':'a'*64,'preview_sha256':'b'*64,'duration_s':10}]}
        return doc,pack,{'splits':{'train':['2'],'validation':['3'],'recheck':['5']}}

    def test_reviewed_negative_interval_valid_but_not_accuracy_certification(self):
        report=check(*self.inputs());self.assertEqual(report['events'],0)
        self.assertTrue(report['schema_and_provenance_valid']);self.assertFalse(report['independent_accuracy_certified'])

    def test_wrong_video_game_preview_or_prediction_overlay_rejected(self):
        for field,value in [('video_sha256','c'*64),('game_id','3'),('preview_sha256','c'*64),('review_attestation',False),('coverage_s',[[0,11]])]:
            d,p,s=self.inputs();d[field]=value
            with self.assertRaises(ValueError):check(d,p,s)
        d,p,s=self.inputs();p['predictions_displayed']=True
        with self.assertRaises(ValueError):check(d,p,s)
