import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from development.clock_alignment import (AlignmentConfig, GeometrySyncConfig, parse_clock,
    observe_tokens, clock_runs, clock_anchors, mapping_segments, mapped_time, refine_anchor)
from tools.clock_observations import ClockOCRConfig, run
from tools.metrica_data import sha256
from tools.sync_alignment import remove_crossings


CFG = AlignmentConfig(.8, 8., 1.1, 3, 4., 1., .25)
GEOMETRY = GeometrySyncConfig(2., .2, 3, .5, 5., .4, .15)


def rows(offset=0., clocks=range(10, 31, 2), period=None):
    return [{'video_time_s': float(c + offset), 'clock_s': float(c), 'confidence': .99,
             'source_kind': 'automatic_clock_observation', 'period': period} for c in clocks]


class ClockAlignmentTests(unittest.TestCase):
    def test_scoreboard_parser_does_not_repair_digits_or_scores(self):
        for text, expected in [('BAR 1-0 ATH 12:34', 754), ('45+02:03', 2823),
                               ('90:00+01:12', 5472), ('105:09', 6309), ('12：34', 754)]:
            self.assertEqual(parse_clock(text), expected)
        for text in ('1-0', '1O:23', '12:60', '01:12:23', '131:00', '12:34 12:35'):
            self.assertIsNone(parse_clock(text))
        observation = observe_tokens([{'text': '12:34', 'confidence': .99},
                                      {'text': '2ND HALF', 'confidence': .99}], .8)
        self.assertEqual(observation['period'], 2)
        self.assertIsNone(observe_tokens([{'text': '12:34', 'confidence': .2}], .8)['clock_s'])

    def test_piecewise_map_never_extrapolates_or_fuses(self):
        anchors = clock_anchors(rows(), rows(5), CFG)
        segments = mapping_segments(anchors, CFG)
        self.assertAlmostEqual(mapped_time(segments, 14.5), 19.5)
        self.assertIsNone(mapped_time(segments, 9.99))
        self.assertIsNone(mapped_time(segments, 30.01))
        self.assertTrue(all(not s['usable_for_possession'] for s in segments))

    def test_cuts_replays_and_unknown_half_collision_remain_unresolved(self):
        broadcast = rows(5) + rows(100)
        self.assertEqual(clock_anchors(rows(), broadcast, CFG), [])
        tactical = rows() + rows(80, clocks=range(40, 51, 2))
        broadcast = rows(5) + rows(90, clocks=range(40, 51, 2))
        segments = mapping_segments(clock_anchors(tactical, broadcast, CFG), CFG)
        self.assertIsNone(mapped_time(segments, 70))
        self.assertEqual(clock_anchors(rows(period=1), rows(5, period=2), CFG), [])
        frozen = [dict(r, clock_s=10.) for r in rows()]
        self.assertEqual(clock_runs(frozen, CFG), [])

    def test_invalid_or_manual_clock_input_fails(self):
        for changes in ({'source_kind': 'manual'}, {'video_time_s': float('nan')},
                        {'clock_s': float('inf')}, {'period': 3}):
            with self.assertRaises(ValueError): clock_runs([dict(rows()[0], **changes)], CFG)
        with self.assertRaises(ValueError): clock_runs(list(reversed(rows())), CFG)
        with self.assertRaises(ValueError): ClockOCRConfig(0, [0, 0, .5, .2], .8, 2)

    def test_geometry_disagreement_removes_review_link(self):
        anchors = clock_anchors(rows(), rows(5), CFG)
        anchors[2]['geometry_status'] = 'source_geometry_disagrees'
        segments = mapping_segments(anchors, CFG)
        self.assertIsNone(mapped_time(segments, anchors[2]['tactical_time_s']))

    def test_cross_source_time_order_contradiction_rejects_both_links(self):
        segments = [{'t0': 0, 't1': 2, 'b0': 10, 'b1': 12},
                    {'t0': 5, 't1': 7, 'b0': 3, 'b1': 5},
                    {'t0': 20, 't1': 22, 'b0': 30, 'b1': 32}]
        self.assertEqual(remove_crossings(segments), [segments[2]])

    def test_geometry_recovers_shift_with_permuted_slots_and_different_fps(self):
        def positions(fps, offset):
            time = np.arange(round(15 * fps)) / fps - offset
            data = np.zeros((len(time), 8, 2))
            for player in range(8):
                data[:, player, 0] = .12 + .09 * player + time * .015
                data[:, player, 1] = .2 + (player % 3) * .2 + np.sin(time) * .01
            return data
        tactical, broadcast = positions(25, 0), positions(20, 2)
        permutation = np.array([4, 2, 0, 6, 7, 5, 1, 3])
        teams = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        anchor = {'tactical_time_s': 6., 'broadcast_time_s': 8.6, 'geometry_supported': False,
                  'usable_for_possession': False, 'uncertainty_s': 1.}
        result = refine_anchor(anchor, tactical, broadcast[:, permutation], teams, teams[permutation],
                               [105, 68], 25, 20, GEOMETRY)
        self.assertTrue(result['geometry_supported'])
        self.assertAlmostEqual(result['broadcast_time_s'], 8.)
        self.assertFalse(result['usable_for_possession'])
        static = np.broadcast_to(tactical[0], tactical.shape)
        result = refine_anchor(anchor, static, static, teams, teams, [105, 68], 25, 25, GEOMETRY)
        self.assertEqual(result['geometry_status'], 'ambiguous_geometry_peak')

    def test_missing_invalid_camera_or_insufficient_team_coverage_does_not_confirm(self):
        data = np.full((300, 8, 2), np.nan)
        teams = [0, 0, 0, 0, 1, 1, 1, 1]
        anchor = {'tactical_time_s': 5., 'broadcast_time_s': 5., 'geometry_supported': False}
        result = refine_anchor(anchor, data, data, teams, teams, [105, 68], 25, 25, GEOMETRY)
        self.assertFalse(result['geometry_supported'])
        data[:] = .5
        result = refine_anchor(anchor, data, data, teams, teams, [105, 68], 25, 25, GEOMETRY,
                               tactical_valid=np.zeros(300, bool))
        self.assertFalse(result['geometry_supported'])

    def test_registered_local_ocr_retains_unknown_frames_without_images(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            video = root / 'synthetic.mp4'; video.write_bytes(b'synthetic-test')
            config = root / 'config.json'
            spec = {'purpose': 'automatic_read_only_synchronization',
                    'parameters_selected_on_provided_fixture': False, 'human_anchors_used': False,
                    'source_provenance': 'Generated scoreboard test', 'fixture_kind': 'synthetic_fixture',
                    'video_sha256': sha256(video),
                    'parameters': {'sample_interval_s': 2., 'roi': [0, 0, .45, .22],
                                   'min_confidence': .8, 'threads': 2}}
            config.write_text(json.dumps(spec))
            frame_reader = lambda *_: iter([(0, 0., 25., np.zeros((8, 8, 3), np.uint8)),
                                            (50, 2., 25., np.zeros((8, 8, 3), np.uint8))])
            observations = iter([[{'text': '12:34', 'confidence': .99}], []])
            summary = run(video, config, root / 'out', factory=lambda _: lambda _: next(observations),
                          frame_reader=frame_reader, provenance=lambda: {'synthetic': True})
            self.assertEqual(summary['samples'], 2)
            self.assertEqual(summary['observed_clock_samples'], 1)
            content = [json.loads(line) for line in (root / 'out' / 'observations.jsonl').read_text().splitlines()]
            self.assertIsNone(content[1]['clock_s'])
            self.assertEqual(summary['images_saved'], 0)
            spec['human_anchors_used'] = True
            config.write_text(json.dumps(spec))
            with self.assertRaises(ValueError): run(video, config, root / 'bad')
