#!/bin/bash
while ! grep -q ALLDONE pre2_val.log 2>/dev/null; do sleep 10; done
while pgrep -f "eval2.py" >/dev/null; do sleep 10; done
FTAG=_f2 python3 train1.py cache/models_v2.pkl > train_v2.log 2>&1
FTAG=_f2 python3 eval3.py cache/models_v2.pkl > eval_v2.log 2>&1
echo ALLDONE >> eval_v2.log
