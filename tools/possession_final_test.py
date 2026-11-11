"""Final test of the frozen possession release on the reserved external match (run once).

    python -m tools.possession_final_test --out <folder outside the repository>
    Windows: double-click SON-TEST.cmd

DFL match J03WMX was set aside on 7 November 2026 (sportec-data-plan.json, split "reserved_test") and has not
been downloaded since. This tool downloads the two registered files from the pinned public source, converts
them with the registered adapter (tools.sportec_prepare.convert), writes corrupted copies as tracking files in
the layout of the provided ATD, runs the frozen release entry point named in the plan (possession.run211)
on those files and scores the output against the provider's flags with the organisers' metric. The design is
registered in possession-final-test-plan.json before the match is accessed.

Nothing is selected here. The result is reported whatever it is; the release is not changed, retrained or
re-selected because of it. The match is public external data (DFL / Sportec, CC BY 4.0): unlike anything
about the provided match, the printed lines and the results file may be shared.

    --rehearsal NAME --prepared DIR   run the same evaluation on an already prepared development match (code
                                      check only; writes rehearsal-NAME.json to --out and nothing else)
"""
import argparse
import csv
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[1]
PLAN = REPO / 'possession-final-test-plan.json'
RESULTS = REPO / 'possession-final-test-results.json'
DATA_PLAN = REPO / 'sportec-data-plan.json'
ARCHIVE = REPO / 'experiments' / 'possession_v2'
SIMULATORS = ('synth_broadcast.py', 'synth_broadcast3.py', 'synth_clock.py')
# accuracy regimes of the simulated broadcast (bias s.d., ball s.d., player s.d. ranges in metres), as in every
# validation since possession-v25-plan.json (experiments/possession_v2/exp_v25.py)
REGIMES = {'good': ((0.0, 0.2), (0.05, 0.25), (0.05, 0.25)), 'medium': ((0.2, 0.6), (0.25, 0.5), (0.25, 0.5)),
           'bad': ((0.6, 1.5), (0.5, 1.0), (0.5, 1.0))}
REHEARSAL_SEED_OFFSET = 100000        # rehearsals never use a registered seed
RUNNER = ("import importlib, json, sys\n"
          "a = json.loads(sys.argv[1])\n"
          "importlib.import_module(a['module']).run(a['root'], a['out'], game='FINAL', halves=[tuple(h) for h in a['halves']],\n"
          "          tactical_clock=a.get('tactical_clock'), broadcast_clock=a.get('broadcast_clock'))\n")


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 22), b''):
            h.update(block)
    return h.hexdigest()


def simulators():
    """The stream and clock simulators of the validations (byte copies in experiments/possession_v2)."""
    if str(ARCHIVE) not in sys.path:
        sys.path.insert(0, str(ARCHIVE))
    import synth_broadcast
    import synth_broadcast3
    import synth_clock
    return synth_broadcast, synth_broadcast3, synth_clock


def acquire(out, data_plan, fixture, log=print):
    """Download (or find) and verify the two registered files of the reserved match. Returns {'meta', 'tracking'}."""
    from tools.metrica_data import verify_file
    files = [e for e in data_plan['files'] if e['fixture_id'] == fixture]
    if (data_plan.get('provided_fixture_used') is not False or len(files) != 2
            or any(e['split'] != 'reserved_test' for e in files)):
        raise ValueError('the registered reserved external match is required')
    raw = Path(out) / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    paths = {}
    for e in files:
        if Path(e['path']).name != e['path'] or e['url'] != data_plan['repository'] + '/resolve/' + data_plan['commit'] + '/' + e['path']:
            raise ValueError('unexpected pinned source path')
        path = raw / e['path']
        if not path.exists():
            log(f'downloading {e["path"]} ({e["bytes"] / 1e6:.0f} MB)')
            if e['sha256']:
                from tools.sportec_download import ranges
                ranges(e, path, 8)
            else:
                from tools.fresh_check import fetch
                fetch(e['url'], path, size=e['bytes'])
        if path.stat().st_size != e['bytes']:
            raise ValueError('wrong raw source size')
        if e['sha256']:
            if sha256(path) != e['sha256']:
                raise ValueError('wrong raw source SHA256')
        else:
            verify_file(path, e)
        paths['tracking' if 'positions_raw' in path.name else 'meta'] = path
    return paths


def prepare(out, paths, fixture, log=print):
    from tools.sportec_prepare import convert
    target = Path(out) / 'prepared' / fixture
    if not (target / 'report.json').exists():
        if target.exists():
            shutil.rmtree(target)                 # an unfinished conversion
        log('converting the provider files (several minutes)')
        convert(paths['meta'], paths['tracking'], target, 'DFL-MAT-' + fixture)
    return target


def baseline_labels(m, window=50):
    """The organisers' starter/baseline.py logic on the common representation: team of the nearest tracked player
    where the ball is seen, majority vote over +-window frames, D where nobody is seen in the window."""
    ball, players, team = m['ball'], m['players'], m['team']
    d = np.linalg.norm(players - ball[:, None], axis=2)
    d = np.where(np.isfinite(d), d, np.inf)
    j = np.argmin(d, 1)
    ok = np.isfinite(ball).all(1) & np.isfinite(d[np.arange(len(d)), j])
    codes = np.where(ok, team[j], -1)
    hc = np.concatenate(([0], np.cumsum(codes == 0)))
    ac = np.concatenate(([0], np.cumsum(codes == 1)))
    i = np.arange(len(codes))
    lo, hi = np.maximum(0, i - window), np.minimum(len(codes), i + window + 1)
    h, a = hc[hi] - hc[lo], ac[hi] - ac[lo]
    lab = np.full(len(codes), 'D', dtype='<U1')
    seen = (h + a) > 0
    lab[seen] = np.where(h[seen] >= a[seen], 'H', 'A')
    return lab


def quality(sb, rng, regime):
    q = sb.sample_quality(rng, 'default')
    (b0, b1), (s0, s1), (p0, p1) = REGIMES[regime]
    q.update(bias_sd=float(rng.uniform(b0, b1)), b_sd=float(rng.uniform(s0, s1)), p_sd=float(rng.uniform(p0, p1)))
    return q


def run_release(module, root, out, halves, clocks=None):
    """The frozen entry point (module name from the plan) in its own process, on the files below root.
    Returns (labels, run report)."""
    args = {'module': module, 'root': str(root), 'out': str(out), 'halves': [list(map(int, h)) for h in halves]}
    if clocks:
        args.update(tactical_clock=str(clocks[0]), broadcast_clock=str(clocks[1]))
    r = subprocess.run([sys.executable, '-c', RUNNER, json.dumps(args)], cwd=str(REPO), capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError('the release entry point failed:\n' + r.stderr[-2000:])
    with open(Path(out) / 'submission.csv', newline='', encoding='utf-8') as fh:
        rows = csv.reader(fh)
        next(rows)
        labels = np.array([row[1] for row in rows])
    return labels, json.loads((Path(out) / 'run.json').read_text(encoding='utf-8'))


def moved(rep):
    """What the goalkeeper team correction moved on this copy (entry points that have it)."""
    k = rep.get('goalkeeper_correction')
    return {'goalkeeper_pieces_moved': int(k['moved_pieces']), 'goalkeeper_frames_moved': int(k['moved_frames'])} if isinstance(k, dict) else {}


def _scores(r):
    return {'spell_f1': round(float(r['spell_f1_mean']), 4), 'macro_f1': round(float(r['macro_f1']), 4)}


def evaluate(prepared, plan, work, limit=None, regimes=None, seed_offset=0, log=print):
    """Rows of the registered design for one prepared match. Finished rows are kept in <work>/progress.json.
    seed_offset shifts every random seed (rehearsals use it, so that they never consume a registered seed)."""
    from possession.data import read_dfl_prepared
    from possession.degrade import degrade, sample_params, RANGES
    from possession.features import play_blocks
    from possession.evaluate import score
    from possession.epts_export import write_packed, write_homography
    sb, sb3, sc = simulators()
    d = plan['design']
    module = plan['release']['module']
    profiles = {'v2': RANGES, 'ext_players': dict(RANGES, player_sigma_m=(0.3, 0.6))}
    regimes = list(regimes or d['broadcast_regimes'])
    m, lab = read_dfl_prepared(prepared)
    per, fps, T = m['period'], float(m['fps']), len(m['period'])
    blocks = play_blocks(per)
    halves = [(k + 1, a, b - 1) for k, (a, b) in enumerate(blocks)]
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    progress = work / 'progress.json'
    rows = json.loads(progress.read_text()) if progress.exists() else []
    done = {(r['copy_index'], r['system']) for r in rows}
    t0 = time.time()

    def keep(row):
        rows.append(row)
        progress.write_text(json.dumps(rows, indent=1))
        log(f"[{(time.time() - t0) / 60:5.1f} min] copy {row['copy_index']} ({row['profile']}, seed {row['seed']}) "
            f"{row['system']:<18} spellF1 {row['spell_f1']:.4f}  macroF1 {row['macro_f1']:.4f}")

    for ci, c in enumerate(d['tactical_copies'][:limit]):
        systems = ['baseline logic', 'tactical only'] + [f'broadcast {r}' for r in regimes]
        if all((ci, s) in done for s in systems):
            continue
        seed = c['seed'] + seed_offset
        rng = np.random.default_rng(seed)
        dm = degrade(m, lab, rng, sample_params(rng, ranges=profiles[c['profile']]))
        root = work / f'copy{ci}'
        if root.exists():
            shutil.rmtree(root)
        peak = write_packed(root / 'tactical', 'FINAL_tactical', dm['players'], dm['ball'], dm['team'],
                            d['tactical_slots'], m['pitch'])
        common = {'copy_index': ci, 'profile': c['profile'], 'seed': seed}
        if (ci, 'baseline logic') not in done:
            keep(dict(common, system='baseline logic', **_scores(score(lab, baseline_labels(dm), per))))
        tac = None
        if (ci, 'tactical only') not in done:
            labels, rep = run_release(module, root, root / 'out-tactical', halves)
            tac = rep
            keep(dict(common, system='tactical only', model_path=rep['path'], peak_tracks_per_team=peak, **moved(rep),
                      measured_noise_m={k: round(v, 3) for k, v in rep['gate']['measured_noise'].items() if k.endswith('_m') and v is not None},
                      **_scores(score(lab, labels, per))))
        for ri, regime in enumerate(d['broadcast_regimes']):
            if regime not in regimes or (ci, f'broadcast {regime}') in done:
                continue
            rb = np.random.default_rng(d['stream_seed_base'] + seed_offset + 100 * ri + ci)
            q = quality(sb, rb, regime)
            bro, valid, _, clock_t = sb3.simulate_warp(m, lab, rb, q)
            bdir = root / 'broadcast'
            if bdir.exists():
                shutil.rmtree(bdir)
            write_packed(bdir, 'FINAL_broadcast', bro['players'], bro['ball'], bro['team'], d['broadcast_slots'], m['pitch'])
            write_homography(bdir / 'FINAL_broadcast_homography.csv', valid)
            rc = np.random.default_rng(d['clock_seed_base'] + seed_offset + 100 * ri + ci)
            pr_t, pr_b = rc.uniform(0.5, 0.95), rc.uniform(0.5, 0.95)
            pm_t, pm_b = rc.uniform(0.01, 0.03), rc.uniform(0.01, 0.03)
            clocks = []
            for name, live, pr, pm in (('clock-tactical', np.arange(T), pr_t, pm_t), ('clock-broadcast', clock_t, pr_b, pm_b)):
                cdir = root / name
                cdir.mkdir(exist_ok=True)
                (cdir / 'observations.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in sc.observations(live, blocks, fps, rc, pr, pm)))
                clocks.append(cdir)
            out = root / f'out-{regime}'
            if out.exists():
                shutil.rmtree(out)
            labels, rep = run_release(module, root, out, halves, clocks)
            f = rep['fusion']
            keep(dict(common, system=f'broadcast {regime}', model_path=rep['path'], fill_used=bool(rep['broadcast_fill_used']), **moved(rep),
                      alignment_mode=f.get('alignment_mode'), gate_median_distance_m=f.get('median_distance_m'),
                      broadcast_quality={k: round(float(q[k]), 3) for k in ('bias_sd', 'b_sd', 'p_sd', 'ball_frac', 'invalid')},
                      **_scores(score(lab, labels, per))))
            shutil.rmtree(bdir)
        shutil.rmtree(root)
        del dm
    labels = {k: int(np.sum(lab[per > 0] == k)) for k in 'HADX'}
    return rows, {'frames': int(T), 'play_frames': int((per > 0).sum()), 'labels_in_play': labels,
                  'halves': [[int(a), int(b)] for _, a, b in halves]}


def summarise(rows):
    out = {}
    for s in dict.fromkeys(r['system'] for r in rows):
        sel = [r for r in rows if r['system'] == s]
        out[s] = {'copies': len(sel), 'spell_f1': round(float(np.mean([r['spell_f1'] for r in sel])), 4),
                  'macro_f1': round(float(np.mean([r['macro_f1'] for r in sel])), 4)}
        if 'fill_used' in sel[0]:
            out[s]['gate_open_on_copies'] = int(sum(r['fill_used'] for r in sel))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--out', required=True, help='folder outside the repository (raw files, prepared match, working files)')
    p.add_argument('--rehearsal', help='name of a development match: code check only')
    p.add_argument('--prepared', help='prepared folder of the development match (with --rehearsal)')
    p.add_argument('--limit', type=int, help='number of copies (only with --rehearsal)')
    p.add_argument('--regimes', nargs='+', help='broadcast regimes (only with --rehearsal)')
    a = p.parse_args(argv)
    import importlib
    from tools.metrica_data import external_output
    out = external_output(a.out)
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    entry = importlib.import_module(plan['release']['module'])
    rel = entry.check_release()
    if sha256(entry.RELEASE) != plan['release']['manifest_sha256'] or rel['version'] != plan['release']['name']:
        print('The release is not the one named in the registered plan.')
        return 1
    sims = {n: sha256(ARCHIVE / n) for n in SIMULATORS}
    if sims != plan['simulator_sha256']:
        print('The simulators differ from the registered plan.')
        return 1
    if a.rehearsal:
        if not a.prepared:
            p.error('--rehearsal needs --prepared')
        name, prepared, fixture = f'rehearsal-{a.rehearsal}', Path(a.prepared), a.rehearsal
        provenance = {'note': 'code check on a development match; NOT the final test'}
    else:
        if a.limit or a.regimes or a.prepared:
            p.error('--limit, --regimes and --prepared are for --rehearsal only')
        if RESULTS.exists():
            print(f'The final test has already been run: {RESULTS.name} exists. It is run once.')
            return 1
        fixture = plan['fixture']['id']
        name = 'final'
        paths = acquire(out, json.loads(DATA_PLAN.read_text(encoding='utf-8')), fixture)
        prepared = prepare(out, paths, fixture)
        report = json.loads((prepared / 'report.json').read_text(encoding='utf-8'))
        provenance = {'raw_sha256': report['raw_sha256'], 'inputs_sha256': report['inputs_sha256'], 'targets_sha256': report['targets_sha256'],
                      'adapter_sha256': report['adapter_sha256'], 'provider_label_counts': report['labels']}
    t0 = time.time()
    rows, facts = evaluate(prepared, plan, out / f'work-{name}', a.limit, a.regimes, seed_offset=REHEARSAL_SEED_OFFSET if a.rehearsal else 0)
    result = {
        'record': 'possession final test on the reserved external match' if not a.rehearsal else 'REHEARSAL of the final-test tool (not the final test)',
        'written_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'plan': PLAN.name, 'plan_sha256': sha256(PLAN),
        'fixture': dict({'id': fixture}, **facts, **provenance),
        'release': {'name': rel['version'], 'manifest_sha256': sha256(entry.RELEASE),
                    'entry_point': plan['release']['module'] + '.run on files written from each copy'},
        'tool_sha256': sha256(__file__), 'tool_as_registered': sha256(__file__) == plan['tool']['sha256'],
        'simulator_sha256': sims,
        'environment': {'platform': platform.platform(), 'python': platform.python_version(), 'numpy': np.__version__},
        'means': summarise(rows), 'rows': rows,
        'minutes': round((time.time() - t0) / 60, 1),
        'decision': 'none: reported as measured; the release is not changed by this result',
        'provided_fixture_used': False, 'not_a_competition_score': True,
    }
    text = json.dumps(result, indent=1) + '\n'
    (out / f'{name}-results.json').write_text(text, encoding='utf-8')
    if not a.rehearsal:
        RESULTS.write_text(text, encoding='utf-8')
    print()
    for s, v in result['means'].items():
        gate = f"  (gate open on {v['gate_open_on_copies']} of {v['copies']})" if 'gate_open_on_copies' in v else ''
        print(f"{s:<18} spellF1 {v['spell_f1']:.4f}  macroF1 {v['macro_f1']:.4f}{gate}")
    print(f"\nWritten: {RESULTS if not a.rehearsal else out / (name + '-results.json')}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
