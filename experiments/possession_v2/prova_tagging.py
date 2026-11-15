"""Rehearsal of the v2.11k chain (K011): a synthetic Smart Tagging file for the synthetic rehearsal bundle A of K003.

Bundle A has the file names, record counts and slot counts of the provided files; its content is corrupted Metrica
sample games laid out on the published graded windows, with an invented stretch before the second-half kick-off
(frames 110,808-113,741; prova_build.py). This script adds what bundle A lacks: a SportsCode XML with the structure
DATA.md describes (638 instances, the published code and set-piece type counts, tag groups Team / Half / Type) whose
two "Kick Off (Start)" instances are 5 s windows that contain the bundle's two kick-offs, as the organisers'
starter/load_smart_tagging.py says of the delivered file. Everything else in it is random. Nothing here comes from the
provided match: the frame numbers are the published graded windows and kick-off frames the bundle was laid out on.

Usage: prova_tagging.py OUT_BUNDLE_DIR   (creates OUT_BUNDLE_DIR/{tactical,broadcast} as links to bundle A + the XML)
"""
import os, sys, hashlib
from pathlib import Path
import numpy as np
P = Path('/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova')
FPS = 25
KICKOFF = {'1st Half': 11185, '2nd Half': 113742}          # where the halves of bundle A start (published frames)
LEAD = {'1st Half': 50, '2nd Half': 60}                    # frames by which the synthetic tag window starts before the kick-off
END = {'1st Half': 90651, '2nd Half': 190197}
CODES = {'PLAYERS IN THE BOX': 97, 'BALL IN FINAL THIRD': 93, 'BALL IN THE BOX': 72, 'PROGRESSION': 66, 'DEFENDING IN MIDDLE THIRD': 66,
         'CREATING CHANCES': 30, 'DEFENDING IN DEFENSIVE THIRD': 30, 'LONG BALL': 29, 'ATTACKING TRANSITION': 24,
         'DEFENSIVE TRANSITION': 24, 'BUILD UP': 22, 'DEFENDING IN ATTACKING THIRD': 22, 'GOALS': 4}
TYPES = {'Throw-in': 26, 'Corner Kick': 12, 'Goal Kick': 10, 'Free Kick': 5, 'Kick Off (After Goal)': 4}


def instances(rng):
    out = []
    for half, k in KICKOFF.items():
        s = (k - LEAD[half]) / FPS
        out.append((s, s + 5.0, 'SET PIECES', [('Team', 'N/A'), ('Half', half), ('Type', 'Kick Off (Start)')]))
    def anywhere():
        half = str(rng.choice(list(KICKOFF)))
        a = rng.uniform(KICKOFF[half] + 30 * FPS, END[half] - 60 * FPS) / FPS
        return half, round(float(a), 2), round(float(a + rng.uniform(2, 25)), 2)
    for typ, n in TYPES.items():
        for _ in range(n):
            half, a, b = anywhere()
            out.append((a, b, 'SET PIECES', [('Team', str(rng.choice(['Barcelona', 'Atletic Club']))), ('Half', half), ('Type', typ)]))
    for code, n in CODES.items():
        for _ in range(n):
            half, a, b = anywhere()
            out.append((a, b, code, [('Team', str(rng.choice(['Barcelona', 'Atletic Club']))), ('Half', half),
                                     ('Side', str(rng.choice(['Central', 'Left', 'Right'])))]))
    out.sort(key=lambda t: t[0])
    return out


def xml(inst):
    parts = ['<?xml version="1.0" encoding="utf-8"?>', '<file>', '<ALL_INSTANCES>']
    for i, (a, b, code, labels) in enumerate(inst, 1):
        parts.append(f'<instance><ID>{i}</ID><start>{a}</start><end>{b}</end><code>{code}</code>'
                     + ''.join(f'<label><group>{g}</group><text>{t}</text></label>' for g, t in labels) + '</instance>')
    parts += ['</ALL_INSTANCES>', '</file>']
    return '\n'.join(parts) + '\n'


if __name__ == '__main__':
    out = Path(sys.argv[1])
    for cam in ('tactical', 'broadcast'):
        (out / cam).mkdir(parents=True)
        for f in sorted((P / 'A' / 'bundle' / cam).iterdir()):
            os.symlink(f, out / cam / f.name)
    inst = instances(np.random.default_rng(20261113))
    assert len(inst) == 638
    text = xml(inst)
    (out / 'tactical' / 'BAR-ATH_tactical_smart_tagging.xml').write_text(text, encoding='utf-8')
    print({'instances': len(inst), 'sha256': hashlib.sha256(text.encode()).hexdigest(),
           'kickoff_tag_start_frames': [int(round(a * FPS)) for a, _, c, l in inst if ('Type', 'Kick Off (Start)') in l]})
