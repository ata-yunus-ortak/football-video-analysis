cd /Users/umut/BARCELONA/work/v216u
for n in MET1 MET2; do for part in 0; do ../.venv/bin/python scan23.py $n 14 > dev23/scan_$n.log 2>&1 & done; done; wait
export DEVD=/Users/umut/BARCELONA/work/v216u/dev23/
cd /Users/umut/BARCELONA/football-video-analysis; export PYTHONPATH=.
W=../work/v216u/weights
../work/.venv/bin/python ../work/v216u/fwd216.py 'MET*' $W/d6_a_s[0-3].npz $W/d6_f_s[0-3].npz /Users/umut/BARCELONA/wt-ata/models/possession-tcn-v215.npz
echo SCAN23 DONE
