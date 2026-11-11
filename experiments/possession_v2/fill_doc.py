"""Fill result tables in TECHNICAL_DOCUMENT_V2.md from possession-v2-results.json."""
import json, sys
doc_path, res_path = sys.argv[1], sys.argv[2]
doc = open(doc_path).read(); R = json.load(open(res_path))
v = R['validation']
c = R['candidates']
crow = ['| candidate | decoder (switch, out, in, dead bias) | spellF1 all | DFL | Metrica | macroF1 |', '|---|---|---|---|---|---|']
for k, r in c.items():
    d = r['best_decoder']
    name = r['description'] + (' **(selected)**' if r['selected'] else '')
    crow.append(f"| {name} | {d['switch']:g}, {d['out_cost']:g}, {d['in_cost']:g}, {d['bias_dead']:g} | {r['spell_f1_all']:.4f} | {r['spell_f1_dfl']:.4f} | {r['spell_f1_metrica']:.4f} | {r['macro_f1']:.4f} |")
doc = doc.replace('<!-- CANDIDATES_TABLE -->', '\n'.join(crow))
rows = ['| system (same corrupted validation copies) | spellF1 all | spellF1 DFL | spellF1 Metrica | macroF1 | predicted spells | true spells |',
        '|---|---|---|---|---|---|---|']
for name, key in (('organiser baseline_smooth50 logic', 'baseline50'), ('team S001 sequence model', 'S001'),
                  ('selected system, frame argmax (no decoder)', 'v2_argmax'), ('**selected system**', 'v2_selected')):
    r = v[key]
    rows.append(f"| {name} | {r['spell_f1_all']:.3f} | {r['spell_f1_dfl']:.3f} | {r['spell_f1_metrica']:.3f} | {r['macro_f1_all']:.3f} | {r['n_pred_spells']:.0f} | {r['n_gt_spells']:.0f} |")
doc = doc.replace('<!-- RESULTS_TABLE -->', '\n'.join(rows))
t = R.get('reserved_test')
if t:
    trows = ['| system | spellF1 | macroF1 |', '|---|---|---|']
    for name, key in (('organiser baseline_smooth50 logic', 'baseline50'), ('team S001', 'S001'), ('**v2 (frozen bundle)**', 'v2')):
        trows.append(f"| {name} | {t['mean'][key]['spell_f1_mean']:.3f} | {t['mean'][key]['macro_f1']:.3f} |")
    doc = doc.replace('<!-- TEST_TABLE -->', 'Metrica sample game 3, two fixed corrupted copies (seeds 201, 202):\n\n' + '\n'.join(trows))
st = R.get('stress_test_final'); s2 = R.get('stress_test_tracker_artefacts')
if st or s2:
    srows = ['| condition | selected system spellF1 | organiser baseline logic |', '|---|---|---|']
    for lev, desc in (('mild', 'mild corruption (ball missing 12% in play, low noise)'),
                      ('harsh', 'harsh (ball missing 40% in play, high noise, false balls)'),
                      ('harsh_dead_coupled', 'harsh + ball missing much more often in stoppages')):
        if st and lev in st:
            srows.append(f"| {desc} | {st[lev]['v2']:.3f} | {st[lev]['baseline50']:.3f} |")
    if s2:
        m = s2['mean']
        for k, desc in (('base', 'standard corruption (one copy per match)'), ('id_swaps', '+ slot identity swaps'),
                        ('duplicates', '+ duplicated players'), ('long_fp', '+ 1-5 s false ball detections'),
                        ('all3', '+ all three')):
            srows.append(f"| {desc} | {m[k]:.3f} | - |")
    doc = doc.replace('<!-- STRESS_TABLE -->', '\n'.join(srows))
open(doc_path, 'w').write(doc)
print('filled')
