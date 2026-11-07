import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import numpy as np
from development.hybrid_tracking import HybridConfig, fuse
from development.hybrid_pipeline import predict_hybrid
from development.motion_possession import MotionConfig, predict
from development.dead_ball_features import extract
from development.player_motion import measured_motion
from tools.hybrid_experiment import run as run_controlled


# Synthetic engineering values, not selected/validated competition settings.
CFG = HybridConfig(8, 3, .7, .04, 1.5, .6, 3., 13., 4, .4, .3, .3, .8, 2., 45., .25)
MOTION = MotionConfig(.1, 3., 60., 4., .5, .3, .1, 3.)


def sample(n=80, fps=10.):
    k = np.arange(12)
    players = np.empty((n, 12, 2))
    players[:, :, 0] = 10 + (k // 2) * 12 + np.arange(n)[:, None] / fps * .2
    players[:, :, 1] = 15 + (k % 2) * 24
    base = {'players': players, 'ball': np.column_stack((20 + np.arange(n) / fps * 2, np.full(n, 30.))),
            'teams': k % 2, 'period': np.ones(n, int), 'frame': np.arange(n),
            'fps': np.asarray(fps), 'pitch': np.array([105., 68.]),
            'player_detected': np.ones((n, 12), bool), 'ball_observed': np.ones(n, bool)}
    permutation = np.array([8, 1, 6, 3, 0, 5, 2, 7, 4, 9, 10, 11])
    broadcast = {key: np.array(value, copy=True) for key, value in base.items()}
    broadcast['players'] = base['players'][:, permutation].copy() + [.1, 0]
    broadcast['teams'] = base['teams'][permutation]
    broadcast['ball'] += [.1, 0]
    visible = np.tile(permutation < 10, (n, 1))
    view = {'source_kind': 'synthetic_image_observations', 'player_visible': visible,
            'ball_visible': np.ones(n, bool), 'calibration_valid': np.ones(n, bool),
            'ball_ground_valid': np.ones(n, bool), 'player_confidence': np.full((n, 12), .95),
            'ball_confidence': np.full(n, .95), 'camera_epoch': np.zeros(n, int),
            'frame_kind': np.full(n, 'live', dtype='<U12')}
    alignment = {'source_kind': 'synthetic_known_alignment', 'human_anchors_used': False,
                 'broadcast_frame': np.arange(n), 'verified': np.ones(n, bool), 'error_bound_s': np.zeros(n)}
    return base, broadcast, alignment, view, permutation


class HybridTests(unittest.TestCase):
    def test_visible_broadcast_players_preferred_and_other_players_unchanged(self):
        tactical, broadcast, alignment, view, permutation = sample()
        original_t, original_b = tactical['players'].copy(), broadcast['players'].copy()
        result = fuse(tactical, broadcast, alignment, view, CFG)
        self.assertTrue(result['frame_allowed'][20])
        self.assertTrue((result['player_source'][20, :10] == 1).all())
        self.assertTrue((result['player_source'][20, 10:] == 0).all())
        np.testing.assert_allclose(result['inputs']['players'][20, :10], tactical['players'][20, :10] + [.1, 0])
        np.testing.assert_array_equal(result['inputs']['players'][:, 10:], tactical['players'][:, 10:])
        for t in range(10): self.assertEqual(result['broadcast_slot'][20, t], int(np.flatnonzero(permutation == t)[0]))
        np.testing.assert_array_equal(tactical['players'], original_t)
        np.testing.assert_array_equal(broadcast['players'], original_b)
        self.assertFalse(result['selected_release'])

    def test_empty_two_person_replay_close_up_and_unknown_views_fall_back(self):
        for kind, count in [('live', 0), ('live', 2), ('replay', 10), ('close_up', 10), ('no_picture', 10), ('unknown', 10)]:
            with self.subTest(kind=kind, count=count):
                t, b, a, v, _ = sample();v['frame_kind'][:] = kind
                v['player_visible'][:] = False;v['player_visible'][:, :count] = True
                result = fuse(t, b, a, v, CFG)
                self.assertFalse(result['player_source'].any());self.assertFalse(result['ball_source'].any())
                np.testing.assert_array_equal(result['inputs']['players'], t['players'])

    def test_review_maps_unknown_visibility_and_wrong_timing_never_activate(self):
        for mode in ('review', 'review_file', 'review_api', 'none', 'finiteness', 'uncertain', 'wrong_period', 'calibration', 'fps'):
            with self.subTest(mode=mode):
                t, b, a, v, _ = sample()
                if mode == 'review': a['source_kind'] = 'automatic_review_candidates'
                elif mode == 'review_file': a = {'version': 'automatic-review-alignment-v1', 'usable_for_possession': False}
                elif mode == 'review_api': a = {'review_only': True, 'usable_for_possession': False}
                elif mode == 'none': v = None
                elif mode == 'finiteness': v['source_kind'] = 'finite_atd_points'
                elif mode == 'uncertain': a['error_bound_s'][:] = .5
                elif mode == 'wrong_period': b['period'][:] = 2
                elif mode == 'calibration': v['calibration_valid'][:] = False
                elif mode == 'fps': b['fps'] = np.asarray(25.)
                result = fuse(t, b, a, v, CFG)
                self.assertFalse(result['player_source'].any())
                self.assertFalse(result['ball_source'].any())

    def test_large_disagreement_and_collective_extreme_motion_disable_broadcast(self):
        t, b, a, v, _ = sample();b['players'] += [8, 0]
        result = fuse(t, b, a, v, CFG)
        self.assertFalse(result['frame_allowed'].any())
        t, b, a, v, _ = sample();b['players'][40:42] += [10, 0]
        result = fuse(t, b, a, v, CFG)
        for f in (39, 40, 41, 42):
            self.assertFalse(result['frame_allowed'][f])
            self.assertEqual(result['frame_reason'][f], 'collective_extreme_motion')
        self.assertFalse(result['frame_allowed'][44])
        self.assertTrue(result['frame_allowed'][45])

    def test_single_bad_or_ambiguous_player_keeps_tactical_and_no_duplicate_ids(self):
        t, b, a, v, permutation = sample()
        slot = int(np.flatnonzero(permutation == 0)[0]);b['players'][40, slot] += [10, 0]
        result = fuse(t, b, a, v, CFG)
        self.assertTrue(result['frame_allowed'][40]);self.assertEqual(result['player_source'][40, 0], 0)
        np.testing.assert_array_equal(result['inputs']['players'][40, 0], t['players'][40, 0])
        for row in result['broadcast_slot']:
            valid = row[row >= 0];self.assertEqual(len(valid), len(set(valid)))
        t, b, a, v, _ = sample();t['players'][:, 2] = t['players'][:, 0]
        result = fuse(t, b, a, v, CFG)
        self.assertFalse(result['player_source'][:, [0, 2]].any())

    def test_short_missing_track_can_use_fresh_link_but_never_invent_a_point(self):
        t, b, a, v, _ = sample();t['players'][40:43, 0] = np.nan;t['player_detected'][40:43, 0] = False
        result = fuse(t, b, a, v, CFG)
        self.assertEqual(result['player_source'][40, 0], 1)
        self.assertEqual(result['player_source'][41, 0], 1)
        self.assertEqual(result['player_source'][42, 0], 0)
        self.assertTrue(np.isnan(result['inputs']['players'][42, 0]).all())

    def test_ball_visibility_ground_validity_conflict_and_missing_tactical_ball(self):
        for mode in ('invisible', 'airborne_or_unknown', 'conflict', 'missing_tactical'):
            with self.subTest(mode=mode):
                t, b, a, v, _ = sample()
                if mode == 'invisible': v['ball_visible'][:] = False
                elif mode == 'airborne_or_unknown': v['ball_ground_valid'][:] = False
                elif mode == 'conflict': b['ball'] += [5, 0]
                else: t['ball'][40:50] = np.nan;t['ball_observed'][40:50] = False
                result = fuse(t, b, a, v, CFG)
                if mode == 'missing_tactical':
                    self.assertTrue((result['ball_source'][40:50] == 1).all())
                    self.assertTrue(result['inputs']['ball_observed'][40:50].all())
                else:self.assertFalse(result['ball_source'].any())

    def test_camera_cut_and_time_index_skip_reset_confirmation(self):
        for mode in ('epoch', 'index'):
            t, b, a, v, _ = sample()
            if mode == 'epoch': v['camera_epoch'][40:] = 1
            else: a['broadcast_frame'][40] = 39
            result = fuse(t, b, a, v, CFG)
            self.assertFalse(result['frame_allowed'][40])
            self.assertFalse(result['frame_allowed'][41])
            self.assertTrue(result['frame_allowed'][43 if mode == 'epoch' else 44])

    def test_source_switch_does_not_produce_velocity_contact_pass_or_dead_ball(self):
        t, b, a, v, _ = sample();b['ball'] += [.9, 0];v['frame_kind'][38:43] = 'replay'
        result = fuse(t, b, a, v, CFG)
        switches = np.flatnonzero(np.diff(result['ball_source']) != 0) + 1
        self.assertTrue(len(switches))
        features = extract(result['inputs'])
        self.assertTrue(np.isnan(features['ball_speed_mps'][switches]).all())
        velocity, _, _ = measured_motion(result['inputs'], 13.)
        for slot in range(10):
            changes = np.flatnonzero(np.diff(result['player_source'][:, slot]) != 0) + 1
            self.assertTrue(np.isnan(velocity[changes, slot]).all())
        pipeline = predict_hybrid(t, b, a, v, CFG, np.full(len(t['ball']), 'H'), MOTION)
        self.assertEqual(pipeline['contacts'], []);self.assertEqual(pipeline['passes'], [])
        self.assertFalse((pipeline['labels'] == 'D').any())
        bad = dict(result['inputs']);del bad['ball_pair_valid']
        with self.assertRaises(ValueError): extract(bad)

    def test_a_real_contact_chain_is_not_joined_across_a_source_break(self):
        n = 20
        x = np.r_[np.full(4, 20.), np.arange(21., 27.), np.full(10, 26.)]
        inputs = {'ball': np.column_stack((x, np.full(n, 30.))),
            'players': np.tile([[20., 30.], [26., 30.], [23., 30.]], (n, 1, 1)),
            'teams': np.array([0, 0, 1]), 'period': np.ones(n, int), 'frame': np.arange(n),
            'ball_observed': np.ones(n, bool), 'player_detected': np.ones((n, 3), bool),
            'fps': np.asarray(10.), 'pitch': np.array([105., 68.])}
        self.assertEqual(len(predict(inputs, np.full(n, 'H'), MOTION)['passes']), 1)
        inputs['ball_pair_valid'] = np.ones(n, bool);inputs['ball_pair_valid'][6] = False
        result = predict(inputs, np.full(n, 'H'), MOTION)
        self.assertEqual([event['frame'] for event in result['contacts']], [3, 9])
        self.assertEqual(result['passes'], [])

    def test_manual_and_malformed_evidence_fail_instead_of_silent_activation(self):
        for mode in ('manual', 'indices', 'confidence'):
            t, b, a, v, _ = sample()
            if mode == 'manual': a['human_anchors_used'] = True
            elif mode == 'indices': a['broadcast_frame'] = np.arange(80, dtype=float)
            else:v['player_confidence'][3, 0] = np.inf
            with self.assertRaises(ValueError): fuse(t, b, a, v, CFG)

    def test_provided_fixture_is_rejected_before_controlled_experiment_reads_arrays(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan = Path(__file__).resolve().parents[1] / 'hybrid-data-plan.json'
            (root / 'report.json').write_text(json.dumps({'provided_fixture_used': True}))
            with patch('tools.hybrid_experiment.np.load') as load:
                with self.assertRaises(ValueError): run_controlled(root, plan, root / 'out')
                load.assert_not_called()
            self.assertFalse((root / 'out').exists())
