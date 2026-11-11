"""Write log entry K005 (Turkish; records correction: order of simultaneous events in the Metrica proxy labels) at the
top of docs/DENEY_KAYDI_TR.md and put a pointer under the heading of K003. Run after k004.py. Usage: k005.py"""
import json
import os
from pathlib import Path

R = Path(os.environ.get('SC_DIR', '/home/claude/sc'))
C = json.loads((R / 'possession-label-order-correction.json').read_text())
co = C['corrected']
L10, L13 = C['label_facts']['python_3_10_release_environment']['games'], C['label_facts']['python_3_13_experiment_environment']['games']


def tr(x, nd=4):
    return f'{x:.{nd}f}'.replace('.', ',')


def sgn(x, nd=4):
    x = round(x, nd)
    return ('+' if x > 0 else '−' if x < 0 else '') + f'{abs(x):.{nd}f}'.replace('.', ',')


def th(n):
    return f'{int(n):,}'.replace(',', '.')


def share_d(g, kind, src):
    c = src[g][kind]['counts']
    return ('%' + f"{100 * c['D'] / sum(c.values()):.1f}").replace('.', ',')


labels = '\n'.join(
    f"| {g} | {th(L10[g]['events'])} / {th(L10[g]['events_that_share_a_start_frame'])} | {th(L10[g]['quicksort']['counts']['D'])} ({share_d(g, 'quicksort', L10)}) / {L10[g]['quicksort']['possessions_on_play_blocks']} | "
    f"{th(L13[g]['stable']['counts']['D'])} ({share_d(g, 'stable', L13)}) / {L13[g]['stable']['possessions_on_play_blocks']} | {th(L10[g]['frames_that_differ'])} |"
    for g in ('MET1', 'MET2', 'MET3'))

k3 = co['full_size_rehearsal_of_K003']


def k3row(b, key, name):
    v = k3[f'bundle {b}'][key]
    a, n = v['as_recorded_in_K003'], v['against_file_order_labels']
    return f"| {name} | {tr(a['spell_f1_mean'])} / {tr(a['macro_f1'])} | {tr(n['spell_f1_mean'])} / {tr(n['macro_f1'])} | {tr(a['f1_D'], 3)} → {tr(n['f1_D'], 3)} |"


rows3 = '\n'.join([
    k3row('A', 'delivered file of the K003 chain (possession-v2.9)', 'paket A, teslim dosyası (v2.9 zinciri)'),
    k3row('A', 'in-memory reference (r1)', 'paket A, bellek içi başvuru (paketleme ve yayın yok)'),
    k3row('A', 'tactical camera only (r3, possession.run25c)', 'paket A, yalnız taktik kamera (dosyadan)'),
    k3row('A', 'reserve chain of K003 (possession-v2.9g)', 'paket A, yedek zincir (v2.9g)'),
    k3row('B', 'delivered file of the K003 chain (possession-v2.9)', 'paket B, teslim dosyası (v2.9 zinciri)'),
    k3row('B', 'in-memory reference (r1)', 'paket B, bellek içi başvuru'),
    k3row('B', 'tactical camera only (r3, possession.run25c)', 'paket B, yalnız taktik kamera (dosyadan)')])
ctl = k3['negative_controls_bundle_A_against_file_order_labels']
first = json.loads((R / 'possession-rehearsal-results.json').read_text())
ctl1 = first['negative_controls_bundle_A']
org = {b: k3[f'bundle {b}']['organisers_scorer_against_file_order_labels'] for b in 'AB'}
dA = lambda key: k3['bundle A'][key]['against_file_order_labels']['spell_f1_mean']
dB = lambda key: k3['bundle B'][key]['against_file_order_labels']['spell_f1_mean']
KD, K1, K3_ = 'delivered file of the K003 chain (possession-v2.9)', 'in-memory reference (r1)', 'tactical camera only (r3, possession.run25c)'

sl1, sl2 = co['slot_and_duplicate_diagnostic']['first_run_python_3_10'], co['slot_and_duplicate_diagnostic']['rerun_python_3_13_file_order_labels']
slot_names = {'base': 'her oyuncu kendi sütununda (doğrulamalardaki düzen)', 'sticky': '46 slota paketli; kaybolan iz 1 sn içinde slotuna döner',
              'lru': 'paketli; iz slotuna hiç dönmez', 'swap': 'paketli; yeni iz en son boşalan slotu alır',
              'dup1': 'çift izleme, prova paketindeki oranda', 'dup5': 'çift izleme, beş katı'}
slots = '\n'.join(
    f"| {v}: {slot_names[v]} | {tr(sl1['mean_spell_f1'][v])} | {'' if v == 'base' else sgn(sl1['difference_to_base'][v])} | {tr(sl2['mean_spell_f1'][v])} | "
    f"{'' if v == 'base' else sgn(sl2['difference_to_base'][v])} | {'' if v == 'base' else ' / '.join(sgn(sl2['difference_to_base_per_match'][v][m]) for m in ('MET1', 'MET2', 'MET3'))} |"
    for v in ('base', 'sticky', 'lru', 'swap', 'dup1', 'dup5'))
slot_single = max(abs(x) for v in sl2['difference_to_base_per_match'].values() for x in v.values())
slot_mean = max(abs(x) for x in sl2['difference_to_base'].values())

ro1, ro2 = co['goalkeeper_diagnostic']['first_run_python_3_10'], co['goalkeeper_diagnostic']['rerun_python_3_13_file_order_labels']
role_names = {'base': 'olduğu gibi', 'gk_one': 'bir kaleci bütün maç yanlış kimlikle', 'gk_both': 'iki kaleci bütün maç yanlış kimlikle',
              'gk_part': 'iki kaleci maçın %30\'unda yanlış kimlikle', 'ref_home': 'hakem izi, ev sahibi kimliğiyle', 'ref_mixed': 'hakem izi, değişen kimlikle'}
roles = '\n'.join(
    f"| {role_names[v]} | {tr(ro1['mean_spell_f1'][v])} | {'' if v == 'base' else sgn(ro1['difference_to_base'][v], 3)} | {tr(ro2['mean_spell_f1'][v])} | {'' if v == 'base' else sgn(ro2['difference_to_base'][v], 3)} |"
    for v in role_names)
ev = C['not_affected']['evidence'][0]

text = f'''## K005 — Kayıt düzeltmesi: Metrica vekil etiketlerinde eşzamanlı olayların sırası, 11 Kasım 2026

**Özet.** Yalnız raporlama amaçlı üç kayıt, duran top aralıklarının yaklaşık yarısını yitirmiş Metrica vekil
etiketleriyle puanlanmıştı: K003'ün tam boy provası, K003'ün slot / çift izleme ölçümü ve K004'ü başlatan
kaleci teşhisi. Hiçbir seçim, eşik, doğrulama ya da ayrılmış test etkilenmedi; sürüm değişmedi. Etiket
betiği düzeltildi, üç kayıt yeniden hesaplandı (`possession-label-order-correction.json`). İlk sayılar
`possession-rehearsal-results.json` ve `possession-v210-plan.json` içinde olduğu gibi duruyor.

**Nasıl bulundu.** K004'ün tam boy provasında, kaleci kimlikleri değiştirilmiş paket (deney ortamında
kuruldu) K003'ün A paketinden yüksek puan aldı; oysa içerikleri aynı. İki paketin etiket dosyaları 17.448
karede farklıydı ve hepsinde A paketi H/A, yeni paket D diyordu.

**Neden.** `metrica_labels.labels_from_events` olayları `Start Frame`'e göre varsayılan sıralamayla
diziyordu; bu sıralama *kararlı* değildir, yani aynı karede başlayan olayların sırası kütüphane sürümüne
bağlıdır. Metrica'nın olay dosyalarında bir duran top (`SET PIECE`) ile onu kullanan pas aynı karede başlar.
Betik, bir duruşun sonunu "sonraki `SET PIECE`" diye arar; pas öne geçerse duran top aralığı hiç
kaydedilmez ve o kareler H/A kalır. Deney ortamında (Python 3.13, pandas 3.0.5, numpy 2.5.3) varsayılan
sıralama dosya sırasını koruyor; sürümün Python 3.10 ortamında (pandas 2.1.4, numpy 1.26.4) korumuyor.

| maç | olay / aynı karede başlayan olay | Python 3.10 ortamı: D kare (pay) / sahiplik sayısı | dosya sırası (deney ortamı): D kare (pay) / sahiplik sayısı | farklı kare |
|---|---|---|---|---|
{labels}

**Etkilenmeyenler ve kanıtı.** v2.1'den v2.11'e bütün planlar, eşikler, doğrulama satırları ve ayrılmış
testler deney ortamında çalıştı. Kanıt: (1) ilk doğrulamayla birlikte saklanan sahiplik sayıları
(`possession-v2-results.json`: dört doğrulama maçının ortalaması {tr(ev['stored']['validation mean over the four validation matches'], 2)}, ayrılmış maç 3 için {ev['stored']['reserved Metrica game 3']}) yalnız
dosya sırasındaki etiketlerle tutuyor (ortalama 403,25 ve 404); Python 3.10 etiketleriyle 398,75 ve {ev['labels_of_the_python_3_10_environment']['MET3']}
olurdu. (2) Doğrulama modelleri scikit-learn nesneleridir ve scikit-learn yalnız deney ortamında kurulu.
(3) Metrica satırı içeren bütün sonuç dosyalarında macroF1 0,78-0,85 düzeyinde; bozuk etiketlerle aynı
sistem 0,70-0,75 alıyor. (4) Bugünkü iki doğrulama `/usr/bin/python3` (3.13) ile başlatıldı. Sürümün
modelleri hiç Metrica etiketiyle eğitilmedi.

**Düzeltme.** Betik artık `kind='stable'` ile sıralıyor; iki ortam da deney ortamının öteden beri verdiği
etiketleri veriyor (maç başına SHA-256 düzeltme dosyasında).

*1. K003 tam boy provası (aynı çıktı dosyaları, dosya sırasındaki etiketlerle yeniden puanlandı):*

| çıktı | ilk yazılan spellF1 / macroF1 | düzeltilmiş | D için F1 |
|---|---|---|---|
{rows3}

Organizatörün `run_evaluation.py` betiği düzeltilmiş etiketlerle A için {tr(org['A']['spell_f1_mean'], 6)} / {tr(org['A']['macro_f1'], 6)}, B için
{tr(org['B']['spell_f1_mean'], 6)} / {tr(org['B']['macro_f1'], 6)} veriyor; bizim puanlayıcımızla aynı. Olumsuz denetimler (A): takımlar değiştirilince
{tr(ctl['teams exchanged']['spell_f1'])} (ilk yazılan {tr(ctl1['teams exchanged']['spell_f1'])}); satırlar 1 kare kayınca {tr(ctl['rows shifted by +1 frames']['spell_f1'])} ({tr(ctl1['rows shifted by +1 frames']['spell_f1'])}); 1 sn kayınca {tr(ctl['rows shifted by +25 frames']['spell_f1'])} / {tr(ctl['rows shifted by -25 frames']['spell_f1'])}
({tr(ctl1['rows shifted by +25 frames']['spell_f1'])} / {tr(ctl1['rows shifted by -25 frames']['spell_f1'])}); 5 sn kayınca {tr(ctl['rows shifted by +125 frames']['spell_f1'])} / {tr(ctl['rows shifted by -125 frames']['spell_f1'])} ({tr(ctl1['rows shifted by +125 frames']['spell_f1'])} / {tr(ctl1['rows shifted by -125 frames']['spell_f1'])}). Paketleme etkisi (dosyadan yalnız
taktik − bellek içi): A {sgn(dA(K3_) - dA(K1))}, B {sgn(dB(K3_) - dB(K1))}; yayın doldurmanın etkisi: A {sgn(dA(KD) - dA(K3_), 3)}, B {sgn(dB(KD) - dB(K3_), 3)}.
Provanın amacı (bağlantı, sabit dal, boyut, süre, bellek) ve sonucu değişmedi; değişen, dış etiketlere
göre yazılan düzeylerdir.

*2. Slot / çift izleme ölçümü (MET1-3, aynı kopyalar, deney ortamında yeniden çalıştırıldı), ortalama spellF1:*

| düzen | ilk yazılan | fark | düzeltilmiş | fark | maç başına fark (MET1 / MET2 / MET3) |
|---|---|---|---|---|---|
{slots}

Düzeltilmiş ölçümde en büyük tekil değişim {tr(slot_single)}, en büyük ortalama değişim {tr(slot_mean)}.

*3. Kaleci teşhisi (MET1-3, aynı kopyalar, deney ortamında yeniden çalıştırıldı), ortalama spellF1:*

| durum | ilk yazılan | fark | düzeltilmiş | fark |
|---|---|---|---|---|
{roles}

**Ne öğrendik.** "Aynı betik" iki ortamda aynı sonucu vermek zorunda değildir; etiket üreten kod da
çıktı üreten kod kadar ortamdan bağımsız olmalı. Bundan sonra dış etiketle puanlama yapan her kayıt,
çalıştığı Python / pandas / numpy sürümlerini yazar; vekil etiketlerin özeti (SHA-256) düzeltme dosyasındaki
değerle karşılaştırılabilir.

'''
p = R / 'docs/DENEY_KAYDI_TR.md'
s = p.read_text(encoding='utf-8')
head = '# Deney kaydı\n\n'
assert s.startswith(head) and 'K005' not in s.split('## K004')[0]
s = head + text + s[len(head):]
k3h = '## K003 — Okuyucu denetimi, girdi öz-denetimi, tam boy prova, slot ve çift izleme ölçümü, yedek sürüm, son test planı, 11 Kasım 2026\n'
assert s.count(k3h) == 1
s = s.replace(k3h, k3h + '\n> **Düzeltme (K005, 11 Kasım 2026).** Bu girdide dış etiketlere göre yazılan prova puanları ve slot / çift\n'
              '> izleme ölçümü, duran top aralıklarının yarısını yitirmiş Metrica vekil etiketleriyle hesaplanmıştı. Düzeltilmiş\n'
              '> sayılar K005 girdisinde ve `possession-label-order-correction.json` dosyasındadır. Aşağıdaki metin ilk hâliyle\n'
              '> bırakılmıştır; zincirin adımları, süre, bellek ve bayt karşılaştırmaları etkilenmez.\n')
p.write_text(s, encoding='utf-8')
print(text[:1500])
