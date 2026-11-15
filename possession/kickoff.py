"""Dead ball before the kick-off of a graded block, from the automatic Smart Tagging.

The organisers grade the second half from its first video frame, which lies before the kick-off; the ball
cannot be in play before a half has kicked off. Their Smart Tagging (automatic, part of the provided bundle
and allowed as input) marks the kick-off of each half as a set piece of type "Kick Off (Start)" (DATA.md).

Rule, as committed by a team member on 12 November 2026 (branch mtah-possession, commit 4b32747,
possession/predict.py) and used here unchanged: in every graded block, if the first "Kick Off (Start)" tag
that starts inside the block starts less than ten minutes after the block's first frame, every frame of
the block before that tag is D. Otherwise the block is left as the models labelled it. No frame number of
any match is stored here.

It cannot be measured on external matches (their tracking starts at the kick-off and they have no Smart
Tagging); the tests are synthetic. A tag that starts after the real kick-off would turn the first moments
of play into D; a missing or unreadable file changes nothing.
"""
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np

CODE, GROUP, TYPE = 'set pieces', 'Type', 'kick off (start)'
MAX_WAIT_S = 10 * 60          # a kick-off tag this long after the block start, or later, is not used


def kickoff_tag_starts(path, fps):
    """Sorted start frames (video frames) of every 'Kick Off (Start)' set piece in a Smart Tagging file.
    Raises on a file that is not XML; an instance without a readable start time is skipped."""
    starts = []
    for inst in ET.parse(path).iter('instance'):
        tags = {lab.findtext('group'): (lab.findtext('text') or '') for lab in inst.findall('label')}
        if (inst.findtext('code') or '').strip().lower() != CODE or tags.get(GROUP, '').strip().lower() != TYPE:
            continue
        try:
            start = float(inst.findtext('start'))
        except (TypeError, ValueError):
            continue
        if np.isfinite(start):
            starts.append(int(round(start * fps)))
    return sorted(starts)


def dead_before_kickoff(labels, blocks, kickoffs, fps):
    """labels: one label per video frame; blocks: [(first, last)] graded blocks, inclusive.
    Returns (new labels, frames changed per block, tag used per block)."""
    out = np.array(labels, copy=True)
    changed, used = [], []
    for first, last in blocks:
        inside = [k for k in kickoffs if first <= k <= last]
        if inside and inside[0] - first < MAX_WAIT_S * fps:
            seg = out[first:inside[0]]
            changed.append(int(np.sum(seg != 'D')))
            seg[:] = 'D'
            used.append(True)
        else:
            changed.append(0)
            used.append(False)
    return out, changed, used


def apply_to_submission(out_dir, tagging_path, blocks, fps):
    """Apply the rule to out_dir/submission.csv (rewritten only if a label changes) and record it in
    out_dir/run.json. Without a readable Smart Tagging file the submission is left as it is."""
    out_dir = Path(out_dir)
    csv_path, run_path = out_dir / 'submission.csv', out_dir / 'run.json'
    rec = {'rule': 'D before the first Smart Tagging "Kick Off (Start)" tag of a graded block, if that tag starts less '
                   'than 10 minutes after the block', 'tagging_file_found': Path(tagging_path).is_file(),
           'tags_read': None, 'used_in_block': [False] * len(blocks), 'frames_changed_in_block': [0] * len(blocks),
           'status': 'no smart tagging file: not applied'}
    report = json.loads(run_path.read_text(encoding='utf-8'))
    kickoffs = None
    if rec['tagging_file_found']:
        try:
            kickoffs = kickoff_tag_starts(tagging_path, fps)
        except (ET.ParseError, OSError, UnicodeError) as e:
            rec['status'] = f'smart tagging unreadable ({type(e).__name__}): not applied'
    if kickoffs is not None:
        with open(csv_path, encoding='utf-8', newline='') as f:
            rows = list(csv.reader(f))
        if rows[0] != ['frame', 'label'] or [r[0] for r in rows[1:]] != [str(i) for i in range(len(rows) - 1)]:
            raise ValueError('unexpected submission layout')
        labels = np.array([r[1] for r in rows[1:]], dtype='<U1')
        new, changed, used = dead_before_kickoff(labels, blocks, kickoffs, fps)
        rec.update(tags_read=len(kickoffs), used_in_block=used, frames_changed_in_block=changed,
                   status='applied' if any(used) else 'no usable tag: not applied')
        if any(changed):
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                w = csv.writer(f, lineterminator='\n')
                w.writerow(['frame', 'label'])
                w.writerows(zip(range(len(new)), new.tolist()))
            graded = np.zeros(len(new), bool)
            spells = 0
            for first, last in blocks:
                graded[first:last + 1] = True
                seg = new[first:last + 1]
                spells += int(np.sum(np.r_[True, seg[1:] != seg[:-1]] & np.isin(seg, ('H', 'A'))))
            report['label_counts_in_play_blocks'] = {k: int(np.sum(new[graded] == k)) for k in 'HADX'}
            report['possession_spells_in_play_blocks'] = spells
            report['submission_sha256'] = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    report['kickoff_rule'] = rec
    report['kickoff_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    run_path.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    return rec
