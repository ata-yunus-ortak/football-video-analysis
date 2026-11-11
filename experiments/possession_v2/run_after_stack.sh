#!/bin/bash
cd /home/claude/work
until grep -q ALLDONE eval_stack_v2.log 2>/dev/null; do sleep 15; done
python3 grid2.py stack_v2_f2 > grid2_stack_v2.log 2>&1
echo ALLDONE >> grid2_stack_v2.log
