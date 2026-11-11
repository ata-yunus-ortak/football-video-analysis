#!/bin/bash
# Sequential queue (one heavy job at a time; cgroup limit ~6.2 GB). Tags experiment dropped:
# Smart Tagging is not selectable under possession-v2-plan.json (no external validation possible).
cd /home/claude/work
while kill -0 8216 2>/dev/null || pgrep -f "precompute2.py" >/dev/null; do sleep 10; done
python3 eval_stack.py cache/models_v2.pkl cache/stack_v2.pkl _f2 > eval_stack_v2.log 2>&1
echo ALLDONE >> eval_stack_v2.log
FTAG=_f3 python3 train1.py cache/models_v3.pkl > train_v3.log 2>&1
FTAG=_f3 python3 eval3.py cache/models_v3.pkl > eval_v3.log 2>&1
python3 grid2.py models_v3_f3 > grid2_v3.log 2>&1
echo ALLDONE >> grid2_v3.log
python3 stress2.py cache/models_v2.pkl '{"switch": 5.0, "out_cost": 120.0, "in_cost": 120.0, "bias_dead": -0.3}' > stress2_v2.log 2>&1
echo ALLDONE >> stress2_v2.log
