@echo off
rem Possession v2: one-time environment + synthetic tests. Touches no match data.
setlocal
cd /d "%~dp0"
set "PYV="
for %%v in (3.10 3.11 3.12) do (
  if not defined PYV (
    py -%%v -c "import sys" >nul 2>&1 && set "PYV=%%v"
  )
)
if not defined PYV (
  echo Python 3.10, 3.11 veya 3.12 bulunamadi. python.org'dan Python 3.10 kurup tekrar deneyin.
  pause
  exit /b 1
)
echo Python %PYV% kullaniliyor.
if not exist ".venv-possession\Scripts\python.exe" (
  py -%PYV% -m venv .venv-possession
  if errorlevel 1 (echo Sanal ortam olusturulamadi. & pause & exit /b 1)
)
".venv-possession\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-possession.txt
if errorlevel 1 (echo KURULUM HATASI & pause & exit /b 1)
".venv-possession\Scripts\python.exe" -m unittest tests.test_possession_v2 tests.test_possession_v23 tests.test_possession_v24 tests.test_possession_v25 tests.test_possession_v26 tests.test_possession_v27 tests.test_possession_plausibility tests.test_possession_v25c tests.test_possession_v29 tests.test_possession_v211 tests.test_possession_public_check tests.test_possession_release tests.test_possession_reader_reference tests.test_possession_inputs_check -v
if errorlevel 1 (echo. & echo TESTLER BASARISIZ & pause & exit /b 1)
echo.
echo KURULUM VE TESTLER TAMAM. Teslim dosyasi icin TESLIM-HAZIRLA.cmd calistirin (ortam, saat okuma, uretim ve kontroller tek adimda).
pause
