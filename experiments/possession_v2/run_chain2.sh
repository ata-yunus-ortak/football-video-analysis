#!/bin/bash
cd /home/claude/work
while ! grep -q ALLDONE eval_v2.log 2>/dev/null; do sleep 10; done
python3 exp_stack.py _f2 cache/stack_v2.pkl > stack_v2.log 2>&1
python3 eval_stack.py cache/models_v2.pkl cache/stack_v2.pkl _f2 > eval_stack_v2.log 2>&1
echo ALLDONE >> eval_stack_v2.log
python3 exp_tags.py cache/tags_v2_sp.pkl sp_only > tags_v2.log 2>&1
python3 eval_tags.py cache/tags_v2_sp.pkl models_v2_f2 > eval_tags_v2.log 2>&1
echo ALLDONE >> eval_tags_v2.log
