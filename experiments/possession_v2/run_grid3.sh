#!/bin/bash
cd /home/claude/work
python3 grid3.py models_v2_f2 > grid3_v2.log 2>&1; echo ALLDONE >> grid3_v2.log
python3 grid3.py stack_v2_f2 > grid3_stack.log 2>&1; echo ALLDONE >> grid3_stack.log
