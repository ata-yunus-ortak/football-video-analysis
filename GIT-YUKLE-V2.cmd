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
> "%POSSESSION_MSG1%" echo Release possession-v2.16: lost players added from the broadcast tracking; records K015-K018
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K017: the submission system is now possession-v2.16 = v2.15 plus one step, possession/playerfill.py. When the
>> "%POSSESSION_MSG1%" echo broadcast files are present and the accuracy gate of the ball fill is open, a registered broadcast player with
>> "%POSSESSION_MSG1%" echo no tactical player of either team within 1.5 m is added to the tracking the models see. Tactical positions
>> "%POSSESSION_MSG1%" echo are never moved; without broadcast files or with the gate closed the output is that of v2.15.
>> "%POSSESSION_MSG1%" echo Registered before any validation row, possession-v216-plan.json: on 16 new copies with a simulated second
>> "%POSSESSION_MSG1%" echo camera spellF1 +0.0104, better on 13 copies and worse on 3, worst copy -0.0056; medium stream +0.0073,
>> "%POSSESSION_MSG1%" echo stream that loses and invents players +0.0044, copies of the other simulator +0.0004. All seven gates
>> "%POSSESSION_MSG1%" echo passed, the last one by a hair, possession-v216-results.json. The second camera is simulated and the
>> "%POSSESSION_MSG1%" echo provided broadcast tracking was not examined; the documents say so. The next step of the ladder is v2.15.
>> "%POSSESSION_MSG1%" echo Eleven synthetic variants give the same bytes under Python 3.10 with numpy 1.26.4 and Python 3.13 with numpy 2.5.3.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K016: asked by the team lead, whether the broadcast camera should take priority where it agrees with the
>> "%POSSESSION_MSG1%" echo tactical one. Simulated second camera on development copies, reporting only, possession-k016-camera-priority.json
>> "%POSSESSION_MSG1%" echo and experiments/possession_v2/v218: taking the ball or the players from the broadcast stream where both
>> "%POSSESSION_MSG1%" echo agree changed the score by -0.005 to +0.002, also with a stream five times as precise. Not adopted.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K015: asked by the team lead, whether a Smart Tagging set-piece tag without a dead-ball stretch of ours
>> "%POSSESSION_MSG1%" echo around it should force one. Simulated tags on the 42 development copies, reporting only, see
>> "%POSSESSION_MSG1%" echo possession-k015-tag-rescue.json and experiments/possession_v2/v217. The decision already has a dead-ball
>> "%POSSESSION_MSG1%" echo stretch before 93 per cent of the restarts and the published tag counts cover about half of them, so the
>> "%POSSESSION_MSG1%" echo ceiling is 0.003 and the rule gained about 0.001. Not registered.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K018: on 15 Nov the delivery chain ran end to end on the team lead computer with v2.15, every step OK,
>> "%POSSESSION_MSG1%" echo same bytes as recorded on Linux for the synthetic variants. v2.16 needs one more run of the chain there.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo Launchers: this script calls git without its pager and asks for no key when TESLIM-TEK-TIK.cmd starts it.
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
