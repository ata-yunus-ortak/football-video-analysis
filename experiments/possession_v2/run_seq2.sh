#!/bin/bash
cd /home/claude/work
python3 eval_stack.py cache/models_v2.pkl cache/stack_v2.pkl _f2 > eval_stack_v2.log 2>&1
echo ALLDONE >> eval_stack_v2.log
FTAG=_f3 python3 train1.py cache/models_v3.pkl > train_v3.log 2>&1
FTAG=_f3 python3 eval3.py cache/models_v3.pkl > eval_v3.log 2>&1
python3 grid2.py models_v3_f3 > grid2_v3.log 2>&1
echo ALLDONE >> grid2_v3.log
