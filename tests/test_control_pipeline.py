import copy
import unittest
import tempfile
import json
from pathlib import Path
from development.control_states import ControlConfig
from development.control_decoder import decode
from development.control_tag_gate import dead_candidates
from development.control_evidence import EvidenceExtractor
from development.transition_benchmark import validate_reference,evaluate_events
from test_visual_possession import frame
from test_visual_possession import pair
import test_visual_possession as fixtures
from tools.control_experiment import run


CFG=ControlConfig()


def evidence(i,owner='p0',team='H',flight=False,measured=True):
    return {'frame':i,'time_s':i/25,'fps':25,'source_id':'tactical','epoch':0,'period':1,
        'measured':measured,'candidate':{'owner_id':owner,'team':team} if owner else None,
        'touch_candidate':None,'flight':flight,'contested':False,'motion_valid':True,'speed':5. if flight else 0.}


class SixStepTests(unittest.TestCase):
    def test_touch_is_reported_separately_from_control(self):
        row=evidence(0);row['touch_candidate']='p0'
        result,events=decode([row],CFG)
        self.assertEqual(result[0]['team'],'X')
        self.assertEqual([e['kind'] for e in events],['touch'])
        self.assertTrue(events[0]['candidate_only'])

    def test_full_pipeline_and_camera_ablation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);factory=fixtures.VisualRunnerTests();t=factory.make(root,'tactical');b=factory.make(root,'broadcast')
            mapping=root/'pairs.jsonl';mapping.write_text(''.join(json.dumps(pair(frame(f),frame(f,'broadcast')))+'\n' for f in range(8)))
            path=Path(__file__).resolve().parents[1]/'control-development-plan.json'
            result=run(t,path,root/'full',b,mapping)
            self.assertEqual(result['sources']['broadcast'],4)
            self.assertGreater(result['team_counts'].get('A',0),0)
            config=json.loads(path.read_text());config['components']['broadcast']=False
            plan=root/'without-broadcast.json';plan.write_text(json.dumps(config))
            other=run(t,plan,root/'ablation',b,mapping)
            self.assertEqual(other['sources'],{'tactical':8})
            self.assertGreater(other['team_counts'].get('H',0),0)
            self.assertFalse(other['selected_release'])

    def test_confirmation_backdates_real_support_with_decision_timestamp(self):
        rows=[evidence(i) for i in range(5)]
        result,events=decode(rows,CFG)
        self.assertEqual(result[0]['owner_id'],'p0');self.assertEqual(result[0]['confirmed_at_frame'],2)
        late,_=decode(rows,CFG,backdating=False)
        self.assertEqual(late[0]['team'],'X');self.assertEqual(late[2]['team'],'H')
        self.assertEqual(events[0]['time_s'],0)

    def test_flight_keeps_team_without_owner_and_records_received_pass(self):
        rows=[evidence(i) for i in range(3)]+[evidence(i,None,flight=True) for i in range(3,6)]+[evidence(i,'p1') for i in range(6,9)]
        result,events=decode(rows,CFG)
        self.assertEqual(result[4]['state'],'flight');self.assertEqual(result[4]['team'],'H')
        self.assertIsNone(result[4]['owner_id']);self.assertTrue(any(e['kind']=='pass' for e in events))
        rows[4]['measured']=False;rows[4]['flight']=False
        result,events=decode(rows,CFG)
        self.assertEqual(result[4]['team'],'X');self.assertFalse(any(e['kind']=='pass' for e in events))

    def test_camera_and_unknown_gaps_never_confirm_across_break(self):
        rows=[evidence(i) for i in range(3)];rows[2]['epoch']=1
        result,_=decode(rows,CFG);self.assertTrue(all(r['team']=='X' for r in result))

    def test_prediction_cannot_create_control(self):
        rows=[evidence(i,None,measured=False) for i in range(8)]
        result,_=decode(rows,CFG);self.assertTrue(all(r['owner_id'] is None for r in result))
        rows[0]['candidate']={'owner_id':'p0','team':'H'}
        with self.assertRaises(ValueError):decode(rows,CFG)

    def test_recording_end_does_not_claim_verified_control_end(self):
        _,events=decode([evidence(i) for i in range(5)],CFG)
        end=next(e for e in events if e['kind']=='control_end')
        self.assertTrue(end['right_censored']);self.assertIsNone(end['confirmed_at_frame'])

    def test_motion_and_touch_use_current_measurements_without_mutating_input(self):
        engine=EvidenceExtractor(CFG);last=None
        for i,x in enumerate([105,106,105]):
            packet=frame(i,ball_x=x)
            view={'view_eligible':True,'ball':{'measurement':True,'detection_id':packet['objects'][-1]['detection_id'],'track_id':'ball'},
                'players':[{'player_id':f'p{k}','team':'H' if k<2 else 'A','detection_id':r['detection_id'],
                'image_xy_px':r['image_xy_px'],'motion_reliable':True} for k,r in enumerate(packet['objects'][:-1])]}
            original=copy.deepcopy((packet,view));last=engine.consume(packet,view)
            self.assertEqual((packet,view),original)
        self.assertTrue(last['comotion']);self.assertEqual(last['touch_candidate'],'p0')
        view['ball']=None
        self.assertFalse(engine.consume(frame(3),view)['measured'])

    def test_tag_alone_never_labels_stationary_ball_dead(self):
        rows=[evidence(i,None) for i in range(20)]
        tags=[{'source_id':'tactical','epoch':0,'start_s':0,'end_s':2,'code':'SET PIECES','tags':{'Type':['free kick']}}]
        mask,_=dead_candidates(rows,tags,[],CFG);self.assertFalse(any(mask))
        signals=[{'source_id':'tactical','epoch':0,'frame':0,'origin':'automatic_image_measurement','measurement':True,'verified':True,'kind':'referee_stop'}]
        for i in range(12,20):rows[i]['speed']=2
        mask,events=dead_candidates(rows,tags,signals,CFG)
        self.assertTrue(mask[0]);self.assertFalse(mask[12]);self.assertEqual([e['kind'] for e in events],['stop','restart'])
        self.assertEqual(events[-1]['frame'],12)

    def test_external_reference_split_and_uncertain_intervals(self):
        doc={'provided_fixture_used':False,'source_kind':'permitted_external_video','reference_origin':'external_human_review',
            'split':'validation','game_id':'3','video_sha256':'a'*64,'coverage_s':[[0,10]],'reviewed_event_kinds':['control_start'],
            'events':[{'id':'a','kind':'control_start','earliest_s':2,'latest_s':3,'team':'H','owner_id':'p0'}]}
        plan={'splits':{'train':['2'],'validation':['3'],'recheck':['5']}}
        validate_reference(doc,plan)
        score=evaluate_events([{'kind':'control_start','time_s':2.5,'team':'H','owner_id':'p0'}],doc,0)
        self.assertEqual(score['matched'],1);self.assertEqual(score['uncertain_reference_events'],1)
        doc.update(split='recheck',game_id='5')
        with self.assertRaises(ValueError):validate_reference(doc,plan)
        doc['provided_fixture_used']=True
        with self.assertRaises(ValueError):validate_reference(doc,plan,True)
