# One check of the frozen candidate on new seeds (copy seeds 23100 + 10 * match + j, second simulator 73100 + match).
cd /Users/umut/BARCELONA/work/v216u
export DEVD=/Users/umut/BARCELONA/work/v216u/hold/ DEVSETS="((23100, 73100),)"
for n in J03WN1 J03WR9 MET1 MET2; do (../.venv/bin/python dev216.py prep $n > hold/prep_$n.log 2>&1; ../.venv/bin/python devfeat.py 2 $n > hold/feat2_$n.log 2>&1) & done
for n in J03WN1 J03WR9; do ../.venv/bin/python v2dfl.py $n > hold/v2dfl_$n.log 2>&1 & done
wait
cd /Users/umut/BARCELONA/football-video-analysis; export PYTHONPATH=.
W=../work/v216u/weights
../work/.venv/bin/python ../work/v216u/fwd216.py 'MET*' $W/d6_a_s[0-3].npz $W/d6_f_s[0-3].npz /Users/umut/BARCELONA/wt-ata/models/possession-tcn-v215.npz
../work/.venv/bin/python ../work/v216u/fwd216.py 'J03*' $W/d4_a_s[0-3].npz $W/d4_f_s[0-3].npz
cd /Users/umut/BARCELONA/work/v216u
../.venv/bin/python grid216.py hold/grid_hold.json 0.4,0.3,0.2 A4F4=a_s0,a_s1,a_s2,a_s3,f_s0,f_s1,f_s2,f_s3 A4=a_s0,a_s1,a_s2,a_s3 HIS=HIS
echo HOLD DONE
