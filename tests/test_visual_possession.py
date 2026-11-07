import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest

from development.visual_possession import VisualCamera, VisualPossessionConfig, choose_view
from tools.visual_possession_experiment import run
from tools.visual_identity_context import run as prepare
from tools.metrica_data import sha256


REPO = Path(__file__).resolve().parents[1]
PLAN = REPO / 'visual-possession-plan.json'
CFG = VisualPossessionConfig(**json.loads(PLAN.read_text())['parameters'])


def frame(f, source='tactical', ball_x=105, count=4, epoch=0):
    people = []
    for i, x in enumerate([100, 300, 600, 800][:count]):
        people.append({'kind': 'person_candidate', 'detection_id': f'{source}/{f}/p{i}',
            'image_track_id': f'{source}/{epoch}/p{i}', 'confidence': .9,
            'box_xyxy_px': [x-20, 100, x+20, 200], 'image_xy_px': [x, 200]})
    ball = {'kind': 'ball_candidate', 'detection_id': f'{source}/{f}/ball',
            'confidence': .9, 'box_xyxy_px': [ball_x-2, 196, ball_x+2, 200], 'image_xy_px': [ball_x, 198]}
    return {'schema': 'project-image-analysis-v1', 'source_id': source, 'source_frame': f,
        'video_time_s': f / 25, 'fps': 25, 'camera_epoch': epoch, 'image_size_px': [1000,500],
        'objects': people+[ball], 'possession': None, 'fusion_eligible': False,
        'ball_tracking': {'tracks': [{'state': 'observed', 'measurement': True,
            'track_id': f'{source}/{epoch}/ball1', 'detection_id': ball['detection_id'],
            'measured_position_px': ball['image_xy_px'], 'predicted_position_px': None}]}}


def context(p):
    return {**{k:p[k] for k in ('source_id','source_frame','video_time_s','camera_epoch')},
        'origin': 'automatic_player_tracking', 'tracking_sha256':'a'*64, 'metadata_sha256':'b'*64,
        'homography_sha256':'c'*64, 'alignment_validated':True, 'clock_error_bound_s':.01,
        'calibration_validated':True, 'frame_kind':'live', 'pitch_m':[100,50],
        'normalized_pitch_to_image':[[1000,0,0],[0,500,0],[0,0,1]],
        'players':[{'player_id':f'p{i}','team':'H' if i<2 else 'A','normalized_xy':[x/1000,.4]}
                   for i,x in enumerate([100,300,600,800])]}


def sequence(source='tactical', ball_x=105):
    engine=VisualCamera(CFG); result=None
    for f in range(8):
        p=frame(f,source,ball_x); result=engine.consume(p,context(p))
    return result


def pair(t,b):
    return {'primary_source_id':t['source_id'],'primary_frame':t['source_frame'],'primary_epoch':t['camera_epoch'],
            'secondary_source_id':b['source_id'],'secondary_frame':b['source_frame'],'secondary_epoch':b['camera_epoch'],
            'verified':True,'error_bound_s':.01}


class VisualPossessionTests(unittest.TestCase):
    def test_video_control_emits_owner_and_preserves_input(self):
        engine=VisualCamera(CFG)
        for f in range(8):
            p=frame(f); c=context(p); original=copy.deepcopy((p,c))
            result=engine.consume(p,c)
            self.assertEqual((p,c),original)
            if f<4:self.assertEqual(result['label'],'X')
        self.assertEqual(result['label'],'H'); self.assertEqual(result['owner_id'],'p0')
        self.assertFalse(result['tracking_ball_used']); self.assertFalse(result['baseline_owner_used'])

    def test_tracking_cannot_inject_ball_or_owner(self):
        for extra in ({'ball':[.1,.2]}, {'owner':'A'}, {'labels':[]}, {'reference':[]}):
            p=frame(0); c=context(p); c.update(extra)
            with self.assertRaises(ValueError): VisualCamera(CFG).consume(p,c)

    def test_identity_metadata_and_image_ball_have_separate_roles(self):
        # Same tracking player geometry; only image ball changes H -> A.
        self.assertEqual(sequence(ball_x=105)['label'],'H')
        self.assertEqual(sequence(ball_x=605)['label'],'A')

    def test_missing_unvalidated_replay_and_truncated_views_abstain(self):
        for change in (None, {'alignment_validated':False}, {'calibration_validated':False},
                       {'frame_kind':'replay'}, {'clock_error_bound_s':.1}, {'source_frame':50}):
            engine=VisualCamera(CFG)
            for f in range(8):
                p=frame(f); c=None if change is None else dict(context(p),**change)
                result=engine.consume(p,c)
            self.assertEqual(result['label'],'X')
        engine=VisualCamera(CFG)
        for f in range(8):
            p=frame(f,count=2); result=engine.consume(p,context(p))
        self.assertFalse(result['view_eligible']); self.assertEqual(result['label'],'X')

    def test_forecasts_multiple_balls_and_unconfirmed_ball_abstain(self):
        for change in ('forecast','tentative','multiple','missing'):
            engine=VisualCamera(CFG)
            for f in range(8):
                p=frame(f); t=p['ball_tracking']['tracks'][0]
                if change=='forecast': t.update(state='predicted',measurement=False)
                if change=='tentative':t['state']='tentative'
                if change=='multiple':p['ball_tracking']['tracks'].append(copy.deepcopy(t))
                if change=='missing':p['ball_tracking']['tracks']=[]
                result=engine.consume(p,context(p))
            self.assertEqual(result['label'],'X')

    def test_unknown_nearest_person_is_not_skipped_to_award_known_player(self):
        engine=VisualCamera(CFG)
        for f in range(8):
            p=frame(f,ball_x=205)
            p['objects'].insert(0,{'kind':'person_candidate','detection_id':f'unknown/{f}',
                'image_track_id':'unknown','confidence':.9,'box_xyxy_px':[180,100,220,200],
                'image_xy_px':[200,200]})
            result=engine.consume(p,context(p))
        self.assertEqual(result['reason'],'nearest_person_identity_unknown')

    def test_fast_relative_motion_and_camera_cut_reset_control(self):
        engine=VisualCamera(CFG)
        for f in range(8):
            p=frame(f,ball_x=105 if f%2==0 else 140)
            result=engine.consume(p,context(p))
        self.assertEqual(result['label'],'X')
        engine=VisualCamera(CFG)
        for f in range(8):
            p=frame(f); result=engine.consume(p,context(p))
        self.assertEqual(result['label'],'H')
        p=frame(8,epoch=1); self.assertEqual(engine.consume(p,context(p))['label'],'X')

    def test_duplicate_or_ambiguous_player_assignment_not_identified(self):
        engine=VisualCamera(CFG)
        for f in range(8):
            p=frame(f); c=context(p)
            c['players'].append({'player_id':'other','team':'A','normalized_xy':[.101,.4]})
            result=engine.consume(p,c)
        self.assertEqual(result['label'],'X')

    def test_broadcast_image_owner_wins_only_in_verified_geometric_match(self):
        t,b=sequence(),sequence('broadcast',605)
        result=choose_view(t,b,pair(t,b),CFG)
        self.assertTrue(result['broadcast_allowed']); self.assertEqual(result['label'],'A')
        self.assertEqual(result['decision_source'],'broadcast')
        for change in ({'verified':False},{'secondary_frame':2},{'error_bound_s':.1}):
            result=choose_view(t,b,dict(pair(t,b),**change),CFG)
            self.assertEqual(result['label'],'H');self.assertFalse(result['broadcast_allowed'])

    def test_broadcast_geometry_conflict_and_unusable_view_fall_back(self):
        t,b=sequence(),sequence('broadcast',605)
        for p in b['players']:p['pitch_xy_m'][0]+=10
        result=choose_view(t,b,pair(t,b),CFG)
        self.assertFalse(result['broadcast_allowed']);self.assertEqual(result['label'],'H')
        b=sequence('broadcast',605);b['view_eligible']=False
        self.assertEqual(choose_view(t,b,pair(t,b),CFG)['decision_source'],'tactical')

    def test_tactical_unseen_by_broadcast_players_are_retained(self):
        t,b=sequence(),sequence('broadcast',605)
        t['players'].append(dict(t['players'][0],player_id='off_camera',pitch_xy_m=[95,20]))
        result=choose_view(t,b,pair(t,b),CFG)
        p=next(p for p in result['players'] if p['player_id']=='off_camera')
        self.assertEqual(p['camera'],'tactical')

    def test_collective_image_jump_rejects_view(self):
        engine=VisualCamera(CFG)
        for f in range(8):
            p=frame(f);engine.consume(p,context(p))
        p=frame(8);c=context(p)
        for person in p['objects'][:-1]:
            person['image_xy_px'][0]+=100
            person['box_xyxy_px'][0]+=100;person['box_xyxy_px'][2]+=100
        for person in c['players']:person['normalized_xy'][0]+=.1
        result=engine.consume(p,c)
        self.assertTrue(result['bulk_jump']);self.assertFalse(result['view_eligible'])
        self.assertEqual(result['label'],'X')

    def test_canonical_player_team_change_is_rejected(self):
        engine=VisualCamera(CFG);p=frame(0);engine.consume(p,context(p))
        p=frame(1);c=context(p);c['players'][0]['team']='A'
        with self.assertRaises(ValueError):engine.consume(p,c)


class VisualRunnerTests(unittest.TestCase):
    def make(self,root,source):
        analysis=root/source;analysis.mkdir()
        packets=[frame(f,source,605 if source=='broadcast' else 105) for f in range(8)]
        (analysis/'frames.jsonl').write_text(''.join(json.dumps(p)+'\n' for p in packets))
        (analysis/'registration.json').write_text(json.dumps({'provided_fixture_used':False,'fixture':{
            'id':'synthetic-video-led','provided_fixture_used':False,'source_kind':'synthetic_fixture'}}))
        (analysis/'summary.json').write_text(json.dumps({'frames':8,'output_sha256':sha256(analysis/'frames.jsonl')}))
        raw=root/(source+'.txt');meta=root/(source+'.xml');hom=root/(source+'.csv')
        # Invalid/non-numeric BALL is intentional: identity preparation must not parse it.
        raw.write_text(''.join(str(f+1)+':'+ ';'.join(f'{x/1000},0.4,0' for x in [100,300,600,800])+':BALL_MUST_NOT_BE_READ\n' for f in range(8)))
        meta.write_text('<Root><FrameRate>25</FrameRate><FieldSize><Width>100</Width><Height>50</Height></FieldSize><Teams><Team id="H"/><Team id="A"/></Teams><Players>'+''.join(f'<Player id="p{i}" teamId="'+('H' if i<2 else 'A')+'"/>' for i in range(4))+'</Players></Root>')
        with hom.open('w',newline='') as stream:
            w=csv.writer(stream);w.writerow(['frame']+[f'h{i}{j}' for i in range(3) for j in range(3)]+['reprojection_error','valid'])
            for f in range(8):w.writerow([f,1000,0,0,0,500,0,0,0,1,0,1])
        evidence=root/(source+'-evidence.jsonl')
        evidence.write_text(''.join(json.dumps({**{k:p[k] for k in ('source_frame','source_id','camera_epoch','video_time_s')},
            'origin':'automatic_camera_validation','alignment_validated':True,'clock_error_bound_s':.01,
            'calibration_validated':True,'frame_kind':'live'})+'\n' for p in packets))
        spec={'provided_fixture_used':False,'reference_annotations_as_inputs':False,'source_kind':'synthetic_fixture',
              'fixture_id':'synthetic-video-led','analysis_path':str(analysis),'tracking_frame_offset':0,'homography_frame_offset':0,
              'camera_evidence_path':str(evidence),'camera_evidence_sha256':sha256(evidence)}
        for key,path in [('tracking',raw),('metadata',meta),('homography',hom)]:
            spec[key+'_path']=str(path);spec[key+'_sha256']=sha256(path)
        specpath=root/(source+'-spec.json');specpath.write_text(json.dumps(spec))
        output=root/(source+'-identity');prepare(specpath,output)
        return output/'camera-manifest.json'

    def test_end_to_end_player_adapter_and_video_led_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);t=self.make(root,'tactical');b=self.make(root,'broadcast')
            mapping=root/'pairs.jsonl'
            mapping.write_text(''.join(json.dumps(pair(frame(f),frame(f,'broadcast')))+'\n' for f in range(8)))
            result=run(t,PLAN,root/'result',b,mapping)
            self.assertEqual(result['label_counts'],{'X':4,'A':4})
            self.assertFalse(result['tracking_ball_used']); self.assertFalse(result['baseline_owner_used'])
            with (root/'result/possession.csv').open() as stream:
                rows=list(csv.DictReader(stream))
            self.assertEqual(rows[-1]['owner_id'],'p2')

    def test_without_camera_validation_identity_is_not_promoted(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.make(root,'tactical')
            spec=json.loads((root/'tactical-spec.json').read_text());spec.pop('camera_evidence_path');spec.pop('camera_evidence_sha256')
            specpath=root/'no-validation.json';specpath.write_text(json.dumps(spec))
            prepare(specpath,root/'unvalidated')
            result=run(root/'unvalidated/camera-manifest.json',PLAN,root/'result')
            self.assertEqual(result['label_counts'],{'X':8})

    def test_changed_raw_tracking_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);manifest=self.make(root,'tactical')
            (root/'tactical.txt').write_text('changed')
            with self.assertRaises(ValueError):run(manifest,PLAN,root/'result')

    def test_supplied_match_is_not_a_development_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);manifest=self.make(root,'tactical')
            spec=json.loads(manifest.read_text());spec['provided_fixture_used']=True
            manifest.write_text(json.dumps(spec))
            with self.assertRaises(ValueError):run(manifest,PLAN,root/'result')
