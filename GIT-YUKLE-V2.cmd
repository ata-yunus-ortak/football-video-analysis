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
git add -- possession models/possession-v2.npz models/possession-v23.npz models/possession-tcn-v215.npz "tests/test_possession_*.py" tests/test_ball_patch_data.py "possession-*.json" experiments/possession_v2 tools/possession_clock.py tools/possession_deliver.py tools/possession_final_test.py tools/possession_place_files.py requirements-possession.txt requirements-possession-train.txt SAHIPLIK-V2-KURULUM.cmd SAHIPLIK-V2-URET.cmd SAHIPLIK-V24-URET.cmd SAHIPLIK-V25-URET.cmd SAHIPLIK-V29-URET.cmd SAHIPLIK-V211-URET.cmd SAAT-OKU.cmd TESLIM-HAZIRLA.cmd TESLIM-TEK-TIK.cmd SON-TEST.cmd GIT-YUKLE-V2.cmd TECHNICAL_DOCUMENT.md TECHNICAL_DOCUMENT_V2.md DATA_SOURCES.md README.md CLAUDE.md AGENTS.md TEAM_START_TR.md docs/SAHIPLIK_V2_TR.md docs/DENEY_KAYDI_TR.md .gitignore .gitattributes .github/workflows/tests.yml
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
> "%POSSESSION_MSG1%" echo Records K019-K020: v2.16 chain OK on the team computer; a fourth attempt with the second model failed its gates
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K020: a team member pushed eight newly trained network members on 16 Nov. The v2.15 plan and the documents had
>> "%POSSESSION_MSG1%" echo said that no further candidate with the second model would be registered; the team lead decided to make one more
>> "%POSSESSION_MSG1%" echo attempt, and the plan and the documents say so. Registered before any validation row, possession-v217-plan.json:
>> "%POSSESSION_MSG1%" echo the same seven gates and thresholds, against the release. On 16 new copies with the tactical camera spellF1
>> "%POSSESSION_MSG1%" echo 0.6704 to 0.6848, with a simulated second camera +0.0125 and +0.0050, copies of the other simulator +0.0110.
>> "%POSSESSION_MSG1%" echo Six gates passed; the gate on single copies failed, one copy 0.0182 lower, possession-v217-results.json.
>> "%POSSESSION_MSG1%" echo Not released: possession-v2.16 stays the release and no
>> "%POSSESSION_MSG1%" echo release file changed. Scripts and the prepared, unreleased integration are under experiments/possession_v2/v219.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K019: on 16 Nov the delivery chain ran end to end on the team lead computer with v2.16, every step OK. Its status
>> "%POSSESSION_MSG1%" echo line says that the v2.16 file has the same bytes as the v2.15 file of the day before: on the provided match the
>> "%POSSESSION_MSG1%" echo added-players step changed no label. The Form had been submitted on 15 Nov with those bytes.
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
