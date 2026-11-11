@echo off
rem Possession release: the whole local delivery chain in one window (tools/possession_deliver.py).
rem Environment, synthetic tests, generation, format and plausibility checks, clock reading, repeat run,
rem fresh-clone regeneration, organisers' validator, copy to FootballPrivate\teslim. Runs only on this computer.
rem The window shows status words only; program output goes to a private log that must not be shared.
rem Options are passed on, for example:  TESLIM-HAZIRLA.cmd --quick   or   TESLIM-HAZIRLA.cmd --no-ocr
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if exist "%~dp0viewer-local.cmd" call "%~dp0viewer-local.cmd"
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
py -%PYV% -m tools.possession_deliver %*
set "RC=%ERRORLEVEL%"
echo.
echo Paylasilabilir: yalnizca yukaridaki [..] satirlari ve SONUC satiri.
echo Paylasilmaz: log, run.json, OZEL-kayit.json, CSV ve belgenin sonundaki calisma kaydi.
pause
exit /b %RC%
