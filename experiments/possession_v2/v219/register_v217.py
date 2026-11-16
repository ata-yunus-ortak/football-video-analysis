"""Write the registration of the v2.17 validation (the team member's eight network members, weight 0.4, against
possession-v2.16) before any validation row exists. Usage: /usr/bin/python3 register_v217.py"""
import hashlib, json, os, re, sys, platform
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np
REPO, V = Path('/home/claude/sc'), Path('/home/claude/work/v219')
U = V / 'u' / 'experiments' / 'v216u'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p in range(4):
    assert not (V / f'exp_v217_{p}.json').exists(), 'registration must come before any validation row'
assert not (REPO / 'possession-v217-results.json').exists()

# --- the candidate's files: commit 74bedbf of branch mtah-possession, checked against the author's own list
theirs = dict(line.split()[::-1] for line in (U / 'SHA256SUMS').read_text().splitlines() if line.strip())
STEMS = ['a_s0', 'a_s1', 'a_s2', 'a_s3', 'f_s0', 'f_s1', 'f_s2', 'f_s3']
weights = {f'{d}_{s}.npz': sha(V / 'weights' / f'{d}_{s}.npz') for d in ('d4', 'd6') for s in STEMS}
assert all(theirs[f'possession/weights/v216u/{k}'] == v for k, v in weights.items()), 'a weight file differs from the author\'s SHA256SUMS'

# --- what was known before this registration (all on external matches)
dev = {r['copy']: r for r in json.loads((U / 'dev_grid_final.json').read_text())}
hold = json.loads((U / 'holdout_new_seeds.json').read_text())
holdf = json.loads((U / 'holdout_new_seeds_fill.json').read_text())
r15 = json.loads((REPO / 'possession-v215-results.json').read_text())
mine = {f"{r['copy'].replace('|', '_')}_{r['condition']}": r for r in r15['rows'] if r['condition'] in ('tactical', 'tactical_sim2')}
common = sorted(k for k in dev if k in mine)
assert len(common) == 20 and max(abs(dev[k]['v2_11'] - mine[k]['v2_11']['spell_f1']) for k in common) < 1e-12
d15 = np.array([dev[k]['sets']['A4F4']['w0.40'] - mine[k]['fused']['spell_f1'] for k in common])
grp = lambda rows, pre: [r for r in rows if r['copy'].startswith(pre)]
def vs11(rows, key='w0.40'):
    d = [r['sets']['A4F4'][key] - r['v2_11'] for r in rows]
    return {'copies': len(d), 'mean': round(float(np.mean(d)), 4), 'worst': round(float(min(d)), 4)}
seen = {
    'author_development_grid': {'what': 'experiments/v216u/dev_grid_final.json: the 40 tactical and second-simulator copies of the v2.14 and v2.15 validations, four member sets x five weights; '
                                        'set A4F4 (the candidate\'s eight members) at weight 0.4, spellF1 difference to v2.11',
                                'DFL': vs11(grp(dev.values(), 'J03')), 'Metrica': vs11(grp(dev.values(), 'MET'))},
    'author_check_on_other_seeds': {'what': 'experiments/v216u/holdout_new_seeds.json and holdout_new_seeds_fill.json: candidate fixed by its author beforehand, run once by him; copy seeds 23100 + 10 * match_index + j '
                                            '(the copies of this process\'s K016 exploration, on which no second-model candidate had been developed) and second simulator 73100 + match_index; difference to v2.11',
                                    'tactical DFL': vs11(grp(hold, 'J03')), 'tactical Metrica': vs11(grp(hold, 'MET')),
                                    'fill_good': vs11([r for r in holdf if r['copy'].endswith('fill_good')]), 'fill_medium': vs11([r for r in holdf if r['copy'].endswith('fill_medium')])},
    'candidate_against_the_release_on_copies_both_sides_scored': {
        'what': 'the author\'s values of the candidate (dev_grid_final.json) minus the registered v2.15 values (possession-v215-results.json) on the 20 tactical and second-simulator copies of the v2.15 validation; '
                'his v2.11 values equal the registered ones on all 20. These copies were development data of the candidate.',
        'mean': round(float(d15.mean()), 4), 'DFL': round(float(np.mean([d for k, d in zip(common, d15) if k.startswith('J03')])), 4),
        'Metrica': round(float(np.mean([d for k, d in zip(common, d15) if k.startswith('MET')])), 4), 'worst': round(float(d15.min()), 4),
        'better': int((d15 > 1e-9).sum()), 'worse': int((d15 < -1e-9).sum()), 'equal': int((np.abs(d15) <= 1e-9).sum())},
    'also': 'everything listed in possession-v215-plan.json and possession-v216-plan.json, the K014 / K015 / K016 records, and the rest of experiments/v216u/README.md of commit 74bedbf '
            '(other member sets and weights, the network alone, pooling on the v2.3 path)'}

# --- wiring: this script on copies of earlier validations must reproduce their rows (no copy of this validation)
wiring = {}
for part in ('wiring_met', 'wiring_dfl', 'wiring_fill'):
    for r in json.loads((V / f'exp_v217_{part}.json').read_text())['rows']:
        wiring[(r['copy'], r['condition'])] = r['fused']['spell_f1']
g16 = {(r['copy'], r['condition']): r['fused']['spell_f1'] for r in json.loads(Path('/home/claude/work/v218/exp_v216_0.json').read_text())['rows']}
checks = {
    'MET1|19120 tactical, arm v2_16 = registered v2.15 value': (wiring[('MET1|19120', 'tactical|v2_16')], mine['MET1_19120_tactical']['fused']['spell_f1']),
    'J03WN1|19100 tactical, arm v2_16 = registered v2.15 value': (wiring[('J03WN1|19100', 'tactical|v2_16')], mine['J03WN1_19100_tactical']['fused']['spell_f1']),
    'J03WN1|28100 good, arm v2_16 = candidate row of the v2.16 validation': (wiring[('J03WN1|28100', 'fill_good|v2_16')], g16[('J03WN1|28100', 'good|candidate')])}
for k, (a, b) in checks.items():
    assert abs(a - b) < 1e-12, (k, a, b)
near = {
    'MET1|19120 tactical, arm candidate (NumPy inference here) against the author\'s value (PyTorch forward)': (wiring[('MET1|19120', 'tactical|candidate')], dev['MET1_19120_tactical']['sets']['A4F4']['w0.40']),
    'J03WN1|19100 tactical, arm candidate against the author\'s value': (wiring[('J03WN1|19100', 'tactical|candidate')], dev['J03WN1_19100_tactical']['sets']['A4F4']['w0.40'])}
for k, (a, b) in near.items():
    assert abs(a - b) < 0.005, (k, a, b)
wiring_record = {'exact': {k: round(a, 6) for k, (a, b) in checks.items()},
                 'candidate_arm': {k: {'here': round(a, 6), 'author': round(b, 6)} for k, (a, b) in near.items()},
                 'J03WN1|28100 good, arm candidate (no earlier value exists)': round(wiring[('J03WN1|28100', 'fill_good|candidate')], 6)}

# --- the seeds of this validation must be new
SEEDS = [29100 + 10 * mi + j for mi in range(4) for j in range(4)] + [54100 + 100 * ri + 4 * mi + j for ri in range(2) for mi in range(4) for j in range(2)] \
        + [84100 + 100 * ri + 4 * mi + j for ri in range(2) for mi in range(4) for j in range(2)] + [94100 + mi for mi in range(4)]
hits = []
for root in (REPO, Path('/home/claude/work')):
    for dp, dn, fn in os.walk(root):
        if any(x in dp for x in ('/cache', '__pycache__', '/.git', '/probs', '/tcn_cache', '/tcn_weights', '/dev', 'repro25_fixture', '/weights', '/prova', '/sc_stage')):   # prova: synthetic rehearsal bundles; their frame counters contain every number
            continue
        for f in fn:
            if f in ('exp_v217.py', 'register_v217.py', 'assemble_v217.py') or not f.endswith(('.py', '.json', '.md', '.log', '.txt', '.sh')):
                continue
            try:
                text = open(os.path.join(dp, f), errors='ignore').read()
            except OSError:
                continue
            found = [s for s in SEEDS if re.search(r'(?<![0-9.])%d(?![0-9])' % s, text)]
            if found:
                hits.append({'file': os.path.join(dp, f).replace('/home/claude/', ''), 'numbers': found})

plan = {
 'version': 'possession-v2.17-plan',
 'registered_at': datetime.now(timezone(timedelta(hours=3))).isoformat(timespec='seconds'),
 'candidate': 'possession-v2.17 = possession-v2.16 with another second model. The three network members of v2.15 / v2.16 (dfl6_both_s0-2, 37 features, weight 0.2 in the arithmetic pool) are replaced by eight members '
              'trained by the team member who wrote the network (repository branch mtah-possession, commit 74bedbf: d6_a_s0-3 on the 37 features of possession/features.py, d6_f_s0-3 on the 71 features of '
              'possession/features2.py), run by his possession/infer.py of that commit (every member gets the features it was trained with; mean over members and both team orders, 4 decimals), and the weight of the '
              'network in the pool is 0.4. Everything else is v2.16: no pooling on the v2.3 path, the v2 decoder with the constants of the bundle, the goalkeeper check, the ball fill and the added players behind '
              'the accuracy gate, the kick-off rule.',
 'candidate_fixed_by': 'its author, before his own check on other seeds (experiments/v216u/README.md of commit 74bedbf: "Candidate (fixed before the check below): eight TCN members ..., pooling weight 0.4"). '
                       'This process trained nothing, chose nothing and changed nothing of it; the 16 weight files are byte copies of that commit (SHA-256 below, equal to his SHA256SUMS).',
 'why_a_fourth_attempt': 'possession-v215-plan.json (15 Nov 01:17) called v2.15 the third attempt to add the second model; its decision rule says that after a failed gate "no further candidate with the second model is '
                         'registered before the deadline", its limits say "no further attempt follows", and AGENTS.md, CLAUDE.md, docs/DENEY_KAYDI_TR.md (K013, K014) and TECHNICAL_DOCUMENT_V2.md (fourth and fifth addendum) '
                         'call it the last attempt and repeat that no further candidate with the second model is registered. v2.15 passed its gates. On 16 Nov between 00:49 and 05:58 the team member pushed new members to his branch, '
                         'together with his development numbers and a check on other seeds; this process had not asked for them. It saw the branch on 16 Nov at about 06:10, while checking the repository after the delivery '
                         'chain of v2.16, told the team lead in the morning that a further registration goes back on the written statement and that the choice was his, and the team lead decided on 16 Nov at 12:24 to make '
                         'one more attempt. This plan is that attempt: the fourth registered validation of a second-model candidate (v2.13, v2.14, v2.15, v2.17) and a departure from the statement quoted above, made after '
                         'the candidate\'s development numbers were known. None of the earlier plans, results or log entries is changed.',
 'training_as_stated_by_the_author': 'experiments/v216u/README.md and train216.py of commit 74bedbf: the network of commit 167dc7b (hidden 128, kernel 5, dilations 1-64 twice, class weights 1 / 1 / 0.7); recipe a: 37 features, '
                                     '3200 steps of AdamW, peak learning rate 1.5e-3, batch 16, seeds 0-3; recipe f: 71 features, 4800 steps, otherwise the same; PyTorch on Apple MPS. Training input: for every training '
                                     'match 16 copies of the team\'s simulator (v2 profile) and 8 of his own, packed into 46 slots and goalkeeper-corrected with the team\'s code. d4_* were trained on J03WOH, J03WOY, J03WPY, '
                                     'J03WQQ (used on the DFL rows here), d6_* on those and J03WN1, J03WR9 (Metrica rows and a release). His statement: external matches only, the provided match was not opened. '
                                     'This process has not observed the training and cannot reproduce it bit for bit; the weight files are the reference.',
 'models_per_match': {'J03WN1, J03WR9 (DFL)': 'v2 side: validation models trained on J03WOH, J03WOY, J03WPY, J03WQQ; arm v2_16: dfl4_both_s0, s1, s2; arm candidate: d4_a_s0-3, d4_f_s0-3',
                      'Metrica games 1, 2': 'v2 side: the released pair models/possession-v2.npz, possession-v23.npz; arm v2_16: dfl6_both_s0, s1, s2 (= models/possession-tcn-v215.npz); arm candidate: d6_a_s0-3, d6_f_s0-3'},
 'seen_on_external_data_before_registration': seen,
 'wiring_check_before_registration': dict(wiring_record, note='copies of the v2.15 and v2.16 validations; arm v2_16 reproduces the registered rows exactly; the candidate arm differs from the author\'s development values '
                                                              'only through his PyTorch forward pass (he states an agreement of about 1e-6 before the rounding to 4 decimals). The three wiring rows were run before the clock seed base of exp_v217.py '
                                                              'was set to 84100 (the only change after them; the wiring parts do not use that constant)'),
 'validation': {
     'run_by': 'this process (which did not build the candidate), in its own environment, with the NumPy inference that would be released',
     'script': 'v219/exp_v217.py (parts 0-3), which imports v218/exp_v216.py (stream and model input of v2.16), v215/exp_v215.py (the release\'s pooled decision), v213/exp_v213.py (copies, v2 models, metrics) unchanged, '
               'and the byte copies v219/tcn2/ of the candidate\'s inference; gates applied by v219/assemble_v217.py, written before any validation row',
     'matches': ['J03WN1', 'J03WR9', 'MET1', 'MET2'],
     'copies': '16 new corrupted copies: possession.degrade, v2 profile (RANGES), seed 29100 + 10 * match_index + j, j = 0..3; packed into 46 anonymous slots; noise gate on the tracking as given; goalkeeper check (keeper2)',
     'conditions': {'tactical': 'all 16 copies: tactical camera only',
                    'fill_good': 'copies j = 0, 1 (8): simulated broadcast stream (synth_broadcast3.simulate_warp), regime good of exp_v25.REGIMES, simulated clock readings; stream seed 54100 + 4 * match_index + j, '
                                 'clock 84100 + 4 * match_index + j; model input of both arms as possession.run216 (ball filled and lost players added when the accuracy gate is open)',
                    'fill_medium': 'copies j = 0, 1 (8): regime medium; stream seed 54200 + 4 * match_index + j, clock 84200 + 4 * match_index + j',
                    'tactical_sim2': 'one copy per match made with the team member\'s simulator (seed 94100 + match_index)'},
     'arms': {'v2_16': 'the release: its three members, weight 0.2', 'candidate': 'the eight members, weight 0.4'},
     'shared_by_both_arms': 'the copy, the model input, the probabilities of the v2 models, the pool, the decoder; on the v2.3 path neither arm pools and the difference is zero by construction',
     'seeds_found_elsewhere': hits},
 'gates': {
     'G1 gain': 'condition tactical, all 16 copies: mean(candidate - v2_16) spellF1 >= +0.008',
     'G2 gain on provider flags': 'condition tactical, the 8 DFL copies: mean(candidate - v2_16) spellF1 >= +0.008',
     'G3 no harm on event proxies': 'condition tactical, the 8 Metrica copies: mean(candidate - v2_16) spellF1 >= -0.002',
     'G4 no bad copy': 'condition tactical: every copy has candidate - v2_16 >= -0.010',
     'G5 macroF1': 'condition tactical, all 16 copies: mean(candidate - v2_16) macroF1 >= -0.003',
     'G6 broadcast fill': 'conditions fill_good and fill_medium, 8 copies each: mean(candidate - v2_16) spellF1 >= 0.000 in each',
     'G7 other simulator': 'condition tactical_sim2, 4 copies: mean(candidate - v2_16) spellF1 >= 0.000',
     'note': 'the seven gates, conditions and thresholds of possession-v214/-v215-plan.json, unchanged, with the comparison arm moved from v2.11 to the current release v2.16 (as possession-v216-plan.json did with v2.15). '
             'That is the stricter reading: v2.16 already contains a second model that passed these gates against v2.11. Evaluated on unrounded values, once, on all rows.'},
 'decision_rule': 'All seven gates pass: the candidate is selected and integrated as possession-v2.17 (new entry point derived from run216.py; byte copies of features2.py and infer.py of commit 74bedbf; the eight d6 files '
                  'with the SHA-256 below; new manifest; v2.16 becomes the next step of the technical ladder). It replaces v2.16 in the delivery only if, by 16 Nov 2026 23:59 Istanbul (the last moment already named in the '
                  'v2.15 and v2.16 plans, not moved), the ported inference runs under Python 3.10 / numpy 1.26.4, the output on synthetic provided-like bundles is byte-identical across Python 3.10 / numpy 1.26.4 and '
                  'Python 3.13 / numpy 2.5.3, the full test suite passes, a full-size chain rehearsal ends OK, and the documents describe the new members, their training as stated by their author, and this fourth '
                  'attempt with the statement it departs from; and only if the delivery chain then runs OK on the team\'s computer. Otherwise v2.16 stays. Any gate fails: v2.16 stays the release and the candidate is '
                  'recorded as tried and not used. Whatever the outcome, no further candidate with the second model is registered before the deadline. The gates are applied once, to all rows; nothing is re-run with '
                  'other seeds, members, weights or pools.',
 'reported_alongside': ['every row; means per source in every condition; both arms against v2.11; the network alone of both arms; frames changed; the path and the state of the accuracy gate per copy'],
 'not_part_of_this_validation': ['The Smart Tagging kick-off rule (unchanged, not measurable externally).', 'The provided match: not read, not run and not scored.',
                                 'Pooling on the v2.3 path (explored by the author, not part of the candidate).',
                                 'The training of the members (not observed and not repeated here).'],
 'limits': ['Fourth registered attempt with the second model, and the first made after a written statement that there would be none. Each validation used new copies, but repeated attempts with the same gates on the same '
            'four matches make a pass easier; a pass here is weaker evidence than a pass at the first attempt would have been. A stopping statement that is set aside once promising numbers appear protects less than one that is kept.',
            'The candidate was built, tuned and first checked by its author on his own computer; this process only validates the committed files. That the training used external matches only and that the provided '
            'match was not opened is the author\'s statement.',
            'The validation matches were used for every earlier selection of v2.x, for the author\'s development grid (the 40 copies of the v2.14 and v2.15 validations: member sets and the weight 0.4 were chosen there) '
            'and for his check. Only the copies are new. The d4 members have not seen the two DFL validation matches; the d6 members were trained on all six DFL matches and are scored on the Metrica games only. '
            'This is a validation, not a fresh test.',
            'There is no untouched test for any pooled system: J03WMX was used in the development of the network recipe by its author, Metrica game 3 in the development of v2.14 and v2.15.',
            'Corruption, slot packing and broadcast camera are simulated by the team; the provided tracking may differ. The members were shown the two simulators and nothing else.',
            'DFL labels are the provider\'s per-frame flags; Metrica labels are the team\'s event-derived proxies.',
            'Registered about 37 hours before the submission deadline. The last moment for the conditions of the decision rule is not moved, so there is less time for integration, rehearsal and the checks on the '
            'team\'s computer than for any earlier release.',
            'Inference bytes: the candidate\'s rounded probabilities on a synthetic input have the same SHA-256 (a91b133b...ba9ebf6b) on macOS arm64 (author: Python 3.12.13 / NumPy 2.5.4 and 3.10.20 / 1.26.4) and here on '
            'Linux x86-64 (Python 3.13.18 / numpy 2.5.3 and 3.10.20 / 1.26.4). Windows is first tested by the cross-platform step of the delivery chain. NumPy matrix products are not guaranteed bit-identical across '
            'BLAS builds; the 4-decimal and 6-decimal rounding makes a different output unlikely, not impossible.',
            'The network runs eight members instead of three: the generation of the file takes several minutes longer.',
            'The organisers state that differences below about 0.04 are noise on one match.',
            'The reserve configuration without the kick-off rule (possession-release-graded-windows.json) stays the v2.11g ladder and uses no second model.'],
 'hashes': {'candidate_weights': weights,
            'release_weights': {f: sha(f'/home/claude/work/v214/tcn_weights/{f}') for f in ['dfl4_both_s0.npz', 'dfl4_both_s1.npz', 'dfl4_both_s2.npz', 'dfl6_both_s0.npz', 'dfl6_both_s1.npz', 'dfl6_both_s2.npz']},
            'tcn2': {f: sha(V / 'tcn2' / f) for f in ('__init__.py', 'infer.py', 'features.py', 'features2.py', 'decode.py')},
            'exp_v217.py': sha(V / 'exp_v217.py'), 'assemble_v217.py': sha(V / 'assemble_v217.py'), 'register_v217.py': sha(V / 'register_v217.py'),
            'exp_v216.py': sha('/home/claude/work/v218/exp_v216.py'), 'exp_v215.py': sha('/home/claude/work/v215/exp_v215.py'), 'exp_v213.py': sha('/home/claude/work/v213/exp_v213.py'),
            'pooling.py': sha('/home/claude/work/v215/pooling.py'), 'possession-v216-release.json': sha(REPO / 'possession-v216-release.json'),
            'author_files_of_commit_74bedbf': {f: sha(U / f) for f in ('README.md', 'SHA256SUMS', 'dev_grid_final.json', 'holdout_new_seeds.json', 'holdout_new_seeds_fill.json', 'train216.py')}},
 'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'blas_threads_per_process': 1},
 'provided_fixture_used': False}
(REPO / 'possession-v217-plan.json').write_text(json.dumps(plan, indent=1) + '\n', encoding='utf-8')
print('registered at', plan['registered_at'], '| seeds found elsewhere:', hits)
print(json.dumps({'seen': seen, 'wiring': wiring_record}, indent=1)[:4000])
