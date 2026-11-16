cd /Users/umut/BARCELONA/work/v216u
for n in J03WN1 J03WR9 MET1 MET2; do ../.venv/bin/python holdfill.py $n > holdfill/prep_$n.log 2>&1 & done; wait
export DEVD=/Users/umut/BARCELONA/work/v216u/holdfill/
cd /Users/umut/BARCELONA/football-video-analysis; export PYTHONPATH=.
W=../work/v216u/weights
../work/.venv/bin/python ../work/v216u/fwd216.py 'MET*' $W/d6_a_s[0-3].npz $W/d6_f_s[0-3].npz /Users/umut/BARCELONA/wt-ata/models/possession-tcn-v215.npz
../work/.venv/bin/python ../work/v216u/fwd216.py 'J03*' $W/d4_a_s[0-3].npz $W/d4_f_s[0-3].npz
cd /Users/umut/BARCELONA/work/v216u
../.venv/bin/python grid216.py holdfill/grid_fill.json 0.4,0.3,0.2 A4F4=a_s0,a_s1,a_s2,a_s3,f_s0,f_s1,f_s2,f_s3 HIS=HIS
echo HOLDFILL DONE
