import sys, json, numpy as np, time
sys.path.insert(0, '/home/claude/work/v217')
import taglib as T
E = T.E
regimes = sys.argv[1].split(',') if len(sys.argv) > 1 else ['clean', 'default', 'noisy', 'false30', 'second']
VAR = {'c inf': dict(cmax=1e9), 'c 120': dict(cmax=120), 'c 110': dict(cmax=110), 'c 100': dict(cmax=100), 'c 90': dict(cmax=90), 'c 60': dict(cmax=60),
       'c 100 bridge 3': dict(cmax=100, bridge=3.0), 'c 100 pre 8': dict(cmax=100, pre=8.0), 'c 100 pre 3': dict(cmax=100, pre=3.0),
       'c 100 post 2': dict(cmax=100, post=2.0), 'c 100 min 25': dict(cmax=100, minlen=25)}
data = [E.load(f) for f in E.copies()]
base = [(E.f1_of(d['lab'], d['pred'], d['per']), T.macro_f1(d['lab'], d['pred'], d['per'])) for d in data]
# sanity: a plain re-decode of the pooled probabilities gives the stored decision
d = data[0]
st = T.rescue(d['pd2'], d['ph2'], d['pred'], d['per'], [], E.DEC)[0]
assert (st == d['pred']).all()
res = {}
for reg in regimes:
    for nm, kw in VAR.items():
        dv, dm, acted, hit, cost_t, cost_f = [], [], [], [], [], []
        for i, d in enumerate(data):
            rng = np.random.default_rng(910000 + 1000 * list(T.REG).index(reg) + i)
            tags = T.sim_tags(d['match'], d['lab'], d['per'], rng, reg)
            out, rep = T.rescue(d['pd2'], d['ph2'], d['pred'], d['per'], tags, E.DEC, **kw)
            dv.append(E.f1_of(d['lab'], out, d['per']) - base[i][0]); dm.append(T.macro_f1(d['lab'], out, d['per']) - base[i][1])
            f = [r for r in rep if r[4] == 'forced']
            acted.append(len(f))
            for r in f:
                k = r[6]
                ok = d['lab'][max(0, k - 25):k + 26].tolist().count('D') > 0          # a true dead frame within 1 s of the forced frame
                hit.append(ok); (cost_t if ok else cost_f).append(r[5])
        dv, dm = np.array(dv), np.array(dm)
        isd = np.array([d['match'].startswith('J03') for d in data])
        res[f'{reg}|{nm}'] = dict(mean=float(dv.mean()), dfl=float(dv[isd].mean()), met=float(dv[~isd].mean()), min=float(dv.min()), max=float(dv.max()),
                                 better=int((dv > 1e-9).sum()), worse=int((dv < -1e-9).sum()), macro=float(dm.mean()), acted=float(np.mean(acted)),
                                 precision=float(np.mean(hit)) if hit else None)
        r = res[f'{reg}|{nm}']
        print(f'{reg:8s} {nm:16s} mean {r["mean"]:+.4f} DFL {r["dfl"]:+.4f} MET {r["met"]:+.4f} min {r["min"]:+.4f} max {r["max"]:+.4f} better/worse {r["better"]}/{r["worse"]} '
              f'macro {r["macro"]:+.4f} forced/copy {r["acted"]:.1f} precision {r["precision"] if r["precision"] is None else round(r["precision"], 2)}', flush=True)
json.dump(res, open(f'rule1_{"_".join(regimes)}.json', 'w'), indent=0)
