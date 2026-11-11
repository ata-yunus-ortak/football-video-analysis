#!/bin/bash
cd /home/claude/work
while kill -0 10898 2>/dev/null; do sleep 10; done
python3 grid3.py models_v3_f3 > grid3_v3.log 2>&1; echo ALLDONE >> grid3_v3.log
python3 exp_stack.py _f3 cache/stack_v3.pkl > stack_v3.log 2>&1
python3 eval_stack.py cache/models_v3.pkl cache/stack_v3.pkl _f3 stack_v3_f3 > eval_stack_v3.log 2>&1; echo ALLDONE >> eval_stack_v3.log
python3 grid3.py stack_v3_f3 > grid3_stack_v3.log 2>&1; echo ALLDONE >> grid3_stack_v3.log
