#!/bin/bash
cd /home/claude/work
# unsmoothed (v2.1 path + gate estimates) and smoothed (v2.3 path) in two parallel lanes
( python3 pre24.py _g21 v2 0 1100 && python3 pre24.py _g21 val-ext-ball 0 1300 && python3 pre24.py _g21 val-ext-players 0 1500 ) > pre_g21.log 2>&1 &
A=$!
( python3 pre24.py _g23 v2 1 1100 && python3 pre24.py _g23 val-ext-ball 1 1300 && python3 pre24.py _g23 val-ext-players 1 1500 ) > pre_g23.log 2>&1 &
B=$!
wait $A $B
echo READY > v24_ready.txt
