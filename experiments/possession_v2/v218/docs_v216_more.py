"""Records of K016 (camera priority, exploration) and K017 (possession-v2.16: validation, selection, integration): log
entries, the long record, README, AGENTS.md, DATA_SOURCES.md, the Turkish guide, the experiments archive, the rehearsal
sentence of the short document. Numbers come from possession-k016-camera-priority.json, possession-v216-results.json,
possession-v216-release.json and possession-v216-rehearsal.json. Run once, after docs_v216_en.py and
assemble_rehearsal_v216.py. Usage: docs_v216_more.py REPO_DIR"""
import json, sys, shutil
from pathlib import Path
import numpy as np
REPO = Path(sys.argv[1]); V = Path('/home/claude/work/v218')
K = json.loads((REPO / 'possession-k016-camera-priority.json').read_text())
R = json.loads((REPO / 'possession-v216-results.json').read_text())
PLAN = json.loads((REPO / 'possession-v216-plan.json').read_text())
REL = json.loads((REPO / 'possession-v216-release.json').read_text())
H = json.loads((REPO / 'possession-v216-rehearsal.json').read_text())
S, G = R['summary'], R['gates']
T = K['spell_f1_difference_to_the_release_by_stream_regime']
U = K['how_much_of_each_camera_the_release_uses']['simulated_copies_share_of_graded_frames']
D = K['stream_that_loses_and_invents_players']['F_minus_release']
assert R['selected'] and all(g['passed'] for g in G.values())
tr = lambda x, nd=4: f'{x:+.{nd}f}'.replace('.', ',')
tn = lambda x, nd=4: f'{x:.{nd}f}'.replace('.', ',')
pc = lambda x, nd=0: f'%{100 * x:.{nd}f}'.replace('.', ',')
en = lambda x, nd=4: f'{x:+.{nd}f}'
new, old, dif = H['delivered_file_against_the_bundle_labels'], H['for_comparison_the_v2.15_chain_file'], H['against_the_v2.15_file']
S_NEW, S_OLD = new['graded windows']['spell_f1_mean'], old['graded windows']['spell_f1_mean']
PCT = 100 * dif['share_of_graded_frames']
TESTS = {'py313': (467, 4), 'py310': (467, 15)}
for name, (n, sk) in TESTS.items():
    tail = (V / f'tests_{name}.log').read_text().strip().splitlines()[-3:]
    assert any(f'Ran {n} tests' in l for l in tail) and tail[-1] == f'OK (skipped={sk})', tail


def edit(name, pairs, binary=False):
    p = REPO / name
    s = p.read_bytes().decode('ascii') if binary else p.read_text(encoding='utf-8')
    for a, b in pairs:
        assert s.count(a) == 1, (name, s.count(a), a[:70])
        s = s.replace(a, b)
    if binary:
        assert s.count('\n') == s.count('\r\n')
        p.write_bytes(s.encode('ascii'))
    else:
        p.write_text(s, encoding='utf-8')
    return s


# ------------------------------------------------------------------ experiment log (Turkish), newest first
def row16(reg, v):
    x = T[reg].get(v)
    return '—' if x is None else f"{tr(x['mean'])} ({x['better']}/{x['worse']}, {x['copies']} kopya)"

VAR_TR = [('T', 'ikinci kamera hiç kullanılmaz'), ('B1', 'iki kamera 0,5 m içinde tutarlıysa top yayından'), ('B2', 'iki kamera da topu görüyorsa top hep yayından'),
          ('C', 'tutarlı yerde iki topun ortalaması'), ('P', 'tutarlı top ve tutarlı oyuncular yayından'), ('F', 'taktiğin kaybettiği oyuncular yayından eklenir'),
          ('PF', 'P ve F birlikte')]
t16 = '\n'.join(f"| {v} | {name} | {row16('sharp', v)} | {row16('good', v)} | {row16('medium', v)} |" for v, name in VAR_TR)
ug, us = U['good'], U['sharp']
K016 = f"""## K016 — İkinci kameraya öncelik vermek işe yaramıyor; işe yarayan, birincinin göremediğini eklemek (keşif; bir aday çıktı), 15 Kasım 2026

**Neden.** Takım lideri 15 Kasım 12:24'te sordu: yayın kamerası daha yakından ve net görüyor; taktik kamerayla tutarlı olduğu
yerlerde yayın kamerasına öncelik versek, az sayıda oyuncu görse bile o noktada onu temel alsak daha iyi olmaz mı? Ayrıca şu an
maçın ne kadarında hangi kamerayı kullanıyoruz? Bu kayıt geliştirme kopyalarında benzetilmiş ikinci kamerayla yapılan keşiftir;
plan kaydedilmedi. Sağlanan maç açılmadı. Sayılar: `possession-k016-camera-priority.json`; betikler:
`experiments/possession_v2/v218/` (`cam1.py`, `cam2.py`, `cam3.py`).

**Şu an hangi kameradan ne alıyoruz.** Taktik takip verisi her karede temeldir (bütün oyuncular ve top). Yayın takip verisinden
yalnız top alınır; yalnız taktik top eksikse, o kare için kabul edilmiş bir yayın karesi varsa ve iki kamera topta 0,50 m içinde
anlaşıyorsa. Yayın oyuncuları yalnız kalibrasyon hatasını ölçmek için kullanılır. Videoların görüntüsünden yalnız maç saati
okunur. Sağlanan maçtaki oranlar bu kayıtta yoktur (maç verisi ve ondan hesaplanan sayılar ajana verilmez). Benzetilmiş
kopyalarda (yayın "iyi" düzeyde, 8 kopya, puanlanan karelerin payı): taktik top {pc(ug['share_tactical_ball'])}, yayından doldurulan {pc(ug['share_ball_filled_from_broadcast'])}, iki kamerada da
top yok {pc(ug['share_no_ball_after_fill'])}; iki kamera topu birlikte {pc(ug['share_both_balls'])} karede görüyor ({pc(ug['share_both_within_0.5m'])}'inde 0,5 m içinde). Kabul edilmiş yayın karesi olan
kareler {pc(ug['share_frames_with_an_accepted_broadcast_frame'])}.

**Yöntem.** Dört doğrulama maçı (J03WN1, J03WR9, MET1, MET2), maç başına iki bozulmuş kopya; her kolda v2.15 kararı. İkinci
kamera temiz konumlardan benzetildi (top çevresinde pencere, yakın çekim ve tekrarlar, çekim başına kalibrasyon kayması, gürültü),
üç düzeyde: **keskin** (yayın, taktik kopyadan belirgin biçimde daha hassas: top hatası ortanca {tn(us['median_error_m_broadcast_ball_where_both'], 2)} m, taktikte
{tn(us['median_error_m_tactical_ball_where_both'], 2)} m; oyuncularda {tn(us['players']['median_error_m_of_their_broadcast_positions'], 2)} m ve {tn(us['players']['median_error_m_of_replaced_tactical_positions'], 2)} m), **iyi** ve **orta** (v2.5 / v2.9 / v2.15 doğrulamalarındaki düzeyler). Hizalama, kayıt
(registration), kapı ve top doldurma her seçenekte sürümdeki gibidir; yalnız modellerin gördüğü top ya da oyuncular değişir.

**Sonuç: sürüme göre spellF1 farkı** (parantez içinde: daha iyi / daha kötü kopya sayısı).

| | seçenek | keskin yayın | iyi yayın | orta yayın |
|---|---|---|---|---|
{t16}

- **Önceliği yayına vermek kazandırmıyor.** Yayın beş kat daha hassas olsa bile fark ±0,002 içinde; yayın daha kabaysa
  −0,004 / −0,005. İki ölçüm yarım metre içinde anlaşıyorsa hangisini seçtiğimiz az şey değiştirir; modelleri sınırlayan,
  eğitildikleri düzeyin altındaki hassasiyet değil.
- **İkinci kameranın değeri, birincinin görmediğini görmesinde.** İkinci kamera hiç kullanılmazsa puan {tn(-T['good']['T']['mean'], 3)}-{tn(-T['sharp']['T']['mean'], 3)} düşüyor
  (8 kopyanın 8'inde). Tutarlı oyuncuların {pc(ug['players']['share_of_tactical_player_positions_replaced'])}'ü (topa 15 m'den yakın olanların {pc(ug['players']['share_replaced_among_players_within_15m_of_the_ball'])}'u) yayından alınabiliyor, ama almak bir
  şey kazandırmıyor.
- **Taktiğin kaybettiği oyuncuları eklemek (F) kazandırıyor:** keskin yayında {tr(T['sharp']['F']['mean'])}, iyi yayında {tr(T['good']['F']['mean'])} (4'er kopya).
  Yayın akışı kendi de oyuncu kaybedip uydursa ve takımları karıştırsa bile (`cam3.py`: her iz zamanın %10'unda yok, dört hayalet
  iz, iki iz daha yanlış takımda; eklenen konumların yalnız %41-67'si gerçek oyuncu) {tr(D['mean'])} (en kötü kopya {tr(D['min'])}).
  12 karşılaştırmanın 9'unda daha iyi, en kötüsü {tr(min(min(T['sharp']['F']['per_copy'].values()), min(T['good']['F']['per_copy'].values()), D['min']))}. Konumları da değiştiren PF belirgin biçimde daha iyi değil ve taktik
  konumlara dokunuyor.

**Karar.** F, önceki planların kapılarıyla aday olarak kaydedildi (`possession-v216-plan.json`, K017). Öteki seçenekler
kullanılmadı.

**Sınırlar.** Karşılaştırma başına 4 (B1 ve P için 8) geliştirme kopyası; 0,005'in altındaki farklar kopyalar arası
dağılımın içindedir. İkinci kamera benzetimdir; sağlanan yayın verisinin nasıl davrandığına bakılmadı. Sayılar bozulmuş dış
kopyalarda başka sağlayıcıların etiketleriyle uyumdur; yarışma puanı değildir.

"""
cond_tr = {'good': 'iyi yayın kamerası, 16 kopya', 'medium': 'orta kalitede yayın kamerası, 8 kopya', 'good_degraded': 'oyuncu kaybeden / uyduran yayın kamerası, 8 kopya',
           'sim2_good': 'ekip arkadaşının benzeticisiyle taktik kopya, iyi yayın, 4 kopya'}
t17 = '\n'.join(f"| {cond_tr[c]} | {tn(S[c]['v2_15_mean'])} | {tn(S[c]['candidate_mean'])} | {tr(S[c]['mean_diff'])} | {tr(S[c]['dfl'])} | {tr(S[c]['metrica'])} | "
                f"{S[c]['better']} / {S[c]['worse']} | {tr(S[c]['min'])} | {tr(S[c]['mean_diff_without_second_model'])} |" for c in cond_tr)
gate_tr = [('G1 gain', 'G1 kazanç (iyi yayın, 16 kopya)', '≥ +0,008'), ('G2 gain on provider flags', 'G2 DFL kopyaları (8)', '≥ +0,008'),
           ('G3 no harm on event proxies', 'G3 Metrica kopyaları (8)', '≥ −0,002'), ('G4 no bad copy', 'G4 en kötü kopya', '≥ −0,010'), ('G5 macroF1', 'G5 macroF1', '≥ −0,003')]
g17 = '\n'.join(f"| {name} | {thr} | {tr(G[k]['value'])} | geçti |" for k, name, thr in gate_tr)
g17 += f"\n| G6 öteki akışlar (orta; oyuncu kaybeden / uyduran) | her biri ≥ 0,000 | {tr(G['G6 other streams']['medium'])}; {tr(G['G6 other streams']['good_degraded'])} | geçti |"
g17 += f"\n| G7 öteki benzetici (4 kopya) | ≥ 0,000 | {tr(G['G7 other simulator']['value'])} | geçti (kıl payı) |"
ap = H['added_players_in_this_synthetic_run']
def addstat(cond, key):
    rr = [x['added'] for x in R['rows'] if x['condition'] == cond]
    if key == 'ratio':
        return float(np.mean([a['player_positions_added'] / a['tactical_player_positions'] for a in rr]))
    return float(np.mean([a[key] for a in rr]))
FIRST_ROW = min((V / f'exp_v216_{p}.log').read_text().split()[0] for p in range(4))
assert PLAN['registered_at'][11:19] < FIRST_ROW
K017 = f"""## K017 — possession-v2.16: taktik kameranın kaybettiği oyuncular yayın kamerasından eklenir (kayıtlı doğrulama geçti; sürüm), 15 Kasım 2026

**Ne.** v2.16 = v2.15 + bir adım (`possession/playerfill.py`): yayın dosyaları varsa ve top doğruluk kapısı açıksa (iki kamera
topta 0,50 m içinde anlaşıyor), zaman hizalaması ve oyuncu tabanlı kayıttan sonra **1,5 m çevresinde hiçbir takımdan taktik
oyuncu bulunmayan** yayın oyuncusu, modellerin gördüğü takip verisine eklenir (yayın izinin verdiği takımla, iz başına bir ek
yuvada). Taktik konumlar hiç değiştirilmez. Kaleci takım denetimi eklenmiş oyuncularla birlikte çalışır; top önceki gibi
doldurulur. Yayın dosyası yoksa ya da kapı kapalıysa çıktı v2.15'in çıktısıdır (test: adım kapalıyken `run216`, `run215` ile aynı
baytları yazar). Kullanılan düzeltme, yayın topunu düzelten kare başına kaymanın aynısıdır.

**Neden.** K016: ikinci kameraya öncelik vermek kazandırmadı; kazandıran tek kullanım, birinci kameranın kaybettiği oyuncuları
eklemekti. Otomatik takip, oyuncuları en çok birbirine yakın olduklarında bir iki saniyeliğine kaybeder; yayın kamerası topu
izlediği için çoğu zaman onları görür.

**Plan (sonuçlardan önce).** `possession-v216-plan.json`, kayıt {PLAN['registered_at'][11:19]} (ilk doğrulama satırı {FIRST_ROW}). Kural ve tek sabiti
(1,5 m) kayıttan önce sabitlendi; doğrulama betiği keşifteki bir satırı birebir yeniden üretti. 16 yeni bozulmuş kopya (4 maç ×
4 tohum, tohumlar 28100...), benzetilmiş ikinci kamera. İki kol aynı kopyayı, akışı, hizalamayı, kaydı, top doldurmayı ve
modelleri paylaşır; yalnız aday kol oyuncu ekler. Kapılar v2.12-v2.15 planlarındaki yedi kapı ve eşiklerdir; adayın sürümden
farklılaştığı koşullara taşındı (ikinci kamera olmadan aday hiçbir şeyi değiştirmez).

**Sonuç (spellF1; `possession-v216-results.json`).**

| koşul | v2.15 | aday | fark | DFL | Metrica | daha iyi / kötü | en kötü kopya | ikinci model olmadan fark |
|---|---|---|---|---|---|---|---|---|
{t17}

| kapı | eşik | değer | sonuç |
|---|---|---|---|
{g17}

"İyi" koşulda eklenen konumlar taktik oyuncu konumlarının ortalama {pc(addstat('good', 'ratio'), 1)}'si; puanlanan karelerin {pc(addstat('good', 'share_of_graded_frames_with_an_added_player'))}'unda en az bir
eklenmiş oyuncu var. "Orta" koşulda eklenenlerin {pc(addstat('medium', 'share_of_added_within_1m_of_a_clean_player'))}'i, oyuncu kaybeden / uyduran akışta {pc(addstat('good_degraded', 'share_of_added_within_1m_of_a_clean_player'))}'si gerçek bir oyuncunun 1 m
yakınında; kazanç yine de sıfırın üstünde.

**Karar.** Yedi kapının yedisi geçti; kayıtlı kurala göre aday seçildi ve **possession-v2.16** olarak donduruldu
({REL['frozen_at'][:16].replace('T', ' ')}; `possession-v216-release.json`; `run216.py`, `run215.py`'den birebir metin değişiklikleriyle türetildi).
Basamak sırası (`possession-release.json`): v2.16 → v2.15 → v2.11k → v2.11g → v2.9g → v2.5b → v2.5b yalnız taktik.

**Entegrasyon denetimleri (kayıtlı teslim koşulları).**
- Python 3.10.20 / numpy 1.26.4 altında çalışıyor.
- Platformlar arası bayt denetimi artık 11 sentetik varyant (ikisi yeni: taktik izleri altışar saniye kaybolan paketlerde
  oyuncu eklenen v2.1 ve v2.3 yolları); 11'i de Python 3.10 / numpy 1.26.4 ile Python 3.13 / numpy 2.5.3 altında aynı bayt.
- Bütün testler: 467 test, Python 3.13 altında 4 atlama, Python 3.10 (sabitlenmiş paketler) altında 15 atlama, hata yok.
- Tam boy zincir provası (K003 sentetik paketi + K011'in uydurma Smart Tagging dosyası, `possession-v216-rehearsal.json`): bütün
  adımlar OK, {H['seconds']} sn (v2.15 zinciri {H['seconds_of_the_v2.15_chain']} sn), en çok {tn(H['peak_child_rss_gb'], 2)} GB bellek (v2.15: {tn(H['peak_child_rss_gb_of_the_v2.15_chain'], 2)} GB). Bu sentetik pakette
  {ap['player_positions_added']:,} oyuncu konumu eklendi ({ap['frames_with_an_added_player']:,} karede); teslim dosyası v2.15 zincirinin dosyasından puanlanan karelerin
  %{tn(PCT, 1)}'inde farklı; paketin etiketlerine göre spellF1 {tn(S_NEW)} (v2.15 zinciri {tn(S_OLD)}). Bağlantı ve boyut denetimidir; doğruluk ölçümü
  değildir, hiçbir seçimde kullanılmadı.
- Ek R'ye "Players added from the broadcast camera" satırı eklendi (yalnız kategori: kullanıldı / eklenecek oyuncu yok /
  kullanılmadı; sayı yok).

**Kalan koşul.** Zincirin ekibin bilgisayarında OK bitmesi; `URETIM` ve `TESLIM` satırlarında `possession-v2.16` yazmalı. Daha
alt bir basamağın adı yazarsa teslim edilen o basamaktır ve belgeler ona göre düzeltilir.

**Sınırlar.**
- İkinci kamera benzetimdir; oyuncuları temiz dış konumlardan gelir. Dört koşulun üçünde penceresi içinde hiç oyuncu
  kaybetmez ve uydurmaz; dördüncüsü uydurulmuş tek bir hata düzenidir (orada kazanç {tr(S['good_degraded']['mean_diff'])}, bir kopya {tr(S['good_degraded']['min'])}).
- Sağlanan yayın verisine bakılmadı: ne sıklıkta oyuncu kaybettiği ya da uydurduğu bilinmiyor. Yayın verisinde bir takımın
  altında taşınan ama taktik veride olmayan bir hakem, oyuncu olarak eklenir.
- G7 kıl payı geçti ({tr(G['G7 other simulator']['value'])}; 4 kopyanın 3'ünde hafif eksi): az oyuncu kaybeden kopyalarda adım neredeyse hiçbir şey
  değiştirmiyor.
- Adım, dört geliştirme kopyasında yedi seçenek arasından seçildi; doğrulama kopyaları yeni, maçlar yeni değil. Aynı gün aynı
  maçlarda incelenen dördüncü fikirdi (K014, K015, K016). Organizatör, tek maçta 0,04'ün altındaki farkların gürültü olduğunu
  söylüyor.
- Bu, v2.15 planındaki "ikinci modelle başka aday kaydedilmez" kaydını değiştirmez: iki kolda da ikinci model aynıdır.

"""
edit('docs/DENEY_KAYDI_TR.md', [('# Deney kaydı\n\n## K015 —', '# Deney kaydı\n\n' + K017 + K016 + '## K015 —')])
print('log entries written')

# ------------------------------------------------------------------ long record (English)
g = S['good']
FIFTH = f'''>
> **Fifth addendum, 15 November 2026 (v2.16): players the tactical tracking has lost.** The submitted entry point is now
> `python -m possession.run216` (release manifest `possession-v216-release.json`). `possession.run215` is the next
> step of the technical ladder; everything in the fourth addendum still applies.
>
> 1. **The question (K016, exploration).** The team lead asked whether the broadcast camera, being closer, should take
>    priority where it agrees with the tactical camera. On development copies of the four validation matches with a
>    simulated second camera (`possession-k016-camera-priority.json`), with the alignment, registration, gate and ball
>    fill of the release unchanged, the v2.15 decision changed as follows against the release, for a stream clearly
>    more precise than the tactical copy / as precise / less precise: broadcast ball where both cameras agree within
>    0.5 m {en(T['sharp']['B1']['mean'])} / {en(T['good']['B1']['mean'])} / {en(T['medium']['B1']['mean'])}; broadcast ball wherever both see it {en(T['sharp']['B2']['mean'])} / {en(T['good']['B2']['mean'])}; mean of the two
>    balls {en(T['sharp']['C']['mean'])} / {en(T['good']['C']['mean'])}; ball and agreeing players from the broadcast stream {en(T['sharp']['P']['mean'])} / {en(T['good']['P']['mean'])} / {en(T['medium']['P']['mean'])}.
>    Without the second camera the score was {abs(T['good']['T']['mean']):.3f}-{abs(T['sharp']['T']['mean']):.3f} lower on every copy. Priority does not help; what the
>    second camera adds is what the first does not see. On these copies the tactical ball is present on {100 * ug['share_tactical_ball']:.0f}% of
>    graded frames, the broadcast ball fills {100 * ug['share_ball_filled_from_broadcast']:.0f}%, and on {100 * ug['share_no_ball_after_fill']:.0f}% neither camera has it. Adding the broadcast players
>    that the tactical copy lacks gained {en(T['sharp']['F']['mean'])} / {en(T['good']['F']['mean'])} on four copies, and {en(D['mean'])} with a stream that itself loses
>    and invents players.
> 2. **The step** (`possession/playerfill.py`). Per accepted broadcast frame, the offset that `register.py` measures
>    at the ball from players seen by both cameras (median over +-0.5 s) is subtracted from the broadcast players. A
>    registered broadcast player with no tactical player of either team within 1.5 m is written into an extra slot
>    (one per broadcast track) under the team of its track. It runs only when `fusion.fuse_gated` reports the gate
>    open; the goalkeeper team check then runs on tactical + added players. Tactical positions are never moved. The
>    radius is the only constant and the only value tried.
> 3. **Validation** (`possession-v216-plan.json`, registered {PLAN['registered_at'][11:16]} before the first validation row;
>    `possession-v216-results.json`). 16 new corrupted copies, both arms on the same copy, stream, alignment and
>    models. Accurate stream: {g['v2_15_mean']:.4f} -> {g['candidate_mean']:.4f} ({en(g['mean_diff'])}; DFL {en(g['dfl'])}, Metrica {en(g['metrica'])}; {g['better']} better, {g['worse']} worse,
>    single copies {en(g['min'])} to {en(g['max'])}; macroF1 {en(g['mean_diff_macro_f1'])}). Medium stream (8 copies) {en(S['medium']['mean_diff'])}; stream that loses and
>    invents players (8) {en(S['good_degraded']['mean_diff'])} (DFL {en(S['good_degraded']['dfl'])}, Metrica {en(S['good_degraded']['metrica'])}, one copy {en(S['good_degraded']['min'])}); tactical copies of the other
>    simulator (4) {en(S['sim2_good']['mean_diff'])} ({S['sim2_good']['worse']} of 4 lower). The seven gates of the earlier plans, moved to the conditions in which
>    the candidate differs from the release, all passed; the last by {G['G7 other simulator']['value']:.4f}. Without the second model the same
>    step gained {en(g['mean_diff_without_second_model'])} on the accurate stream.
> 4. **Release and checks.** `run216.py` is `run215.py` with exact text replacements (the fill behind the open
>    gate, a report entry, a test switch); with the switch off it writes the bytes of `run215` (test), as it does
>    without broadcast files or with the gate closed (tests). Frozen {REL['frozen_at'][:16].replace('T', ' ')}. The cross-platform check has
>    eleven synthetic variants (two new ones on bundles whose tactical tracks vanish for six seconds at a time, one
>    per model path), byte-identical under Python 3.10 / numpy 1.26.4 and Python 3.13 / numpy 2.5.3; 467 tests pass
>    in both environments. The chain was rehearsed once on the synthetic bundle of K003 with the invented tag file
>    of K011 (`possession-v216-rehearsal.json`): all steps OK in {H['seconds']} s (v2.15 chain {H['seconds_of_the_v2.15_chain']} s), peak memory
>    {H['peak_child_rss_gb']} GB; {ap['player_positions_added']:,} player positions added on that bundle; the file differs from the v2.15 chain
>    file on {PCT:.1f}% of the graded frames; spellF1 {S_NEW:.4f} against {S_OLD:.4f}. A wiring and size check on games used
>    in development, not a selection input. Appendix R has a row that says, as a category, whether players were
>    added. Whether the chain runs on the team's computer is the last condition of the decision rule.
> 5. **Limits.** A simulated second camera whose players come from clean positions; only one of the four
>    conditions lets it lose or invent players. The provided broadcast tracking was not examined; a referee that it
>    carries under a team and the tactical tracking lacks would be added as a player. The step was picked among
>    seven variants on four development copies, on a day on which three other ideas were examined on the same
>    matches. It does not touch the statement of the fourth addendum that no further candidate with the second model
>    is registered: the second model is the same in both arms.
'''
edit('TECHNICAL_DOCUMENT_V2.md', [
    ('# Possession v2 — technical document (full record; current release: v2.15)', '# Possession v2 — technical document (full record; current release: v2.16)'),
    ('Submission file regenerated with `python -m possession.run215` (see the four addenda and Reproduction).',
     'Submission file regenerated with `python -m possession.run216` (see the five addenda and Reproduction).'),
    ('''>    release is unchanged (`possession-k015-tag-rescue.json`, scripts in `experiments/possession_v2/v217/`).
''', '''>    release is unchanged (`possession-k015-tag-rescue.json`, scripts in `experiments/possession_v2/v217/`).
''' + FIFTH),
    ('python -m possession.run215 --data-dir <bundle root containing tactical/ and broadcast/> --out <new folder> \\',
     'python -m possession.run216 --data-dir <bundle root containing tactical/ and broadcast/> --out <new folder> \\'),
    ('`possession.run215` (like `possession.run211k`, `possession.run211`, `possession.run29` and `possession.run25`) reads',
     '`possession.run216` (like `possession.run215`, `possession.run211k`, `possession.run211`, `possession.run29` and `possession.run25`) reads'),
    ('given, the two clock-observation files; `run215` and `run211k` also read the "Kick Off (Start)" tags of',
     'given, the two clock-observation files; `run216`, `run215` and `run211k` also read the "Kick Off (Start)" tags of'),
    ('against the release manifest (`possession-v215-release.json`, which lists every inference source and the three model\nfiles; the lower steps have `possession-v211k-release.json`,',
     'against the release manifest (`possession-v216-release.json`, which lists every inference source and the three model\nfiles; the lower steps have `possession-v215-release.json`, `possession-v211k-release.json`,'),
])

# ------------------------------------------------------------------ README, AGENTS.md, DATA_SOURCES.md
edit('README.md', [
    ('## Submission system: possession v2.15\n', '## Submission system: possession v2.16\n'),
    ('''Release `possession-v2.15`, entry point `python -m possession.run215`, manifest
`possession-v215-release.json`. The release and its technical fall-backs (the next one is
`possession-v2.11k`, the same system without the second model) are named in `possession-release.json`.''',
     '''Release `possession-v2.16`, entry point `python -m possession.run216`, manifest
`possession-v216-release.json`. The release and its technical fall-backs (the next ones are
`possession-v2.15`, the same system without the players added from the second camera, and
`possession-v2.11k`, without the second model as well) are named in `possession-release.json`.'''),
    ('python -m possession.run215 --data-dir <bundle root> --out <new folder> --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast',
     'python -m possession.run216 --data-dir <bundle root> --out <new folder> --tactical-clock <clock>/tactical --broadcast-clock <clock>/broadcast'),
    ('''  simulators) and the average goes through the unchanged decoder (`possession/pooling.py`). On the
  noisier path nothing is averaged.
''', '''  simulators) and the average goes through the unchanged decoder (`possession/pooling.py`). On the
  noisier path nothing is averaged.
- **Players the tactical tracking has lost (v2.16):** when the two cameras agree on the ball (the gate
  of the broadcast fill is open), a registered broadcast player with no tactical player of either
  team within 1.5 m is added to the tracking the models see (`possession/playerfill.py`). Tactical
  positions are never moved; without broadcast files or with the gate closed nothing is added.
'''),
    ('''second model 0.645 -> 0.656 on 16 new copies (better on 14, log entry K013). Tested''',
     f'''second model 0.645 -> 0.656 on 16 new copies (better on 14, log entry K013); players added from a
simulated second camera {g['v2_15_mean']:.3f} -> {g['candidate_mean']:.3f} on 16 further new copies (better on {g['better']}, log entry K017). Tested'''),
    ('''better on 15 of 16 copies but one copy clearly worse; the third way, with a smaller weight, is the
release).''',
     '''better on 15 of 16 copies but one copy clearly worse; the third way, with a smaller weight, is part of
the release). Explored and not registered: forcing a stoppage at set-piece tags (log entry K015) and
giving the broadcast tracking priority where the cameras agree (log entry K016).'''),
])
edit('AGENTS.md', [
    ('''- Possession (`possession/`): the submission system is `possession-v2.15`, entry point
  `python -m possession.run215`, release manifest `possession-v215-release.json`; the release and its
  technical fall-backs (the next one is `possession-v2.11k`, `possession.run211k`) are named in
  `possession-release.json`. v2.15 = v2.11k + a second model family on the core path:''',
     '''- Possession (`possession/`): the submission system is `possession-v2.16`, entry point
  `python -m possession.run216`, release manifest `possession-v216-release.json`; the release and its
  technical fall-backs (the next ones are `possession-v2.15`, `possession.run215`, and
  `possession-v2.11k`, `possession.run211k`) are named in `possession-release.json`.
  v2.16 = v2.15 + players the tactical tracking has lost, added from the broadcast tracking when the
  accuracy gate of the broadcast fill is open (`possession/playerfill.py`; a registered broadcast
  player with no tactical player of either team within 1.5 m; tactical positions are never moved;
  log entries K016 and K017, `possession-v216-plan.json`, `-results.json`). `playerfill.py` and
  `run216.py` are hash-frozen like every other release file: a change needs a new version and plan.
  v2.15 = v2.11k + a second model family on the core path:'''),
])
edit('DATA_SOURCES.md', [
    ('**Second model of the release (v2.15).** Design, features and NumPy inference: the same team member',
     '**Players added from the broadcast tracking (v2.16).** No new data and nothing trained: the step is a fixed rule\n'
     '(`possession/playerfill.py`) validated on new corrupted copies of the validation matches below with a simulated\n'
     'second camera (`possession-v216-plan.json`).\n\n'
     '**Second model of the release (v2.15 and v2.16).** Design, features and NumPy inference: the same team member'),
])

# ------------------------------------------------------------------ team guide (Turkish)
GUIDE = f'''## Güncelleme, 15 Kasım 2026 (akşam): v2.16 — taktik kameranın kaybettiği oyuncular yayın kamerasından eklenir

Teslim sistemi artık **possession-v2.16** (`python -m possession.run216`). Çalıştırma aynı: `TESLIM-TEK-TIK.cmd` ya da
`TESLIM-HAZIRLA.cmd`. Bir alt basamak v2.15'tir (aynı sistem, bu adım olmadan). Ayrıntılı kayıt: `docs/DENEY_KAYDI_TR.md`
K016 ve K017.

**Soru neydi.** "Yayın kamerası daha net; iki kamera tutarlıysa yayını temel alsak?" Dış maçlarda benzetilmiş ikinci
kamerayla ölçtük: önceliği yayına vermek (top, oyuncular ya da ortalama) puanı değiştirmedi (−0,005 ile +0,002), yayın beş
kat keskin olsa bile. İkinci kameranın faydası daha net görmesinden değil, **birincinin göremediğini görmesinden** geliyor.
Bunu şimdiye kadar yalnız top için kullanıyorduk.

**Ne değişti.** Otomatik takip, oyuncuları en çok birbirine yakın olduklarında bir iki saniyeliğine kaybeder. Yayın kamerası
topu izlediği için onları çoğu zaman görür. v2.16, iki kamera topta anlaşıyorsa (0,50 m kapısı açıksa), yayın kamerasının
gördüğü ve çevresinde 1,5 m içinde hiçbir taktik oyuncu bulunmayan oyuncuyu modellerin gördüğü veriye ekler. Taktik
konumlara dokunmaz. Yayın dosyası yoksa ya da kapı kapalıysa sonuç v2.15 ile aynıdır.

**Ölçüm (16 yeni kopya, önceden yazılmış yedi şart).** {tn(g['v2_15_mean'])} → {tn(g['candidate_mean'])} ({tr(g['mean_diff'])}); 16 kopyanın {g['better']}'ünde daha iyi, en
kötü kopya {tr(g['min'])}. Orta kalitede yayın kamerasıyla {tr(S['medium']['mean_diff'])}; kendi de oyuncu kaybeden ve uyduran yayın kamerasıyla {tr(S['good_degraded']['mean_diff'])};
öteki benzeticiyle {tr(S['sim2_good']['mean_diff'])}. Yedi şartın yedisi geçti (sonuncusu kıl payı).

**Dürüst sınırlar.** İkinci kamera benzetimdir; gerçek yayın verisinin ne kadar oyuncu kaybettiğini ya da uydurduğunu
bilmiyoruz ve bakamayız. Yayın verisinde bir takımın altında görünen ama taktik veride olmayan bir hakem, oyuncu diye
eklenir. Az oyuncu kaybeden kopyalarda adım neredeyse hiçbir şey değiştirmiyor. Bu, aynı gün aynı maçlarda incelenen
dördüncü fikirdi; ölçümler sağlanan maç için bir ölçüm değildir.

**Zincirde ne değişti.** `PLATFORM` artık 11 sentetik varyantı karşılaştırır (ikisi oyuncu eklemeli). Belge ekinde (Ek R)
"Players added from the broadcast camera" satırı vardır: kullanıldı / eklenecek oyuncu yok / kullanılmadı.

**Tam boy prova (`possession-v216-rehearsal.json`).** Bütün adımlar OK, {H['seconds']} saniye, en çok {tn(H['peak_child_rss_gb'], 2)} GB bellek. Üretilen
dosya v2.15 zincirinin dosyasından puanlanan karelerin %{tn(PCT, 1)}'inde farklı; o paketin etiketlerine göre spellF1 {tn(S_NEW, 3)}
(v2.15 zinciri {tn(S_OLD, 3)}). Bağlantı ve boyut denetimidir; doğruluk ölçümü değildir. **Kalan koşul:** zincirin ekibin
bilgisayarında OK bitmesi; `URETIM` ve `TESLIM` satırlarında `possession-v2.16` yazmalı. Daha alt bir basamağın adı yazarsa
teslim edilen o basamaktır.

*Öğrenilecek şey:* "daha net olan kaynağa öncelik ver" sezgisi makul görünüyordu ama ölçüm onu desteklemedi; ölçüm
sırasında aynı fikrin başka bir parçası (eksik olanı tamamlamak) işe yaradı. Bir fikri denemenin değeri bazen ilk sorunun
cevabında değil, o sırada görülen başka bir şeydedir. Yine de o "başka şey" ayrı bir planla, yeni veride ölçülmeden sürüme
girmedi.

'''
edit('docs/SAHIPLIK_V2_TR.md', [
    ('''> **Güncel durum (15 Kasım 2026):** teslim sistemi **v2.15**'tir (`python -m possession.run215`).
> Aşağıda anlatılan v2.5 sisteminin üstüne gelen ekler belgenin sonundaki "Güncelleme" bölümlerindedir
> (v2.9, v2.11, 13 Kasım: başlama vuruşu kuralı, 15 Kasım: ikinci model). Bir alt teknik basamak v2.11k'dır.''',
     '''> **Güncel durum (15 Kasım 2026, akşam):** teslim sistemi **v2.16**'dır (`python -m possession.run216`).
> Aşağıda anlatılan v2.5 sisteminin üstüne gelen ekler belgenin sonundaki "Güncelleme" bölümlerindedir
> (v2.9, v2.11, 13 Kasım: başlama vuruşu kuralı, 15 Kasım: ikinci model, 15 Kasım akşam: yayın kamerasından
> eklenen oyuncular). Alt teknik basamaklar v2.15 ve v2.11k'dır.'''),
    ('''`possession-v2.15` → `possession-v2.11k` → `possession-v2.11g` → `possession-v2.9g` → v2.5b → v2.5b yalnız taktik kamera
(15 Kasım'dan beri; v2.15 için belgenin sonundaki güncellemeye bakın).''',
     '''`possession-v2.16` → `possession-v2.15` → `possession-v2.11k` → `possession-v2.11g` → `possession-v2.9g` → v2.5b → v2.5b yalnız taktik kamera
(15 Kasım akşamından beri; v2.15 ve v2.16 için belgenin sonundaki güncellemelere bakın).'''),
    ('''.\\.venv-possession\\Scripts\\python.exe -m possession.run215 --data-dir <veri kökü> --out <yeni klasör>''',
     '''.\\.venv-possession\\Scripts\\python.exe -m possession.run216 --data-dir <veri kökü> --out <yeni klasör>'''),
    ('''*Öğrenilecek şey:* bir fikir ilk ölçümde başarısız olunca iki yol vardır: bırakmak ya da **neden** başarısız olduğunu''',
     GUIDE + '''*Öğrenilecek şey (v2.15):* bir fikir ilk ölçümde başarısız olunca iki yol vardır: bırakmak ya da **neden** başarısız olduğunu'''),
])

# ------------------------------------------------------------------ short document: rehearsal sentence
edit('TECHNICAL_DOCUMENT.md', [
    ('''  frames and scored 0.772 (`possession-v215-rehearsal.json`). This checks wiring and size, not
  accuracy on the provided match; the games in these bundles had been used in development.''',
     f'''  frames and scored 0.772 (`possession-v215-rehearsal.json`). With step 10 it was run once more on
  the same bundle, whose simulated broadcast stream then also supplies players: every step passed,
  the file differs from the previous one on {PCT:.1f}% of the graded frames and scored {S_NEW:.3f}
  (`possession-v216-rehearsal.json`). This checks wiring and size, not
  accuracy on the provided match; the games in these bundles had been used in development.'''),
])

# ------------------------------------------------------------------ archive of the scripts
dst = REPO / 'experiments' / 'possession_v2' / 'v218'
(dst / 'port').mkdir(parents=True, exist_ok=True)
SCRIPTS = ('cam1.py', 'cam2.py', 'cam3.py', 'sum1.py', 'k016_assemble.py', 'exp_v216.py', 'assemble_v216.py', 'register_v216.py', 'freeze_v216.py',
           'score_k017.py', 'assemble_rehearsal_v216.py', 'docs_v216_en.py', 'docs_v216_more.py')
for n in SCRIPTS:
    shutil.copyfile(V / n, dst / n)
shutil.copyfile(V / 'port' / 'make_run216.py', dst / 'port' / 'make_run216.py')
for n in ('exp_v216.py', 'assemble_v216.py', 'cam1.py', 'cam2.py', 'cam3.py', 'register_v216.py'):
    import hashlib
    assert hashlib.sha256((dst / n).read_bytes()).hexdigest() == PLAN['hashes'][n], n            # the registered files, byte for byte
edit('experiments/possession_v2/README.md', [
    ('`/home/claude/work/v216`, `/home/claude/work/v217` | the folders `v213/`, `v214/`, `v215/`, `v216/`, `v217/` below;',
     '`/home/claude/work/v216`, `/home/claude/work/v217`, `/home/claude/work/v218` | the folders `v213/`, `v214/`, `v215/`, `v216/`, `v217/`, `v218/` below;'),
    ('| superseded, not run | `test_final_wmx.py`',
     '| K016 which camera supplies a position both see, and what else the second camera adds; simulated second camera on development copies (reporting only; `possession-k016-camera-priority.json`) | in `v218/`: `cam1.py` (release against broadcast ball / players where the cameras agree, the mean, no second camera; three stream regimes), `cam2.py` (players the tactical copy lost, added), `cam3.py` (the same with a stream that loses and invents players), `sum1.py`, `k016_assemble.py`. They import `v215/exp_v215.py` and `v213/exp_v213.py` |\n'
     '| K017 possession-v2.16: registered validation of the added players, freeze, rehearsal (`possession-v216-plan.json`, `-results.json`, `-release.json`, `-rehearsal.json`) | in `v218/`: `register_v216.py` (plan, before any validation row), `exp_v216.py` (parts 0-3; `wiring` reproduces a row of the exploration), `assemble_v216.py` (gates, written before the rows), `freeze_v216.py` (manifest), `port/make_run216.py` (derives `possession/run216.py` from `run215.py` by exact text replacements), `score_k017.py`, `assemble_rehearsal_v216.py` (chain rehearsal), `docs_v216_en.py`, `docs_v216_more.py`, `docs_v216_status.py` (documents, log entries, status snapshot, launcher) |\n'
     '| superseded, not run | `test_final_wmx.py`'),
])
print('documents written;', len(SCRIPTS) + 1, 'scripts archived')
