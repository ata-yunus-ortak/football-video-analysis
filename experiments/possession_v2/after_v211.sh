#!/bin/bash
# After the decision and the freeze: reserved Metrica game 3 (reporting only), full-size rehearsals. One heavy job at a time.
S=/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad
P=$S/prova; PY=/home/claude/venv310/bin/python
cd /home/claude/sc
echo "== reserved Metrica game 3 (seed 31103), once $(date -Iseconds)"
(cd /home/claude/work && /usr/bin/python3 exp_v211.py reserved > exp_v211_reserved.log 2>&1); tail -8 /home/claude/work/exp_v211_reserved.log
for G in G1:tactical G2:both; do
  name=${G%%:*}; feeds=${G##*:}
  echo "== build $name (goalkeepers exchanged in: $feeds) $(date -Iseconds)"
  /usr/bin/python3 $P/prova_gk.py $P/$name --feeds $feeds > $P/logs/build_$name.log 2>&1; tail -1 $P/logs/build_$name.log
done
$PY - <<'PYEOF'
import numpy as np
P = '/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova'
a = np.load(P + '/A/truth.npz')
for g in ('G1', 'G2'):
    z = np.load(f'{P}/{g}/truth.npz')
    print(g, 'truth copy equals bundle A:', {k: bool(np.array_equal(a[k], z[k], equal_nan=True)) if a[k].dtype.kind == 'f' else bool(np.array_equal(a[k], z[k])) for k in a.files})
PYEOF
run() {   # bundle, module, tag
  python3 $P/rss_run.py $PY -m possession.$2 --data-dir $P/$1/bundle --out $P/$1/out-$2 --tactical-clock $P/$1/private/possession-clock/tactical --broadcast-clock $P/$1/private/possession-clock/broadcast > $P/logs/$1_$2.log 2>&1
  tail -1 $P/logs/$1_$2.log
  $PY $P/score_prova.py $P/$1/truth.npz $P/$1/out-$2/submission.csv > $P/$1/score_$2.json
  $PY -c "
import json; s = json.load(open('$P/$1/score_$2.json')); r = json.load(open('$P/$1/out-$2/run.json'))
print('$1 $2', s['graded windows (as the organisers grade)']['spell_f1_mean'], s['graded windows (as the organisers grade)']['macro_f1'], 'path', r['path'], 'fill', r['broadcast_fill_used'], 'moved', (r.get('goalkeeper_correction') or {}).get('moved_pieces'), (r.get('goalkeeper_correction') or {}).get('moved_frames'))"
}
echo "== entry points on G1 $(date -Iseconds)"; run G1 run211; run G1 run29
echo "== entry point on G2 $(date -Iseconds)"; run G2 run211
echo "== v2.11 entry point on bundle A (ids as corrupted) $(date -Iseconds)"; run A run211
echo "== chain on bundle A with the v2.11 release $(date -Iseconds)"
rm -rf $P/A/private_v211 && mkdir -p $P/A/private_v211 && cp -r $P/A/private/possession-clock $P/A/private_v211/
python3 $P/rss_run.py $PY -m tools.possession_deliver --python $PY --private $P/A/private_v211 --data-dir $P/A/bundle --team Prova --organiser-repo /home/claude/org/repo --no-public-check --no-clone-check > $P/logs/chain_A_v211.log 2>&1
cat $P/logs/chain_A_v211.log
$PY $P/score_prova.py $P/A/truth.npz $P/A/private_v211/teslim/Prova.csv > $P/A/v211_score.json
echo "== chain on bundle G1 with the v2.11 release, quick $(date -Iseconds)"
rm -rf $P/G1/private_chain && mkdir -p $P/G1/private_chain && cp -r $P/G1/private/possession-clock $P/G1/private_chain/
python3 $P/rss_run.py $PY -m tools.possession_deliver --python $PY --private $P/G1/private_chain --data-dir $P/G1/bundle --team Prova --organiser-repo /home/claude/org/repo --no-public-check --no-clone-check --no-tests --quick > $P/logs/chain_G1_v211.log 2>&1
cat $P/logs/chain_G1_v211.log
$PY $P/score_prova.py $P/G1/truth.npz $P/G1/private_chain/teslim/Prova.csv > $P/G1/chain_score.json
echo "== reserve configuration (v2.11g) chain on bundle A, quick $(date -Iseconds)"
rm -rf $P/A/private_v211g && mkdir -p $P/A/private_v211g && cp -r $P/A/private/possession-clock $P/A/private_v211g/
python3 $P/rss_run.py $PY -m tools.possession_deliver --python $PY --private $P/A/private_v211g --data-dir $P/A/bundle --team Prova --organiser-repo /home/claude/org/repo --no-public-check --no-clone-check --no-tests --quick --release-config possession-release-graded-windows.json > $P/logs/chain_A_v211g.log 2>&1
cat $P/logs/chain_A_v211g.log
$PY $P/score_prova.py $P/A/truth.npz $P/A/private_v211g/teslim/Prova.csv > $P/A/v211g_score.json
echo "== AFTERDONE $(date -Iseconds)"
