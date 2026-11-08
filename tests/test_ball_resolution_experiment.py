import unittest
from tools.ball_resolution_experiment import box_summary, gate


class ResolutionExperimentTests(unittest.TestCase):
    def test_one_to_one_and_unannotated_accounting(self):
        p={'box_xyxy':[0,0,10,10],'confidence':.8}
        summary=box_summary([{'game':'4','predictions':[p,p],'references':[{'box_xyxy':[0,0,10,10]}]},
                             {'game':'4','predictions':[p],'references':[]}])['4']
        self.assertEqual(summary['matched'],1)
        self.assertEqual(summary['unmatched_predictions'],2)
        self.assertEqual(summary['predictions_on_unannotated_frames'],1)

    def test_each_game_must_pass_both_gates(self):
        base={g:{'references':20,'matched':10,'unmatched_predictions':4} for g in ('4','6','9')}
        candidate={g:{'matched':12,'unmatched_predictions':5} for g in base}
        self.assertTrue(gate(base,candidate))
        candidate['9']['unmatched_predictions']=6
        self.assertFalse(gate(base,candidate))
        self.assertFalse(gate({},{}))
