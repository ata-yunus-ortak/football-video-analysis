"""Freeze the v2.5 release after the v2.5b verdict: release flag, tool/launchers, manifest, results, docs, lists."""
import json, shutil, subprocess, sys
from pathlib import Path
S = Path('/home/claude/sc'); W = Path('/home/claude/work')
SCR = Path('/tmp/claude-0/-home-claude/8ee93673-040f-5f7f-b5ac-603877427998/scratchpad')
b = json.loads((W / 'exp_v25b.json').read_text())
use_clock = bool(b['selected'])
g = b['summary']['good']


def edit(path, old, new):
    p = S / path
    t = p.read_bytes().decode('utf-8')
    assert t.count(old) == 1, (path, old[:60])
    p.write_bytes(t.replace(old, new).encode('utf-8'))


# 1. release flag
edit('possession/run25.py', 'USE_CLOCK = None   # set at freeze: True if the clock-anchored alignment (v2.5b) was selected',
     f'USE_CLOCK = {use_clock}   # frozen: the clock-anchored alignment (v2.5b) was {"selected" if use_clock else "NOT selected"}')
# 2. tool and launchers
shutil.copy(SCR / 'SAHIPLIK-V25-URET.cmd', S / 'SAHIPLIK-V25-URET.cmd')
if use_clock:
    shutil.copy(SCR / 'possession_clock.py', S / 'tools' / 'possession_clock.py')
    shutil.copy(SCR / 'SAAT-OKU.cmd', S / 'SAAT-OKU.cmd')
# 3. results + manifest
subprocess.run([sys.executable, str(W / 'assemble_v25b.py')], check=True)
subprocess.run([sys.executable, str(W / 'make_release25.py')], check=True)
# 4. docs
subprocess.run([sys.executable, str(W / 'doc_v25.py'), '1' if use_clock else '0'], check=True)
subprocess.run([sys.executable, str(W / 'doc_v25_tr.py'), '1' if use_clock else '0'], check=True)
entry = f'''## P008 — Saatle çapalanmış yayın eşlemesi (v2.5b), {"SEÇİLDİ" if use_clock else "seçilmedi"}, 10 Kasım 2026

Ekibin önerisi: iki videoda da görünen maç saatiyle kareleri eşlemek. Plan
`possession-v25b-plan.json` (14:03:16; v2.5'in ilk 10 satırı görüldükten sonra yazıldı).
`possession/clocksync.py`, S002'deki OCR çıktısını (`tools/clock_observations.py`) okur. Tutarlı
saat dizilerini eşler; uzatma dakikası gibi iki kez görünen saatleri atlar. Her yarı için ortanca
zaman farkını verir: en az 10 eşleşme, IQR ≤ 1,5 s. Eksen yönü ve takım eşlemesi bu farkta
seçilir; ince ayar ±40 karede yapılır (`possession/fusion.py`). Saat yoksa v2.5'in yörünge
araması kullanılır.

Doğrulama 16 YENİ kopyada (tohum 3100+/3500+) yapıldı. Saat okumaları sentetikti: okunabilirlik
%50-95, hatalı okuma %1-3, uzatma dakikaları ikinci yarıyla çakışıyor. İyi rejimde v2.4
{g['v2_4']:.3f}, v2.5 {g['v2_5']:.3f}, v2.5b {g['v2_5b']:.3f}. Başarısız eşleme v2.5'te
{g['alignment_failures']['v2_5']}, v2.5b'de {g['alignment_failures']['v2_5b']}. Orta rejimde
v2.5b {b['summary']['medium']['v2_5b']:.3f}, kötü rejimde {b['summary']['bad']['v2_5b']:.3f}
(v2.4 {b['summary']['medium']['v2_4']:.3f}).
Kayıtlı koşullar: {', '.join(k + (' ✓' if v else ' ✗') for k, v in b['gates'].items())}.
{"Teslim sistemi saat çapasını kullanıyor; saat dosyası verilmezse yörünge eşlemesine düşüyor." if use_clock else "Teslim sistemi yalnız yörünge eşlemesini kullanıyor."}
Sonuçlar: `possession-v25b-results.json`.

'''
p = S / 'docs' / 'DENEY_KAYDI_TR.md'
t = p.read_text()
anchor = '## P007 — '
assert t.count(anchor) == 1
p.write_text(t.replace(anchor, entry + anchor))
print('finalized; use_clock =', use_clock)
