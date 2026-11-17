"""K021, part B (records only): log entry, status snapshot, commit message and index row for (1) the chain run of
16 November 2026 23:31 on commit cc62a5f and (2) the documents-only change of part A (docs_k021_a.py).
Input: the shareable status file of that run (PAYLASILABILIR-durum.txt; nothing else of the run was read).
Every replacement must match exactly once. Usage: python3 docs_k021_b.py REPO_DIR STATUS_FILE"""
import re, shutil, sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
V = Path(__file__).resolve().parent
lines = [l.rstrip() for l in Path(sys.argv[2]).read_text(encoding='utf-8', errors='replace').splitlines()]
steps = [l for l in lines if re.match(r'^\[ ?\d+\] ', l)]
sonuc = [l for l in lines if l.startswith('SONUC')]
assert len(steps) == 18 and sonuc == ['SONUC: TESLIM HAZIR'], (len(steps), sonuc)
assert lines[0].startswith('POSSESSION TESLIM ZINCIRI  2026-11-16 23:31') and '(possession-v2.16)' in lines[0], lines[0]
find = lambda key: next(l for l in steps if f'] {key} ' in l)
assert find('DEPO').endswith('commit cc62a5fadffc, temiz')
assert find('URETIM').endswith('OK (possession-v2.16, saatli)')
assert find('TESLIM').endswith('OK (possession-v2.16, saatli; onceki teslim dosyasi ile AYNI)')
assert find('TEMIZ KLON').endswith('AYNI (commit cc62a5fadffc)') and find('PLATFORM').endswith('AYNI') and find('TESTLER').endswith('OK')
block = '\n'.join(steps + sonuc)


def edit(rel, pairs, newline=None):
    p = REPO / rel
    s = p.read_bytes().decode('utf-8')
    if newline:
        assert s.count('\r\n') == s.count('\n'), rel
        s = s.replace('\r\n', '\n')
    for o, n in pairs:
        assert s.count(o) == 1, (rel, s.count(o), o[:100])
        s = s.replace(o, n)
    if newline:
        s = s.replace('\n', newline)
    p.write_bytes(s.encode('utf-8'))


# ---------------------------------------------------------------- experiment log (newest entry on top)
K021 = f"""## K021 — Zincir K019-K020 kayıtlarıyla OK; teslim belgesindeki süreç açıklaması organizatörün istediği dört maddeye göre genişletildi (yalnız belge), 16-17 Kasım 2026

**Zincir (16 Kasım 23:31 - 17 Kasım 00:24).** Takım lideri `TESLIM-TEK-TIK.cmd`'yi çalıştırdı. Commit `cc62a5f` (K019-K020
kayıtları, 59 dosya) GitHub'a gitti; GitHub Actions bu commit'te başarılı (çalıştırma 16, 8 dk 41 sn). Paylaşılabilir durum
satırları (`Desktop\\logs\\PAYLASILABILIR-durum.txt`; başka hiçbir çıktı okunmadı):

```
{block}
```

Sürüm `possession-v2.16`. `TESLIM` satırı yine `onceki teslim dosyasi ile AYNI` diyor: dosya, 15 Kasım'da forma yüklenen dosyayla
aynı baytlardır (K019). Dosya ikinci çalıştırmada, saat okumaları olmadan ve dalın temiz klonundan da aynı baytlarla üretildi.
Bunlar özet (hash) karşılaştırmalarıdır; doğruluk ölçümü değildir.

**Süreç açıklaması: yalnız belge değişti; kod, model, sürüm dosyası ve seçim yok.**
- *Neden.* Takım lideri 16 Kasım 23:40'ta, 3 Kasım'dan önceki dönemin organizatöre bildirildiğinin, organizatörün cevabının ve
  yeniden başlamanın teslim belgesinde daha açık yazılmasını istedi.
- *Kaynaklar* (takım liderinin posta kutusunda, 16 Kasım 23:45'te yeniden okundu): ekibin organizatöre 31 Ekim 2026 e-postası,
  organizatörün 3 Kasım 2026 08:40 UTC cevabı, ekibin 3 Kasım 2026 11:08 UTC bildirimi. Ayrıca `rules-provenance.json`,
  `REMEDIATION.md`, uzun belgenin 2. bölümü.
- *Bulunan eksik.* Organizatörün cevabındaki dördüncü şart, teknik belgede dört şeyin yazılmasını ister: ne olduğu, hangi
  aşamaların etkilendiği, çalışılan kural metni ve seçimin nasıl yeniden yapıldığı. Forma yüklenen kısa belgenin 6. bölümünde
  kural metni ve etkilenen aşamalar yoktu; yalnız uzun belgede vardı.
- *6. bölümün yeni içeriği* (`TECHNICAL_DOCUMENT.md`): çalışılan kural metni (20 Ekim 2026 tarihli `RULES.md`, SHA-256'sı;
  ifade organizatörün 22-23 Ekim açıklamasıyla değişti, ekip Ekim sonuna kadar eski kopyayla çalıştı); ne olduğu; bildirim
  (31 Ekim) ve cevap (3 Kasım; organizatörün kendi sözleriyle: ifade kendi kurallarındaydı, durum iyi niyetli sayılıyor, ekip
  dört şartla devam edebilir ve teslim normal değerlendirilir); etkilenen aşamalar; her şartın karşısında ne yapıldığı.
- *Uzun belgede düzeltme* (`TECHNICAL_DOCUMENT_V2.md`, 2. bölüm): "Until the 22-23 October clarification the team worked from a
  local copy" diye başlayan cümle, anlatılan işin o tarihte bittiği gibi okunuyordu. Ekibin 31 Ekim e-postası eski kopyayla
  çalışmanın sürdüğünü söyler. Cümle düzeltildi; düzeltme cümlenin içinde tarihiyle yazılıdır.
- *Sağlayıcı tarafı.* Takım lideri 16 Kasım 23:52'de eski sohbetin silindiğini ve sağlayıcı tarafını başka bir araçla kendisinin
  doğruladığını bildirdi. Bu süreç o denetimi yapmadı ve görmedi. Belgelerde "takım lideri kendisi doğruladı" diye yazıldı;
  `REMEDIATION.md`'ye onun beyanı olarak tarihli bir not eklendi. O dosyanın 3 ve 7 Kasım notları değiştirilmedi.
  `AGENTS.md`'deki ilgili satır kayda göre güncellendi.
- *Betikler:* `experiments/possession_v2/v219/docs_k021_a.py` (belgeler), `docs_k021_b.py` (bu kayıt).

**Testler.** Kod değişmedi; tam takım K020'deki kod üzerinde çalışmıştı (467 test). Belgeyi okuyan `tests.test_possession_deliver`
yeni metinle Python 3.13 ve Python 3.10 altında yeniden çalıştırıldı: 13 test, hata yok.

**Sıradaki.** Yeni 6. bölümün `LittleSickle.md`'ye girmesi için takım lideri zinciri bir kez daha çalıştırır; form o son
çalıştırmanın belgesiyle gönderilir. Sahiplik dosyası değişmez (kod ve sürüm aynı). Formun K019'dan sonra yeniden gönderildiği
bu kayıt yazılırken teyit edilmemişti.

"""
edit('docs/DENEY_KAYDI_TR.md', [("# Deney kaydı\n\n## K020 — ", "# Deney kaydı\n\n" + K021 + "## K020 — ")])

# ---------------------------------------------------------------- status snapshot for agents
edit('CLAUDE.md', [
    ("## Status snapshot (16 Nov 2026, afternoon — verify before relying on it)\n\n"
     "- **Submission system: still `possession-v2.16`** (`python -m possession.run216`). Nothing of the release changed today.\n",
     "## Status snapshot (17 Nov 2026, 00:40 — verify before relying on it)\n\n"
     "- **Submission system: still `possession-v2.16`** (`python -m possession.run216`). Nothing of the release changed on 16 Nov.\n"
     "- **K021 (16 Nov 23:31 - 17 Nov 00:24): the chain ran OK on commit cc62a5f** (K019-K020 records; every step OK;\n"
     "  `TESLIM ... onceki teslim dosyasi ile AYNI`; `TEMIZ KLON AYNI`; GitHub Actions run 16 succeeded). **Documents only since\n"
     "  then:** at the team lead's request Section 6 of `TECHNICAL_DOCUMENT.md` (the delivered document) now has the four items\n"
     "  the organisers' reply of 3 Nov asks for (rules snapshot, what happened, affected stages, how the selection was re-done)\n"
     "  and says what that reply answered (a \"good-faith situation\"; the team may continue and be evaluated as normal on four\n"
     "  conditions) and what was done for each condition. One sentence of `TECHNICAL_DOCUMENT_V2.md` Section 2 was corrected (the\n"
     "  team worked from its old `RULES.md` until the end of October). The provider-side cleanup is written as the team lead\n"
     "  stated it on 16 Nov (he verified it himself; no agent saw that check; `REMEDIATION.md` records it as his statement and\n"
     "  keeps its earlier entries). Keep to that form: say what was done and where it is recorded. **Still open:** one more\n"
     "  chain run by the team lead so that `LittleSickle.md` carries the new Section 6, then the Form.\n"),
    ("  The technical document changed today (Section 3 tells of the fourth attempt): one more chain run regenerates\n"
     "  `LittleSickle.md`, and the Form should then be sent again with it.\n",
     "  The technical document changed on 16 Nov (Section 3: the fourth attempt; Section 6: the extended disclosure, K021): the\n"
     "  Form is sent again with the `LittleSickle.md` of the chain run that follows the K021 commit.\n"),
])

# ---------------------------------------------------------------- index of experiment scripts
edit('experiments/possession_v2/README.md', [
    ("| superseded, not run | `test_final_wmx.py`",
     "| K021 documents only: process disclosure of the delivered document (Section 6), one corrected sentence of the long document, the team lead's "
     "statement in `REMEDIATION.md`; log entry | in `v219/`: `docs_k021_a.py` (documents), `docs_k021_b.py` (log entry, status snapshot, commit message; "
     "input: the shareable status file of the chain run) |\n"
     "| superseded, not run | `test_final_wmx.py`"),
])

# ---------------------------------------------------------------- commit message of the upload script (CRLF file)
p = REPO / 'GIT-YUKLE-V2.cmd'
s = p.read_bytes().decode('ascii')
assert s.count('\r\n') == s.count('\n')
s = s.replace('\r\n', '\n')
# REMEDIATION.md changes in this commit and was not in the list of paths the script stages
o_, n_ = ' TECHNICAL_DOCUMENT_V2.md DATA_SOURCES.md README.md ', ' TECHNICAL_DOCUMENT_V2.md REMEDIATION.md DATA_SOURCES.md README.md '
assert s.count(o_) == 1 and 'REMEDIATION.md' not in s
s = s.replace(o_, n_)
a = s.index('> "%POSSESSION_MSG1%" echo Records K019-K020:')
b = s.index('>> "%POSSESSION_MSG1%" echo Co-Authored-By:')
msg = ["Record K021: chain OK on cc62a5f; process disclosure of the delivered document extended, documents only",
       "",
       "K021: on 16 Nov 23:31 the delivery chain ran end to end on the team lead computer on commit cc62a5f, every step OK.",
       "The file has the same bytes as the one already delivered, also on a second run and from a fresh clone.",
       "",
       "Documents only since then, at the team lead request. Section 6 of TECHNICAL_DOCUMENT.md now has the four items the",
       "organisers asked for in their reply of 3 Nov: the rules snapshot the team worked from in October, what happened,",
       "the affected stages and how the selection was re-done. It also says what that reply answered and what was done for",
       "each of its conditions. One sentence of TECHNICAL_DOCUMENT_V2.md Section 2 is corrected: the team worked from its old",
       "copy of RULES.md until the end of October. REMEDIATION.md records a statement of the team lead of 16 Nov about the",
       "provider side as his statement. Its earlier entries are unchanged. No code, model or release file changed.",
       "",
       "No provided match data and no frame-level output are in the repository.",
       ""]
for m in msg:
    assert not re.search(r'[&|<>^%()!"]', m), m
new = ''.join(('> ' if i == 0 else '>> ') + '"%POSSESSION_MSG1%" echo' + ('.' if not m else ' ' + m) + '\n' for i, m in enumerate(msg))
s = s[:a] + new + s[b:]
assert new.count('\n') == len(msg) and s[a + len(new):].startswith('>> "%POSSESSION_MSG1%" echo Co-Authored-By: Claude Fable 5.2 ^<noreply@anthropic.com^>\n'
                                                                    '>> "%POSSESSION_MSG1%" echo Claude-Session: https://claude.ai/code/session_01XFbvRnLFWRaGyWGvKPjhiv\n'
                                                                    'git commit -q -F "%POSSESSION_MSG1%"\n')
p.write_bytes(s.replace('\n', '\r\n').encode('ascii'))

# ---------------------------------------------------------------- archive the two scripts next to the others of 16 Nov
dst = REPO / 'experiments' / 'possession_v2' / 'v219'
for n in ('docs_k021_a.py', 'docs_k021_b.py'):
    shutil.copyfile(V / n, dst / n)
print('K021 part B written: log entry, status snapshot, index row, commit message; scripts archived')
