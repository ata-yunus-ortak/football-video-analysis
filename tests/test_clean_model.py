import json,tempfile,unittest
from pathlib import Path
import numpy as np
from clean_model.atd import load
from clean_model.decoder import DecoderConfig,predict
from clean_model.run import run

class CleanTests(unittest.TestCase):
    def test_atd_speed_is_not_ball_height(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);meta=root/'meta.xml';raw=root/'raw.txt'
            meta.write_text('<main><Team id="h"/><Team id="a"/><Player teamId="h"/><Player teamId="a"/></main>')
            raw.write_text('1:0.2,0.3,999;0.7,0.6,999:0.21,0.31,999\n2:nan,nan,nan;0.7,0.6,999:nan,nan,nan\n')
            x=load(meta,raw,2,25,[100,60]);np.testing.assert_allclose(x['ball'][0],[21,18.6]);self.assertFalse(x['ball_observed'][1]);self.assertNotIn('ball_height',x)
    def test_no_measurement_never_becomes_a_guessed_owner(self):
        x={'players':np.full((12,2,2),np.nan),'ball':np.full((12,2),np.nan),'ball_observed':np.zeros(12,bool),'teams':np.array([0,1]),'period':np.ones(12,int)}
        labels,_,_=predict(x,DecoderConfig(2,.2,2,2,3));self.assertTrue(np.all(labels=='X'))
    def test_temporal_confirmation_backdates_only_supported_run(self):
        x={'players':np.tile([[10.,10.],[80.,50.]],(12,1,1)),'ball':np.tile([10.2,10.],(12,1)),'ball_observed':np.ones(12,bool),'teams':np.array([0,1]),'period':np.ones(12,int)}
        x['ball'][7:]=np.nan;x['ball_observed'][7:]=False;labels,_,_=predict(x,DecoderConfig(2,.2,3,0,2));self.assertTrue(np.all(labels[:7]=='H'));self.assertEqual(labels[-1],'X')
    def test_changed_source_freeze_fails_before_input_access(self):
        with tempfile.TemporaryDirectory() as folder:
            model=Path(folder)/'model.json';model.write_text(json.dumps({'source_hashes':{'atd.py':'invalid'},'provided_fixture_used_for_selection':False}))
            with self.assertRaises(ValueError):run('nonexistent.xml','nonexistent.txt',model,Path(folder)/'out')

if __name__=='__main__':unittest.main()
