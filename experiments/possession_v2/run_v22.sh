#!/bin/bash
cd /home/claude/work
until grep -q DONE pre_f2v.log 2>/dev/null; do sleep 15; done
FTAG=_f2x python3 train1.py cache/models_v22.pkl > train_v22.log 2>&1
python3 exp_stack.py _f2x cache/stack_v22.pkl > stack_v22.log 2>&1
python3 eval_v22.py > eval_v22.log 2>&1
echo ALLDONE >> eval_v22.log
