#!/bin/bash
# wait for training to finish to avoid memory pressure, then precompute v2 features sequentially
while pgrep -f "train1.py" >/dev/null; do sleep 5; done
python3 precompute2.py J03WOH,J03WOY,J03WPY,J03WQQ 1,2,3 _f2 > pre2_train.log 2>&1
python3 precompute2.py J03WN1,J03WR9,MET1,MET2 101,102 _f2 > pre2_val.log 2>&1
echo ALLDONE >> pre2_val.log
