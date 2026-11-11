#!/bin/bash
cd /home/claude/work
while kill -0 12380 2>/dev/null; do sleep 10; done
grep -q ALLDONE reserved_test.log || { echo "reserved test missing" > post.log; exit 1; }
DEC='{"switch": 3, "out_cost": 60, "in_cost": 60, "bias_dead": -0.3}'
python3 stress.py cache/models_v2.pkl "$DEC" cache/stack_v2.pkl /home/claude/work/stress_final.json > stress_final.log 2>&1
python3 stress2.py cache/models_v2.pkl "$DEC" cache/stack_v2.pkl /home/claude/work/stress2_final.json > stress2_final.log 2>&1
python3 assemble_final.py /home/claude/sc/possession-v2-results.json possession-v2.1 stack_v2_f2 "$DEC" > assemble.log 2>&1
echo ALLDONE >> assemble.log
