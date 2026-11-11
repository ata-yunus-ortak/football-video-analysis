#!/bin/bash
cd /home/claude/work
python3 precompute23.py _s23t v2.3 1 1,2,3 J03WOH J03WOY J03WPY J03WQQ > pre_s23t.log 2>&1
FTAG=_s23t python3 train1.py cache/models_v23.pkl > train_v23.log 2>&1 &
TP=$!
python3 precompute23.py _s23o v2 1 101,102 J03WN1 J03WR9 MET1 MET2 > pre_s23o.log 2>&1
python3 precompute23.py _s23b val-ext-ball 1 301,302 J03WN1 J03WR9 MET1 MET2 > pre_s23b.log 2>&1
wait $TP
python3 exp_stack.py _s23t cache/stack_v23.pkl > stack_v23.log 2>&1 &
SP=$!
python3 precompute23.py _s23p val-ext-players 1 501,502 J03WN1 J03WR9 MET1 MET2 > pre_s23p.log 2>&1
python3 precompute23.py _f2p val-ext-players 0 501,502 J03WN1 J03WR9 MET1 MET2 > pre_f2p.log 2>&1
wait $SP
echo READY > v23_ready.txt
