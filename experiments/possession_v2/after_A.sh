#!/bin/bash
# sequential: one heavy job at a time
P=/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova
PY=/home/claude/venv310/bin/python
cd /home/claude/sc
mkdir -p $P/A/view && ln -sfn $P/A/bundle/tactical $P/A/view/tactical
echo "== R3 tactical-only entry point on the packed bundle $(date -Iseconds)"
python3 $P/rss_run.py $PY -m possession.run25c --data-dir $P/A/view --out $P/A/r3 > $P/logs/r3.log 2>&1; tail -1 $P/logs/r3.log
$PY $P/score_prova.py $P/A/truth.npz $P/A/r3/submission.csv > $P/A/r3_score.json
echo "== R1 in-memory reference $(date -Iseconds)"
python3 $P/rss_run.py $PY $P/r1.py $P/A/truth.npz $P/A/r1.csv > $P/logs/r1.log 2>&1; tail -2 $P/logs/r1.log
$PY $P/score_prova.py $P/A/truth.npz $P/A/r1.csv > $P/A/r1_score.json
echo "== reserve configuration (v2.9g) chain $(date -Iseconds)"
mkdir -p $P/A/private_g && cp -r $P/A/private/possession-clock $P/A/private_g/
python3 $P/rss_run.py $PY -m tools.possession_deliver --python $PY --private $P/A/private_g --data-dir $P/A/bundle --team Prova --organiser-repo /home/claude/org/repo --no-public-check --no-clone-check --no-tests --quick --release-config possession-release-graded-windows.json > $P/logs/chain_Ag.log 2>&1
cat $P/logs/chain_Ag.log
$PY $P/score_prova.py $P/A/truth.npz $P/A/private_g/teslim/Prova.csv > $P/A/v29g_score.json
echo "== slot / duplicate stress $(date -Iseconds)"
$PY /home/claude/work/stress_slots.py /home/claude/work/stress_slots.json > /home/claude/work/stress_slots.log 2>&1
echo "== ALLDONE $(date -Iseconds)"
