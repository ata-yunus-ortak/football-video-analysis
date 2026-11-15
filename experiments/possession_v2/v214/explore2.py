"""Development on copies already scored in the v2.13 validation (NOT a validation): pooling rules through fuse2.pool and
the v2 decoder, for an ensemble of re-trained TCN members whose probabilities were stored by retcn2.py.
Usage: explore2.py OUTNAME DFL_TAGS MET_TAGS [pattern]     tags: comma-separated member tags, or 'his' for the stored
probabilities of the teammate's weights."""
import sys, glob, json, os, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/work/v213'); sys.path.insert(0, '/home/claude/sc'); sys.path.insert(0, '/home/claude/work/v214')
from possession.decode import emissions, decode_blocks, LETTERS
from possession.features import play_blocks
from possession.evaluate import score
from tcn.decode import viterbi as his_viterbi
import lib214 as L
import fuse2
import exp_v25

OUR = {'v2.1': {'switch': 3, 'out_cost': 60, 'in_cost': 60, 'bias_dead': -0.3}}
for k, v in exp_v25.PATHS.items():
    OUR[k] = v[2]
GRID = [('arithmetic', w) for w in (0.2, 0.3, 0.4, 0.5, 0.6)] + [('geometric', w) for w in (0.3, 0.4, 0.5, 0.6)]


def dec_his(mixed, per, cost=6.0):
    out = np.full(len(per), 'D', dtype='<U1')
    for a, b in play_blocks(per):
        out[a:b] = LETTERS[his_viterbi(np.log(np.clip(mixed[a:b], 1e-6, 1.0)), cost)]
    return out


def variants(d, tcn, extra_decoders=()):
    per = d['per']; path = str(d['path'])
    out = {'v2_11': d['v2_labels'], 'tcn_alone': dec_his(tcn, per, 6.0),
           'v213rule': dec_his(0.5 * tcn + 0.5 * fuse2.three_class(d['p_dead'], d['p_home']), per, 6.0)}
    for kind, w in GRID:
        pd_, ph = fuse2.pool(tcn, d['p_dead'], d['p_home'], w, kind)
        out[f'{kind[:3]}{int(w * 100)}'] = decode_blocks(emissions(pd_, ph), per, OUR[path])
        for name, par in extra_decoders:
            out[f'{kind[:3]}{int(w * 100)}_{name}'] = decode_blocks(emissions(pd_, ph), per, dict(OUR[path], **par))
    return out


if __name__ == '__main__':
    outname, tags_dfl, tags_met = sys.argv[1], sys.argv[2], sys.argv[3]
    pat = sys.argv[4] if len(sys.argv) > 4 else '*'
    extra = [('sw4', {'switch': 4}), ('sw5', {'switch': 5})] if os.environ.get('DECODERS') else []
    rows = {}
    for f in sorted(glob.glob(L.PROBS + pat + '.npz')):
        if f.endswith('.feat.npz') or '.m_' in f:
            continue
        key = os.path.basename(f)[:-4]
        tags = tags_dfl if key.startswith('J03') else tags_met
        d = dict(np.load(f, allow_pickle=False))
        if tags == 'his':
            tcn = d['tcn'].astype(np.float64)
        else:
            files = [f[:-4] + '.m_' + t + '.npz' for t in tags.split(',')]
            if not all(os.path.exists(x) for x in files):
                continue
            tcn = L.ensemble_tcn(files, d['per'])
        V = variants(d, tcn, extra)
        rows[key] = {k: (lambda s: (float(s['spell_f1_mean']), float(s['macro_f1'])))(score(d['lab'], v, d['per'])) for k, v in V.items()}
        print(key, ' '.join(f"{k}={v[0]:.4f}" for k, v in rows[key].items()), flush=True)
    json.dump(rows, open(f'/home/claude/work/v214/explore2_{outname}.json', 'w'), indent=1)
    names = list(next(iter(rows.values())).keys())
    groups = {'all': list(rows), 'DFL': [k for k in rows if k.startswith('J03')], 'MET': [k for k in rows if k.startswith('MET')],
              'ours (tactical)': [k for k in rows if k.endswith('_tactical')], 'his simulator': [k for k in rows if k.endswith('sim2')]}
    for g, ks in groups.items():
        if not ks:
            continue
        print(f'\n== {g}: n = {len(ks)}; mean spellF1 difference to v2_11 | min | copies better | copies below -0.010 | macro')
        for nm in names:
            dsp = np.array([rows[k][nm][0] - rows[k]['v2_11'][0] for k in ks]); dm = np.array([rows[k][nm][1] - rows[k]['v2_11'][1] for k in ks])
            print(f"  {nm:14s} {dsp.mean():+.4f}  {dsp.min():+.4f}  {int((dsp > 0).sum()):2d}/{len(ks)}  {int((dsp < -0.010).sum())}  {dm.mean():+.4f}")
