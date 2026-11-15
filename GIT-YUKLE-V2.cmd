@echo off
rem Commits the possession release (source, model bundles and network weights, plans, results, documents, tests, launchers, experiment scripts)
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
git add -- possession models/possession-v2.npz models/possession-v23.npz models/possession-tcn-v215.npz "tests/test_possession_*.py" tests/test_ball_patch_data.py "possession-*.json" experiments/possession_v2 tools/possession_clock.py tools/possession_deliver.py tools/possession_final_test.py tools/possession_place_files.py requirements-possession.txt requirements-possession-train.txt SAHIPLIK-V2-KURULUM.cmd SAHIPLIK-V2-URET.cmd SAHIPLIK-V24-URET.cmd SAHIPLIK-V25-URET.cmd SAHIPLIK-V29-URET.cmd SAHIPLIK-V211-URET.cmd SAAT-OKU.cmd TESLIM-HAZIRLA.cmd TESLIM-TEK-TIK.cmd SON-TEST.cmd GIT-YUKLE-V2.cmd TECHNICAL_DOCUMENT.md TECHNICAL_DOCUMENT_V2.md DATA_SOURCES.md README.md CLAUDE.md AGENTS.md TEAM_START_TR.md docs/SAHIPLIK_V2_TR.md docs/DENEY_KAYDI_TR.md .gitignore .gitattributes .github/workflows/tests.yml
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
> "%POSSESSION_MSG1%" echo Release possession-v2.15 (second model pooled with the v2 models); records K007-K014
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K013: the submission system is now possession-v2.15 = v2.11k plus a second model family on the core
>> "%POSSESSION_MSG1%" echo model path. The second-stage probabilities of the tree models are averaged with those of a temporal
>> "%POSSESSION_MSG1%" echo convolution network, weight 0.2 for the network, and decoded by the unchanged v2 decoder, see
>> "%POSSESSION_MSG1%" echo possession/pooling.py, possession/tcn and models/possession-tcn-v215.npz. The network was designed
>> "%POSSESSION_MSG1%" echo by a team member, branch mtah-possession, commit 167dc7b; its weights were trained by us on the six
>> "%POSSESSION_MSG1%" echo open DFL matches with both corruption simulators, experiments/possession_v2/v214/tcn_jax.py.
>> "%POSSESSION_MSG1%" echo Registered before any new result, possession-v215-plan.json: on 16 new copies spellF1 +0.0112,
>> "%POSSESSION_MSG1%" echo better on 14 copies and worse on 0, all seven gates passed, possession-v215-results.json.
>> "%POSSESSION_MSG1%" echo It is the third attempt with the same gates and the documents say so. Nothing is pooled on the
>> "%POSSESSION_MSG1%" echo noisier v2.3 path. The next step of the technical ladder is v2.11k.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K014: error-pattern study of v2.15 on 42 external development copies, reporting only, see
>> "%POSSESSION_MSG1%" echo possession-k014-error-patterns.json and experiments/possession_v2/v216. Possessions under 2 s carry
>> "%POSSESSION_MSG1%" echo 38 per cent of the lost score and are not visible to either model family; 29 per cent is the timing
>> "%POSSESSION_MSG1%" echo of possessions that are found. Rules built on these patterns changed the score by at most 0.003,
>> "%POSSESSION_MSG1%" echo a learned combination of both families was explored and not registered. The release is unchanged.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo TESLIM-TEK-TIK.cmd: one double-click for the delivery on the team lead computer.
>> "%POSSESSION_MSG1%" echo tools/possession_place_files.py copies the files the organisers shipped from where a download put
>> "%POSSESSION_MSG1%" echo them into the bundle folder, on that computer only; then this script and the delivery chain run, and
>> "%POSSESSION_MSG1%" echo the shareable status lines are also copied to Desktop logs. Tests: tests/test_possession_place_files.py,
>> "%POSSESSION_MSG1%" echo synthetic folders only.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K012: candidate possession-v2.14, the same pooled system with equal weights: +0.0201 on 16 new
>> "%POSSESSION_MSG1%" echo copies and better on 15, but one copy was 0.016 worse, so the gate on single copies failed and it
>> "%POSSESSION_MSG1%" echo is not released, see possession-v214-plan.json and possession-v214-results.json.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K011: possession-v2.11k = v2.11g plus one rule (possession/kickoff.py):
>> "%POSSESSION_MSG1%" echo in a graded block, the frames before the first automatic Smart Tagging Kick Off (Start) tag are
>> "%POSSESSION_MSG1%" echo written D if that tag starts less than ten minutes after the block begins. Without a usable tag the
>> "%POSSESSION_MSG1%" echo output is that of v2.11g. No step of possession-release.json uses the kick-off frame published in
>> "%POSSESSION_MSG1%" echo FAQ.md any more: the organisers answer of 12 Nov did not allow that constant explicitly.
>> "%POSSESSION_MSG1%" echo possession.run211 stays frozen and unused. The rule is taken unchanged from commit 4b32747 of branch
>> "%POSSESSION_MSG1%" echo mtah-possession. It cannot be measured on external matches; its tests are synthetic and the chain was
>> "%POSSESSION_MSG1%" echo rehearsed on a synthetic bundle (possession-v211k-rehearsal.json). The delivery chain now reports
>> "%POSSESSION_MSG1%" echo whether the Smart Tagging file is present, the input check compares the number of kick-off tags with
>> "%POSSESSION_MSG1%" echo DATA.md (28 checks), and the final-test plan was re-registered for v2.11k and stays there.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K010: candidate possession-v2.13, the release probabilities averaged with the temporal convolution
>> "%POSSESSION_MSG1%" echo network of a team member (his fusion rule unchanged), was registered before any score, see
>> "%POSSESSION_MSG1%" echo possession-v213-plan.json, and validated on 16 new copies. Tactical camera only: spellF1
>> "%POSSESSION_MSG1%" echo -0.0045 on DFL, +0.0172 on Metrica, worst copy -0.0295. 3 of six gates failed (G1, G2, G4),
>> "%POSSESSION_MSG1%" echo so it is not released (possession-v213-results.json).
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K007: diagnosis on used validation copies, reporting only: 74%% of the possessions shorter than 2 s
>> "%POSSESSION_MSG1%" echo are missed and there is no systematic lag (possession-k007-diagnosis.json).
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K008: candidate possession-v2.12 (possession/touch.py, ball-touch and control-change columns for the
>> "%POSSESSION_MSG1%" echo core models): spellF1 +0.0125 on DFL, -0.008 on Metrica; four of six registered gates failed, so it
>> "%POSSESSION_MSG1%" echo is not released. Unused integration code is kept under
>> "%POSSESSION_MSG1%" echo experiments/possession_v2/v212/integration_not_released.
>> "%POSSESSION_MSG1%" echo.
>> "%POSSESSION_MSG1%" echo K009: the frozen v2.11 was watched on one external PFF FC World Cup 2022 game, inspection only, see
>> "%POSSESSION_MSG1%" echo experiments/possession_v2/pff_viewer. That data has no published licence and is not in the
>> "%POSSESSION_MSG1%" echo repository; nothing was selected or tuned on it.
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
git diff --cached --name-only -- "*.npz" ":(exclude)models/possession-v2.npz" ":(exclude)models/possession-v23.npz" ":(exclude)models/possession-tcn-v215.npz" | findstr /r "." >nul
if not errorlevel 1 goto refuse
exit /b 0
:refuse
echo HATA: eklenecek dosyalar arasinda veri turu bir dosya var. Hicbir sey commit edilmedi.
git diff --cached --name-only
git reset -q
pause
exit /b 1
