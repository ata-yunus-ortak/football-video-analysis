@echo off
rem Commits the possession release (source, model bundles and network weights, plans, results, documents, tests, launchers, experiment scripts)
rem and, as a second commit, the external control-reference tooling that was only on this computer. Then pushes the branch.
rem Every path is named below; nothing else is added. Data file types are refused even if they were listed by mistake.
rem git is called with --no-pager: a long list must not stop the window at the pager. With POSSESSION_NO_PAUSE set
rem (TESLIM-TEK-TIK.cmd sets it) the script asks for no key unless something fails.
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
if not defined POSSESSION_NO_PAUSE pause >nul
:workflowok
git reset -q
git add -- possession models/possession-v2.npz models/possession-v23.npz models/possession-tcn-v215.npz "tests/test_possession_*.py" tests/test_ball_patch_data.py "possession-*.json" experiments/possession_v2 tools/possession_clock.py tools/possession_deliver.py tools/possession_final_test.py tools/possession_place_files.py requirements-possession.txt requirements-possession-train.txt SAHIPLIK-V2-KURULUM.cmd SAHIPLIK-V2-URET.cmd SAHIPLIK-V24-URET.cmd SAHIPLIK-V25-URET.cmd SAHIPLIK-V29-URET.cmd SAHIPLIK-V211-URET.cmd SAAT-OKU.cmd TESLIM-HAZIRLA.cmd TESLIM-TEK-TIK.cmd SON-TEST.cmd GIT-YUKLE-V2.cmd TECHNICAL_DOCUMENT.md TECHNICAL_DOCUMENT_V2.md REMEDIATION.md DATA_SOURCES.md README.md CLAUDE.md AGENTS.md TEAM_START_TR.md docs/SAHIPLIK_V2_TR.md docs/DENEY_KAYDI_TR.md .gitignore .gitattributes .github/workflows/tests.yml
if errorlevel 1 (echo git add basarisiz. & pause & exit /b 1)
call :guard
if errorlevel 1 exit /b 1
git diff --cached --quiet
if not errorlevel 1 goto second
echo.
echo ===== 1. commit: sahiplik surumu =====
git --no-pager diff --cached --stat
echo.
echo Listede .csv, .xml, .mp4, data/ veya FootballPrivate OLMAMALI.
echo Devam etmek icin bir tusa basin; iptal icin bu pencereyi kapatin.
if not defined POSSESSION_NO_PAUSE pause >nul
set "POSSESSION_MSG1=%TEMP%\possession_msg1.txt"
> "%POSSESSION_MSG1%" echo Record K021: chain OK on cc62a5f; process disclosure of the delivered document extended, documents only
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K021: on 16 Nov 23:31 the delivery chain ran end to end on the team lead computer on commit cc62a5f, every step OK.
>> "%POSSESSION_MSG1%" echo The file has the same bytes as the one already delivered, also on a second run and from a fresh clone.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo Documents only since then, at the team lead request. Section 6 of TECHNICAL_DOCUMENT.md now has the four items the
>> "%POSSESSION_MSG1%" echo organisers asked for in their reply of 3 Nov: the rules snapshot the team worked from in October, what happened,
>> "%POSSESSION_MSG1%" echo the affected stages and how the selection was re-done. It also says what that reply answered and what was done for
>> "%POSSESSION_MSG1%" echo each of its conditions. One sentence of TECHNICAL_DOCUMENT_V2.md Section 2 is corrected: the team worked from its old
>> "%POSSESSION_MSG1%" echo copy of RULES.md until the end of October. REMEDIATION.md records a statement of the team lead of 16 Nov about the
>> "%POSSESSION_MSG1%" echo provider side as his statement. Its earlier entries are unchanged. No code, model or release file changed.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo No provided match data and no frame-level output are in the repository.
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
git --no-pager diff --cached --stat
echo Devam etmek icin bir tusa basin; iptal icin bu pencereyi kapatin.
if not defined POSSESSION_NO_PAUSE pause >nul
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
git --no-pager diff HEAD --name-only
echo Yukaridaki satirlar bos ise izlenen dosyalarin hepsi GitHub ile ayni.
echo GitHub Actions sekmesinde testlerin sonucunu kontrol edin, sonra TESLIM-HAZIRLA.cmd calistirin.
if not defined POSSESSION_NO_PAUSE pause
exit /b 0

:guard
git diff --cached --name-only -- "*.csv" "*.tsv" "*.xml" "*.jsonl" "*_atd.txt" "*.mp4" "*.mkv" "*.mov" "*.avi" "*.npy" "*.pkl" "*.pt" "*.pth" "*.onnx" "*.png" "*.jpg" "*.zip" "*.log" | findstr /r "." >nul
if not errorlevel 1 goto refuse
git diff --cached --name-only -- "*.npz" ":(exclude)models/possession-v2.npz" ":(exclude)models/possession-v23.npz" ":(exclude)models/possession-tcn-v215.npz" | findstr /r "." >nul
if not errorlevel 1 goto refuse
exit /b 0
:refuse
echo HATA: eklenecek dosyalar arasinda veri turu bir dosya var. Hicbir sey commit edilmedi.
git --no-pager diff --cached --name-only
git reset -q
pause
exit /b 1
