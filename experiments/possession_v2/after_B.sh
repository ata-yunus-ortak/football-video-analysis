#!/bin/bash
# waits for the first queue, then: harder rehearsal bundle (noisy players -> v2.3 path; broadcast with a larger calibration error)
P=/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova
PY=/home/claude/venv310/bin/python
until grep -q ALLDONE $P/logs/after_A.log; do sleep 10; done
cd $P && echo "== build B $(date -Iseconds)" && $PY prova_build.py $P/B --profile hard --seed 20261112 > $P/logs/build_B.log 2>&1; tail -1 $P/logs/build_B.log
cd /home/claude/sc
echo "== inputs B"; $PY -m possession.inputs_check --data-dir $P/B/bundle | grep -c PASS
echo "== chain B (quick) $(date -Iseconds)"
python3 $P/rss_run.py $PY -m tools.possession_deliver --python $PY --private $P/B/private --data-dir $P/B/bundle --team Prova --organiser-repo /home/claude/org/repo --no-public-check --no-clone-check --no-tests > $P/logs/chain_B.log 2>&1
cat $P/logs/chain_B.log
$PY $P/score_prova.py $P/B/truth.npz $P/B/private/teslim/Prova.csv > $P/B/v29_score.json
mkdir -p $P/B/view && ln -sfn $P/B/bundle/tactical $P/B/view/tactical
echo "== B tactical only $(date -Iseconds)"
$PY -m possession.run25c --data-dir $P/B/view --out $P/B/r3 > $P/logs/r3_B.log 2>&1
$PY $P/score_prova.py $P/B/truth.npz $P/B/r3/submission.csv > $P/B/r3_score.json
echo "== B in-memory reference $(date -Iseconds)"
$PY $P/r1.py $P/B/truth.npz $P/B/r1.csv > $P/logs/r1_B.log 2>&1; tail -1 $P/logs/r1_B.log
$PY $P/score_prova.py $P/B/truth.npz $P/B/r1.csv > $P/B/r1_score.json
echo "== BDONE $(date -Iseconds)"
