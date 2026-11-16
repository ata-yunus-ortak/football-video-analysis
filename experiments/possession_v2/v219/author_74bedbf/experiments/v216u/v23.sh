cd /Users/umut/BARCELONA/work/v216u
export V23=1
for m in J03WOH J03WOY J03WPY J03WQQ; do ../.venv/bin/python v2val.py feats $m > v2cache/feats23_$m.log 2>&1 & done; wait
../.venv/bin/python v2val.py fit > v2cache/fit23.log 2>&1
unset V23
for n in J03WN1 J03WR9; do ../.venv/bin/python scan23.py $n 14 > dev23/scan_$n.log 2>&1 & done; wait
export DEVD=/Users/umut/BARCELONA/work/v216u/dev23/
cd /Users/umut/BARCELONA/football-video-analysis; export PYTHONPATH=.
W=../work/v216u/weights
../work/.venv/bin/python ../work/v216u/fwd216.py 'J03*' $W/d4_a_s[0-3].npz $W/d4_f_s[0-3].npz
cd /Users/umut/BARCELONA/work/v216u
PAT='J03*' ../.venv/bin/python score23.py 0.2,0.3,0.4,0.5 A4F4=a_s0,a_s1,a_s2,a_s3,f_s0,f_s1,f_s2,f_s3 A4=a_s0,a_s1,a_s2,a_s3
echo V23 DONE
