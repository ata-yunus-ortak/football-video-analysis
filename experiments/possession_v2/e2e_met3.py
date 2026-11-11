"""Full-size production-path check on an external EPTS file (Metrica sample game 3 tracking only;
no labels read): reader with 11 DataFormatSpecifications, both stages, decoder, validator.
Reports runtime, peak memory and the output hash (to compare numpy versions)."""
import sys, os, time, json, resource, tempfile
from pathlib import Path
sys.path.insert(0, '/home/claude/sc')
from possession import run as runmod
from possession.data import read_epts
src = Path('/home/claude/ext/sd/data/Sample_Game_3')
with tempfile.TemporaryDirectory() as d:
    tac = Path(d) / 'bundle' / 'tactical'; tac.mkdir(parents=True)
    os.symlink(src / 'Sample_Game_3_metadata.xml', tac / 'MET3_tactical_atd.xml')
    os.symlink(src / 'Sample_Game_3_tracking.txt', tac / 'MET3_tactical_atd.txt')
    _, info = read_epts(tac / 'MET3_tactical_atd.xml', tac / 'MET3_tactical_atd.txt')
    p = info['provider_parameters']
    halves = [(1, int(p['first_half_start']) - 1, int(p['first_half_end']) - 1),
              (2, int(p['second_half_start']) - 1, int(p['second_half_end']) - 1)]
    t = time.time()
    rep = runmod.run(Path(d) / 'bundle', Path(d) / 'out', game='MET3', halves=halves)
    dt = time.time() - t
    from possession.validate import check
    ok, vinfo = check(Path(d) / 'out' / 'submission.csv', rows=rep['rows'])
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
print('E2E', json.dumps({'python': sys.version.split()[0], 'numpy': __import__('numpy').__version__,
                         'rows': rep['rows'], 'seconds': round(dt, 1), 'peak_rss_gb': round(peak, 2),
                         'validator_ok': ok, 'teams': rep['teams'], 'submission_sha256': rep['submission_sha256']}))
