#!/bin/bash
cd /home/claude/work
python3 exp_v4.py default > exp_v4_default.log 2>&1; echo ALLDONE >> exp_v4_default.log
python3 exp_v4.py bad > exp_v4_bad.log 2>&1; echo ALLDONE >> exp_v4_bad.log
