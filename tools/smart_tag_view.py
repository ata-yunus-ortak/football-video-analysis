"""Read automatic SportsCode tags for local display only; no truth labels."""
import math
from collections import Counter
import xml.etree.ElementTree as ET


def load_tags(path, fps, frame_count):
    if not math.isfinite(fps) or fps <= 0 or frame_count < 1:
        raise ValueError('Valid reference clock required')
    events = []
    for index, instance in enumerate(ET.parse(path).iter('instance')):
        start, end = float(instance.findtext('start')), float(instance.findtext('end'))
        if not all(math.isfinite(v) for v in (start, end)) or end < start:
            raise ValueError('Invalid Smart Tagging interval')
        tags = {}
        for label in instance.findall('label'):
            group = label.findtext('group') or '(grupsuz)'
            tags.setdefault(group, []).append(label.findtext('text') or '')
        a, b = round(start * fps), round(end * fps)
        # Keep original times/bounds. Navigation is clamped separately by UI.
        events.append({'id': index, 'source_id': instance.findtext('ID') or instance.get('id'),
                       'code': instance.findtext('code') or '(kodsuz)',
                       'start_s': start, 'end_s': end, 'start_frame': a, 'end_frame': b,
                       'duration_s': end - start, 'tags': tags,
                       'outside_reference': a < 0 or b > frame_count,
                       'extras': [{'name': child.tag, 'value': ' '.join(child.itertext()).strip()}
                                  for child in instance if child.tag not in ('ID', 'start', 'end', 'code', 'label')]})
    events.sort(key=lambda e: (e['start_s'], e['end_s'], e['id']))
    return {'available': True, 'fps': fps, 'frame_count': frame_count, 'events': events,
            'count': len(events), 'code_counts': dict(Counter(e['code'] for e in events)),
            'time_base': 'seconds from tactical video frame zero; end frame exclusive',
            'source_kind': 'automatic_provider_tags', 'human_accuracy_evaluated': False}


def demo_tags(fps, frame_count):
    events = [
        {'id': 0, 'source_id': 'synthetic-1', 'code': 'BUILD UP', 'start_s': 1., 'end_s': 4.,
         'start_frame': round(fps), 'end_frame': round(4 * fps), 'duration_s': 3.,
         'tags': {'Team': ['Örnek H'], 'Half': ['1st Half'], 'Side': ['Left', 'Central']}, 'extras': [], 'outside_reference': False},
        {'id': 1, 'source_id': 'synthetic-2', 'code': 'SET PIECES', 'start_s': 3., 'end_s': 5.,
         'start_frame': round(3 * fps), 'end_frame': round(5 * fps), 'duration_s': 2.,
         'tags': {'Team': ['N/A'], 'Half': ['1st Half'], 'Type': ['Throw-in']}, 'extras': [], 'outside_reference': False},
        {'id': 2, 'source_id': 'synthetic-3', 'code': 'DEFENSIVE TRANSITION', 'start_s': 6., 'end_s': 8.,
         'start_frame': round(6 * fps), 'end_frame': round(8 * fps), 'duration_s': 2.,
         'tags': {'Team': ['Örnek A'], 'Half': ['2nd Half']}, 'extras': [], 'outside_reference': False},
    ]
    return {'available': True, 'fps': fps, 'frame_count': frame_count, 'count': len(events), 'events': events,
            'code_counts': dict(Counter(e['code'] for e in events)), 'source_kind': 'synthetic_UI_fixture',
            'human_accuracy_evaluated': False}
