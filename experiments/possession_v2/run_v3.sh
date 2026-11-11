#!/bin/bash
cd /home/claude/work
while pgrep -f "stress.py" >/dev/null; do sleep 10; done
python3 precompute2.py J03WOH,J03WOY,J03WPY,J03WQQ 1,2,3 _f3 > pre3_train.log 2>&1
python3 precompute2.py J03WN1,J03WR9,MET1,MET2 101,102 _f3 > pre3_val.log 2>&1
while pgrep -f "exp_stack.py|eval_stack.py|exp_tags.py|eval_tags.py" >/dev/null; do sleep 10; done
FTAG=_f3 python3 train1.py cache/models_v3.pkl > train_v3.log 2>&1
FTAG=_f3 python3 eval3.py cache/models_v3.pkl > eval_v3.log 2>&1
python3 grid2.py models_v3_f3 > grid2_v3.log 2>&1
echo ALLDONE >> grid2_v3.log
