"""Write possession-label-order-correction.json (log entry K005): the Metrica proxy labels depended on how tied events
were sorted; three reporting-only records had been computed in an environment in which the ties came out in another
order than in the provider's files. Collects the label facts of both environments, the evidence that no selection
was affected, and the recomputed numbers. Usage: assemble_k005.py"""
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np

REPO, WORK = Path('/home/claude/sc'), Path('/home/claude/work')
P = Path('/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad/prova')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
load = lambda p: json.loads(Path(p).read_text())


def table(rows, variants):
    """{'spell_f1': {variant: {match: x}}, 'mean': {variant: x}, 'difference_to_base': {variant: x}, 'largest_single_change': x}"""
    sp = {v: {r['match']: r['spell_f1'] for r in rows if r['variant'] == v} for v in variants}
    mean = {v: round(float(np.mean(list(sp[v].values()))), 4) for v in variants}
    diff = {v: round(mean[v] - mean['base'], 4) for v in variants if v != 'base'}
    single = {v: {m: round(sp[v][m] - sp['base'][m], 4) for m in sp[v]} for v in variants if v != 'base'}
    return {'spell_f1': sp, 'mean_spell_f1': mean, 'difference_to_base': diff, 'difference_to_base_per_match': single,
            'macro_f1_base': {r['match']: r.get('macro_f1') for r in rows if r['variant'] == 'base'}}


def main():
    first = load(REPO / 'possession-rehearsal-results.json')
    slots_first = first['slot_and_duplicate_diagnostic']
    roles_first = load(WORK / 'stress_roles.json')['rows']
    roles_new = load(WORK / 'stress_roles_py313.json')['rows']
    slots_new = load(WORK / 'stress_slots_py313.json')['rows']
    roles_v = ('base', 'gk_one', 'gk_both', 'gk_part', 'ref_home', 'ref_mixed')
    slots_v = ('base', 'sticky', 'lru', 'swap', 'dup1', 'dup5')
    assert len(roles_new) == 18 and len(slots_new) == 18
    py310, py313 = load(WORK / 'gk2/label_order_py310.json'), load(WORK / 'gk2/label_order_py313.json')
    for g in ('MET1', 'MET2', 'MET3'):
        assert py310['games'][g]['stable']['sha256'] == py313['games'][g]['stable']['sha256'] == py313['games'][g]['quicksort']['sha256']
        assert py310['games'][g]['quicksort']['sha256'] != py310['games'][g]['stable']['sha256']
    v2 = load(REPO / 'possession-v2-results.json')
    out = {
        'record': 'K005: order of simultaneous events in the Metrica proxy labels (records correction; no selection affected)',
        'written_at': subprocess.check_output(['date', '-Iseconds']).decode().strip(),
        'finding': 'Three reporting-only records were scored against Metrica proxy labels that had lost about half of their dead-ball intervals: '
                   'the full-size rehearsal of K003 (bundles A and B), the slot / duplicate diagnostic of K003 and the goalkeeper diagnostic '
                   'that motivated K004. They had been run in the Python 3.10 environment of the release (pandas 2.1.4, numpy 1.26.4); every '
                   'selection, gate, validation and reserved test ran in the experiment environment (Python 3.13, pandas 3.0.5, numpy 2.5.3), '
                   'where the labels are as intended.',
        'how_it_was_found': 'In the full-size rehearsal of possession-v2.11 (K004) the bundle with exchanged goalkeeper ids, built in the experiment '
                            'environment, scored higher than bundle A of K003, although both have the same content. Their label files differed in '
                            '17,448 frames, all of them H or A in bundle A and D in the new bundle.',
        'cause': "experiments/possession_v2/metrica_labels.labels_from_events sorted the events by 'Start Frame' with the default sort, which is not "
                 'stable. In the provider\'s files a SET PIECE and the PASS that takes it share a start frame, and the dead-ball interval before '
                 'a restart is recorded only if the SET PIECE row stays first, as in the file. Under pandas 3.0.5 / numpy 2.5.3 the default sort '
                 'keeps the file order of these ties (identical to a stable sort on all three games); under pandas 2.1.4 / numpy 1.26.4 it does not.',
        'label_facts': {'python_3_10_release_environment': py310, 'python_3_13_experiment_environment': py313},
        'not_affected': {
            'statement': 'possession-v2.1 to possession-v2.11: every plan, gate, validation row and reserved test. No model was trained on Metrica labels.',
            'evidence': [
                {'what': 'the possession counts stored with the first validation and reserved test (possession-v2-results.json) are those of the '
                         'file-order labels',
                 'stored': {'validation mean over the four validation matches': v2['validation']['v2_selected']['n_gt_spells'],
                            'reserved Metrica game 3': v2['reserved_test']['cases']['201']['v2']['n_gt_spells']},
                 'file_order_labels': {'MET1': py313['games']['MET1']['stable']['possessions_on_play_blocks'], 'MET2': py313['games']['MET2']['stable']['possessions_on_play_blocks'],
                                       'MET3': py313['games']['MET3']['stable']['possessions_on_play_blocks'], 'J03WN1': 500, 'J03WR9': 370, 'mean of the four validation matches': 403.25},
                 'labels_of_the_python_3_10_environment': {'MET1': py310['games']['MET1']['quicksort']['possessions_on_play_blocks'],
                                                           'MET2': py310['games']['MET2']['quicksort']['possessions_on_play_blocks'],
                                                           'MET3': py310['games']['MET3']['quicksort']['possessions_on_play_blocks'], 'mean of the four validation matches': 398.75}},
                {'what': 'the validation models (work/cache/models_v2*.pkl, stack_v2*.pkl) are scikit-learn objects; scikit-learn is installed only in '
                         'the experiment environment, so no validation since possession-v2.2 can have run in the Python 3.10 environment'},
                {'what': 'macroF1 of the Metrica rows in every results file with such rows (v2.1, v2.5, v2.5b, v2.6, v2.9 and its amendment, v2.10, v2.11) '
                         'is 0.78-0.85 where the system is not deliberately broken; against the degraded labels the same system gets about 0.70-0.75 '
                         '(rows of the slot diagnostic in possession-rehearsal-results.json)'},
                {'what': 'the two validations of 11 November (exp_v210.py, exp_v211.py) were started with /usr/bin/python3 (Python 3.13); '
                         'the reserved Metrica game 3 test of possession-v2.4 repeats the stored v2.1 numbers of the same copies to four decimals'}]},
        'affected_records': [
            'possession-rehearsal-results.json: rehearsal scores of bundles A and B against the external labels, organisers\' scorer cross-check, negative controls, slot / duplicate diagnostic',
            'possession-v210-plan.json: field diagnostic_spell_f1 (the goalkeeper diagnostic quoted as motivation; not a gate)',
            'documents that quoted those numbers before this correction (technical documents, team guide, CLAUDE.md, log entry K003)'],
        'corrected': {
            'full_size_rehearsal_of_K003': load(P / 'rescore_k003.json'),
            'slot_and_duplicate_diagnostic': {
                'first_run_python_3_10': {k: slots_first[k] for k in ('spell_f1', 'mean_spell_f1', 'difference_to_base')},
                'rerun_python_3_13_file_order_labels': table(slots_new, slots_v), 'rows': slots_new},
            'goalkeeper_diagnostic': {
                'first_run_python_3_10': table(roles_first, roles_v),
                'rerun_python_3_13_file_order_labels': table(roles_new, roles_v), 'rows': roles_new},
        },
        'what_the_correction_changes': 'Absolute levels (spellF1 about +0.05, macroF1 about +0.13 against the file-order labels) and small differences; '
                                       'no conclusion that was drawn from these records (see the two tables) and no decision.',
        'fix': {'file': 'experiments/possession_v2/metrica_labels.py', 'change': "sort_values(['Start Frame'], kind='stable')",
                'sha256_after': sha(REPO / 'experiments/possession_v2/metrica_labels.py'),
                'check': 'with the stable sort both environments give the same labels as the experiment environment gave before (sha256 per game in label_facts)'},
        'kept_unchanged': ['possession-rehearsal-results.json and possession-v210-plan.json keep the first numbers; this file and log entry K005 hold the corrections',
                           'the synthetic rehearsal bundles themselves (their tracking does not depend on the labels; the broadcast replays of bundles A and B were placed with the degraded labels)'],
        'scripts': {'label_order.py': sha(WORK / 'gk2/label_order.py'), 'rescore_k003.py': sha(P / 'rescore_k003.py'), 'gt_spells.py': sha(WORK / 'gk2/gt_spells.py'),
                    'stress_slots.py': sha(WORK / 'stress_slots.py'), 'stress_roles.py': sha(WORK / 'stress_roles.py')},
        'provided_fixture_used': False,
    }
    (REPO / 'possession-label-order-correction.json').write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    c = out['corrected']
    print('slots first', c['slot_and_duplicate_diagnostic']['first_run_python_3_10']['mean_spell_f1'], c['slot_and_duplicate_diagnostic']['first_run_python_3_10']['difference_to_base'])
    print('slots rerun', c['slot_and_duplicate_diagnostic']['rerun_python_3_13_file_order_labels']['mean_spell_f1'], c['slot_and_duplicate_diagnostic']['rerun_python_3_13_file_order_labels']['difference_to_base'],
          c['slot_and_duplicate_diagnostic']['rerun_python_3_13_file_order_labels']['difference_to_base_per_match'])
    print('roles first', c['goalkeeper_diagnostic']['first_run_python_3_10']['mean_spell_f1'], c['goalkeeper_diagnostic']['first_run_python_3_10']['difference_to_base'])
    print('roles rerun', c['goalkeeper_diagnostic']['rerun_python_3_13_file_order_labels']['mean_spell_f1'], c['goalkeeper_diagnostic']['rerun_python_3_13_file_order_labels']['difference_to_base'])


if __name__ == '__main__':
    main()
