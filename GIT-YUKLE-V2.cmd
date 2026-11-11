@echo off
rem Commits the possession release (source, model bundles, plans, results, documents, tests, launchers, experiment scripts)
rem and, as a second commit, the external control-reference tooling that was only on this computer. Then pushes the branch.
rem Every path is named below; nothing else is added. Data file types are refused even if they were listed by mistake.
setlocal
cd /d "%~dp0"
for /f %%b in ('git rev-parse --abbrev-ref HEAD') do set "BR=%%b"
if /i not "%BR%"=="feature/external-possession-selection" (
  echo Su anki dal: %BR%. Once "git checkout feature/external-possession-selection" calistirin.
  pause
  exit /b 1
)
findstr /c:"requirements-possession.txt" ".github\workflows\tests.yml" >nul 2>&1
if not errorlevel 1 goto workflowok
echo.
echo NOT: .github\workflows\tests.yml yalniz requirements.txt kuruyor; GitHub testleri sahiplik testlerini ATLAR.
echo      Isterseniz once o dosyadaki "python -m pip install -r requirements.txt" satirinin sonuna
echo      " -r requirements-possession.txt" ekleyip kaydedin, sonra bu betigi yeniden calistirin.
echo      Bu haliyle devam etmek icin bir tusa basin; iptal icin pencereyi kapatin.
pause >nul
:workflowok
git reset -q
git add -- possession models/possession-v2.npz models/possession-v23.npz "tests/test_possession_*.py" tests/test_ball_patch_data.py "possession-*.json" experiments/possession_v2 tools/possession_clock.py tools/possession_deliver.py tools/possession_final_test.py requirements-possession.txt requirements-possession-train.txt SAHIPLIK-V2-KURULUM.cmd SAHIPLIK-V2-URET.cmd SAHIPLIK-V24-URET.cmd SAHIPLIK-V25-URET.cmd SAHIPLIK-V29-URET.cmd SAHIPLIK-V211-URET.cmd SAAT-OKU.cmd TESLIM-HAZIRLA.cmd SON-TEST.cmd GIT-YUKLE-V2.cmd TECHNICAL_DOCUMENT.md TECHNICAL_DOCUMENT_V2.md DATA_SOURCES.md README.md CLAUDE.md AGENTS.md docs/SAHIPLIK_V2_TR.md docs/DENEY_KAYDI_TR.md .gitignore .gitattributes .github/workflows/tests.yml
if errorlevel 1 (echo git add basarisiz. & pause & exit /b 1)
call :guard
if errorlevel 1 exit /b 1
git diff --cached --quiet
if not errorlevel 1 goto second
echo.
echo ===== 1. commit: sahiplik surumu =====
git diff --cached --stat
echo.
echo Listede .csv, .xml, .mp4, data/ veya FootballPrivate OLMAMALI.
echo Devam etmek icin bir tusa basin; iptal icin bu pencereyi kapatin.
pause >nul
set "POSSESSION_MSG1=%TEMP%\possession_msg1.txt"
> "%POSSESSION_MSG1%" echo Add possession release v2.11: H/A/D system, local delivery chain, records
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo Per-frame H/A/D possession from the provided automatic tracking, trained and selected only on
>> "%POSSESSION_MSG1%" echo external matches (Sportec/DFL open data, Metrica sample games). Core v2.1: position features,
>> "%POSSESSION_MSG1%" echo two gradient-boosted tree models, a second stage on out-of-fold probabilities and a three-state
>> "%POSSESSION_MSG1%" echo Viterbi decoder. v2.4 adds a noise gate with a second model path, v2.5 a broadcast ball fill
>> "%POSSESSION_MSG1%" echo behind a 0.50 m agreement gate with clock-anchored alignment, v2.5c the second-half kick-off
>> "%POSSESSION_MSG1%" echo frame published in the organisers FAQ, v2.9 a broadcast ball registered through the players
>> "%POSSESSION_MSG1%" echo that both cameras see, v2.11 a goalkeeper team check before the features. possession.run29
>> "%POSSESSION_MSG1%" echo (v2.9) stays as the next step of the technical fall-back ladder.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo Frozen bundles models/possession-v2.npz and models/possession-v23.npz with release manifests.
>> "%POSSESSION_MSG1%" echo tools/possession_deliver.py and TESLIM-HAZIRLA.cmd run the whole local chain and print status
>> "%POSSESSION_MSG1%" echo words only. Plans, results and experiment scripts of every candidate are included, also of
>> "%POSSESSION_MSG1%" echo those not selected: Smart Tagging v3, ungated fill v4, v2.2, v2.3 alone, hazard v2.6, gap
>> "%POSSESSION_MSG1%" echo features v2.7, Metrica training v2.8.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo Records audit K002: eight validation copies of v2.9 had been used before. They were replaced
>> "%POSSESSION_MSG1%" echo under an amendment registered before the new results, the unchanged gates were applied once
>> "%POSSESSION_MSG1%" echo and passed. The technical document now has a training data section, and DATA_SOURCES.md names
>> "%POSSESSION_MSG1%" echo the actual download source.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K003: before generating, the chain checks the provided files against the facts DATA.md
>> "%POSSESSION_MSG1%" echo publishes and against a second reading done the way the organisers starter code reads the
>> "%POSSESSION_MSG1%" echo tracking files (possession/inputs_check.py, pass/fail only). The whole chain was rehearsed on
>> "%POSSESSION_MSG1%" echo synthetic bundles with the file names, record counts and slot counts of the provided files
>> "%POSSESSION_MSG1%" echo (possession-rehearsal-results.json). possession.run211g and run29g are reserve entry points without the
>> "%POSSESSION_MSG1%" echo published kick-off frame, for the case that the organisers do not allow that constant.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K004: team ids come from the tracker and goalkeepers wear another kit. A diagnostic on external
>> "%POSSESSION_MSG1%" echo matches showed that goalkeeper tracks under the other team id would cost 0.02 to 0.30 spellF1.
>> "%POSSESSION_MSG1%" echo A first check (v2.10, possession/keeper.py) passed its four registered gates but moved outfield
>> "%POSSESSION_MSG1%" echo players when the far goalkeeper was not tracked; it was not released. The second version (v2.11,
>> "%POSSESSION_MSG1%" echo possession/keeper2.py) was registered and validated with that situation as two additional gates;
>> "%POSSESSION_MSG1%" echo all six passed. Whether the provided tracking has such errors was not looked at.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K005, records correction: the script that derives proxy labels from Metrica events sorted
>> "%POSSESSION_MSG1%" echo simultaneous events unstably. In the Python 3.10 environment the labels lost about half of their
>> "%POSSESSION_MSG1%" echo dead-ball intervals; every selection, gate, validation and reserved test had run in the
>> "%POSSESSION_MSG1%" echo experiment environment, where the labels are in file order. The K003 rehearsal scores, its slot
>> "%POSSESSION_MSG1%" echo diagnostic and the goalkeeper diagnostic were recomputed
>> "%POSSESSION_MSG1%" echo (possession-label-order-correction.json); the script now sorts stably.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo A final test of the frozen release on the reserved DFL match J03WMX is registered
>> "%POSSESSION_MSG1%" echo (possession-final-test-plan.json, tools/possession_final_test.py, SON-TEST.cmd) and was registered
>> "%POSSESSION_MSG1%" echo again for v2.11 before any access to the match. The match has not been downloaded; the test is
>> "%POSSESSION_MSG1%" echo run once and reported whatever the result.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo No provided match data and no frame-level output are in the repository. External numbers are
>> "%POSSESSION_MSG1%" echo agreement with other providers labels, not competition scores.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo Co-Authored-By: Claude Fable 5.2 ^<noreply@anthropic.com^>
>> "%POSSESSION_MSG1%" echo Claude-Session: https://claude.ai/code/session_01XFbvRnLFWRaGyWGvKPjhiv
git commit -q -F "%POSSESSION_MSG1%"
if errorlevel 1 (echo Commit olusturulamadi. & pause & exit /b 1)
:second
git add -- development/transition_benchmark.py tests/test_control_pipeline.py tools/control_review_pack.py tools/control_reference.html tools/control_reference.js tools/control_reference_check.py tools/control_reference_workspace.py tests/test_reference_check.py tests/test_reference_scope.py
if errorlevel 1 (echo git add basarisiz. & pause & exit /b 1)
call :guard
if errorlevel 1 exit /b 1
git diff --cached --quiet
if not errorlevel 1 goto push
echo.
echo ===== 2. commit: dis kaynakli kontrol referansi araclari =====
git diff --cached --stat
echo Devam etmek icin bir tusa basin; iptal icin bu pencereyi kapatin.
pause >nul
set "POSSESSION_MSG2=%TEMP%\possession_msg2.txt"
> "%POSSESSION_MSG2%" echo External control reference tooling: reviewed event kinds, workspace builder, checks
>> "%POSSESSION_MSG2%" echo.
>> "%POSSESSION_MSG2%" echo Earlier work that existed only in the working copy. The transition benchmark requires an
>> "%POSSESSION_MSG2%" echo explicit list of reviewed event kinds and a non-empty reviewed time coverage, and matches
>> "%POSSESSION_MSG2%" echo events only inside the same reviewed window. A prediction-blind local reference editor can be
>> "%POSSESSION_MSG2%" echo built from a pinned external review pack, and an exported review is validated against the
>> "%POSSESSION_MSG2%" echo registered video, split and coverage. External fixtures only.
>> "%POSSESSION_MSG2%" echo.
>> "%POSSESSION_MSG2%" echo Co-Authored-By: Claude Fable 5.2 ^<noreply@anthropic.com^>
>> "%POSSESSION_MSG2%" echo Claude-Session: https://claude.ai/code/session_01XFbvRnLFWRaGyWGvKPjhiv
git commit -q -F "%POSSESSION_MSG2%"
if errorlevel 1 (echo Commit olusturulamadi. & pause & exit /b 1)
:push
git push origin feature/external-possession-selection
if errorlevel 1 (echo PUSH BASARISIZ & pause & exit /b 1)
echo.
for /f %%h in ('git rev-parse --short HEAD') do echo YUKLEME TAMAM. Commit: %%h
git diff HEAD --name-only
echo Yukaridaki satirlar bos ise izlenen dosyalarin hepsi GitHub ile ayni.
echo GitHub Actions sekmesinde testlerin sonucunu kontrol edin, sonra TESLIM-HAZIRLA.cmd calistirin.
pause
exit /b 0

:guard
git diff --cached --name-only -- "*.csv" "*.tsv" "*.xml" "*.jsonl" "*_atd.txt" "*.mp4" "*.mkv" "*.mov" "*.avi" "*.npy" "*.pkl" "*.pt" "*.pth" "*.onnx" "*.png" "*.jpg" "*.zip" "*.log" | findstr /r "." >nul
if not errorlevel 1 goto refuse
git diff --cached --name-only -- "*.npz" ":(exclude)models/possession-v2.npz" ":(exclude)models/possession-v23.npz" | findstr /r "." >nul
if not errorlevel 1 goto refuse
exit /b 0
:refuse
echo HATA: eklenecek dosyalar arasinda veri turu bir dosya var. Hicbir sey commit edilmedi.
git diff --cached --name-only
git reset -q
pause
exit /b 1
