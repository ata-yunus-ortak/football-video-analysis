cd /home/claude/work
python3 pre27.py _n4 v2 0 J03WN1:7100 J03WN1:7101 J03WR9:7110 J03WR9:7111 MET1:7120 MET1:7121 MET2:7130 MET2:7131
python3 precompute23.py _n2 v2 0 7100,7101 J03WN1
python3 precompute23.py _n2 v2 0 7110,7111 J03WR9
python3 precompute23.py _n2 v2 0 7120,7121 MET1
python3 precompute23.py _n2 v2 0 7130,7131 MET2
echo LANEDONE
