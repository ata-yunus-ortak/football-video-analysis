"""Derive possession/run217.py from the frozen possession/run216.py by exact text replacements (each must match once),
so that everything not listed here is the v2.16 flow verbatim. Usage: python3 make_run217.py <out file>"""
import sys
from pathlib import Path

src = Path('/home/claude/sc/possession/run216.py').read_text(encoding='utf-8')
a = src.index('import argparse')
body = src[a:]


def rep(old, new, count=1):
    global body
    assert body.count(old) == count, (body.count(old), old[:80])
    body = body.replace(old, new)


DOC = '''"""Generate the competition submission with possession v2.17.

Run on the team's own computer (the data must never be uploaded to AI services):

    python -m possession.run217 --data-dir C:/path/to/mtah2027-data --out C:/path/to/new-output-dir
        [--tactical-clock <clock observations dir> --broadcast-clock <clock observations dir>]

v2.17 is possession.run216 with another second model; every other line of run() below is the v2.16 flow.
5. The second model family on the v2.1 path is an ensemble of eight networks instead of three: four on the
   37 features of possession/tcn/features.py and four on the 71 features of possession/tcn/features2.py
   (models/possession-tcn-v217/, trained by a team member on external matches; byte copies of repository
   branch mtah-possession, commit 74bedbf, as is the inference module possession/tcn/infer2.py, which gives
   every member the features it was trained with). Its weight in the arithmetic pool is 0.4 instead of 0.2.
   Pool, decoder and the rule that nothing is pooled on the v2.3 path are unchanged.
   Selected on external matches against gates registered beforehand (possession-v217-plan.json,
   possession-v217-results.json); it is the fourth registered attempt with a second model.
Changes 1-4 are those of possession.run216: the organisers' graded windows, the second model family on
the v2.1 path, the Smart Tagging kick-off rule, the players the tactical tracking has lost.
"""
'''

rep("from . import run211, run211k, run215, kickoff, pooling\n",
    "from . import run211, run211k, run215, run216, kickoff, pooling\n")
rep("from .tcn import infer as tcn_infer, decode as tcn_decode\n",
    "from .tcn import infer2 as tcn_infer, decode as tcn_decode\n")
rep("RELEASE = HERE.parent / 'possession-v216-release.json'\n",
    "RELEASE = HERE.parent / 'possession-v217-release.json'\n")
rep("TCN_MODEL = HERE.parent / 'models' / 'possession-tcn-v215.npz'\n",
    "TCN_DIR = HERE.parent / 'models' / 'possession-tcn-v217'\n"
    "TCN_MEMBERS = ('d6_a_s0.npz', 'd6_a_s1.npz', 'd6_a_s2.npz', 'd6_a_s3.npz', 'd6_f_s0.npz', 'd6_f_s1.npz', 'd6_f_s2.npz', 'd6_f_s3.npz')\n"
    "TCN_WEIGHT = 0.4               # weight of the network in the arithmetic pool, fixed in possession-v217-plan.json\n")
rep("SOURCES = run215.SOURCES + ('playerfill.py', 'run216.py')\n",
    "SOURCES = run216.SOURCES + ('tcn/features2.py', 'tcn/infer2.py', 'run217.py')\n")
rep("    \"\"\"Every source and both bundles must match the frozen release manifest.\"\"\"\n",
    "    \"\"\"Every source, both bundles and the eight network members must match the frozen release manifest.\"\"\"\n")
rep("    for key, model in (('v2.1', V21_MODEL), ('v2.3', V23_MODEL), ('tcn', TCN_MODEL)):\n"
    "        if rel['bundle_sha256'][key] != sha256(model):\n"
    "            raise ValueError(f'frozen bundle changed: {key}')\n",
    "    for key, model in (('v2.1', V21_MODEL), ('v2.3', V23_MODEL)):\n"
    "        if rel['bundle_sha256'][key] != sha256(model):\n"
    "            raise ValueError(f'frozen bundle changed: {key}')\n"
    "    for name in TCN_MEMBERS:\n"
    "        if rel['tcn_members_sha256'].get(name) != sha256(TCN_DIR / name):\n"
    "            raise ValueError(f'frozen network member changed: {name}')\n")
rep("        v21_model=V21_MODEL, v23_model=V23_MODEL, tcn_model=TCN_MODEL, release=RELEASE, pooled=True, add_players=True):\n",
    "        v21_model=V21_MODEL, v23_model=V23_MODEL, tcn_dir=TCN_DIR, release=RELEASE, pooled=True, add_players=True):\n")
rep("        tcn = tcn_probabilities(tcn_infer.load_weights(tcn_model), model_input, period)\n"
    "        p_dead, p_home = pooling.pool(tcn, p_dead, p_home)\n",
    "        members = sum((tcn_infer.load_weights(Path(tcn_dir) / name) for name in TCN_MEMBERS), [])      # change 5: eight members\n"
    "        tcn = tcn_probabilities(members, model_input, period)\n"
    "        p_dead, p_home = pooling.pool(tcn, p_dead, p_home, weight=TCN_WEIGHT)\n")
rep("        second = {'used': True, 'weights_sha256': sha256(tcn_model), 'pool': pooling.POOL, 'weight': pooling.WEIGHT}\n",
    "        second = {'used': True, 'weights_sha256': {name: sha256(Path(tcn_dir) / name) for name in TCN_MEMBERS}, 'members': len(members),\n"
    "                  'pool': pooling.POOL, 'weight': TCN_WEIGHT}\n")
rep("    report = {'rows': n, 'system': ('possession-v2.16 (v2.15 with the players the tactical tracking has lost added from the broadcast '\n"
    "                                    'tracking when the accuracy gate is open)'),\n",
    "    report = {'rows': n, 'system': ('possession-v2.17 (v2.16 with a second model of eight networks instead of three, weight 0.4 in the '\n"
    "                                    'pool on the v2.1 path)'),\n")
Path(sys.argv[1]).write_text(DOC + body, encoding='utf-8')
print('written', sys.argv[1])
