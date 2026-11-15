"""Derive possession/run216.py from the frozen possession/run215.py by exact text replacements (each must match once),
so that everything not listed here is the v2.15 flow verbatim. Usage: python3 make_run216.py <out file>"""
import sys
from pathlib import Path

src = Path('/home/claude/sc/possession/run215.py').read_text(encoding='utf-8')
a = src.index('import argparse')
body = src[a:]


def rep(old, new, count=1):
    global body
    assert body.count(old) == count, (body.count(old), old[:80])
    body = body.replace(old, new)


DOC = '''"""Generate the competition submission with possession v2.16.

Run on the team's own computer (the data must never be uploaded to AI services):

    python -m possession.run216 --data-dir C:/path/to/mtah2027-data --out C:/path/to/new-output-dir
        [--tactical-clock <clock observations dir> --broadcast-clock <clock observations dir>]

v2.16 is possession.run215 with one added step; every other line of run() below is the v2.15 flow.
4. Players the tactical tracking has lost. When the broadcast files are present and the accuracy gate of
   possession/fusion.py is open (the two cameras agree on the ball within 0.50 m), a broadcast player
   that, after the time alignment and the player-based registration, has no tactical player of either
   team within 1.5 m is added to the tracking the models see (possession/playerfill.py), under the team
   the broadcast tracking gives it. Tactical positions are never moved or removed. The goalkeeper team
   check then runs on the tracking with the added players, and the ball is filled as before.
   Without broadcast files, or with the gate closed, the output is that of possession.run215.
   Selected on external matches with a simulated second camera against gates registered beforehand
   (possession-v216-plan.json, possession-v216-results.json).
Changes 1-3 are those of possession.run215: the organisers' graded windows, the second model family on
the v2.1 path, the Smart Tagging kick-off rule.
"""
'''

rep("from . import run211, run211k, kickoff, pooling\n",
    "from . import run211, run211k, run215, kickoff, pooling\n")
rep("from .register import register_ball\n",
    "from .register import register_ball\nfrom .playerfill import fill_players\n")
rep("RELEASE = HERE.parent / 'possession-v215-release.json'\n",
    "RELEASE = HERE.parent / 'possession-v216-release.json'\n")
rep("SOURCES = run211.SOURCES + TCN_SOURCES + ('pooling.py', 'kickoff.py', 'run211g.py', 'run211k.py', 'run215.py')\n",
    "SOURCES = run215.SOURCES + ('playerfill.py', 'run216.py')\n")
rep("        v21_model=V21_MODEL, v23_model=V23_MODEL, tcn_model=TCN_MODEL, release=RELEASE, pooled=True):\n",
    "        v21_model=V21_MODEL, v23_model=V23_MODEL, tcn_model=TCN_MODEL, release=RELEASE, pooled=True, add_players=True):\n")
rep("    # --- broadcast fill\n    fusion = {'used': False}\n",
    "    # --- broadcast fill\n    fusion = {'used': False}\n"
    "    added = {'used': False, 'reason': 'switched off (test only)' if not add_players else 'no broadcast files, or the accuracy gate is closed'}\n")
rep("        if frep['used']:\n            model_input = dict(model_input, ball=filled_ball)\n",
    "        if frep['used']:\n"
    "            if add_players:                                                    # change 4: players the tactical tracking has lost\n"
    "                players, team, added = fill_players(match, bro2, t_of_b, match['fps'])\n"
    "                model_input, keeper = correct_goalkeepers(dict(match, players=players, team=team))\n"
    "                added = dict(added, used=True)\n"
    "            model_input = dict(model_input, ball=filled_ball)\n")
rep("    report = {'rows': n, 'system': ('possession-v2.15 (v2.11 on the graded windows; on the v2.1 path its probabilities are pooled with a '\n"
    "                                    'temporal convolution network before the v2 decoder; Smart Tagging kick-off rule)'),\n"
    "              'second_model': second,\n",
    "    report = {'rows': n, 'system': ('possession-v2.16 (v2.15 with the players the tactical tracking has lost added from the broadcast '\n"
    "                                    'tracking when the accuracy gate is open)'),\n"
    "              'second_model': second,\n"
    "              'added_players': added,\n")
rep("              'inputs_used': ['tactical ATD metadata', 'tactical ATD raw positions', 'broadcast ATD (if present)',\n",
    "              'inputs_used': ['tactical ATD metadata', 'tactical ATD raw positions', 'broadcast ATD: ball and players (if present)',\n")
Path(sys.argv[1]).write_text(DOC + body, encoding='utf-8')
print('written', sys.argv[1])
