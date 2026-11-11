@echo off
rem Possession: automatic clock readings of both videos (separate OCR environment). Never upload the videos.
rem TESLIM-HAZIRLA.cmd runs this step by itself; this launcher is kept for running it alone.
rem Frames are read in memory only; nothing is saved except the clock observations (outside the repository).
chcp 65001 >nul
cd /d "%~dp0"
if exist "%~dp0viewer-local.cmd" call "%~dp0viewer-local.cmd"
if not defined MTAH_DATA_DIR set "MTAH_DATA_DIR=%USERPROFILE%\FootballPrivate\mtah2027\bundle"
set "TV=%MTAH_DATA_DIR%\tactical\BAR-ATH_tactical.mp4"
set "BV=%MTAH_DATA_DIR%\broadcast\BAR-ATH_broadcast.mp4"
if not exist "%TV%" (echo Taktik video bulunamadi: %TV% & pause & exit /b 1)
if not exist "%BV%" (echo Yayin videosu bulunamadi: %BV% & pause & exit /b 1)
if not exist ".venv-sync\Scripts\python.exe" (
  py -3.10 -m venv .venv-sync
  if errorlevel 1 (echo Python 3.10 gerekli. & pause & exit /b 1)
  ".venv-sync\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-sync-lock.txt
  if errorlevel 1 (echo OCR ORTAMI KURULAMADI & pause & exit /b 1)
)
set "CLK=%USERPROFILE%\FootballPrivate\possession-clock"
if exist "%CLK%\tactical\summary.json" if exist "%CLK%\broadcast\summary.json" (
  echo Saat okumalari zaten var: %CLK%
  pause
  exit /b 0
)
if exist "%CLK%" (
  echo %CLK% yarim kalmis gorunuyor. Klasoru silip tekrar calistirin.
  pause
  exit /b 1
)
echo Taktik video okunuyor...
".venv-sync\Scripts\python.exe" -m tools.possession_clock --video "%TV%" --out "%CLK%\tactical"
if errorlevel 1 (echo TAKTIK SAAT OKUMASI BASARISIZ & pause & exit /b 1)
echo Yayin videosu okunuyor...
".venv-sync\Scripts\python.exe" -m tools.possession_clock --video "%BV%" --out "%CLK%\broadcast"
if errorlevel 1 (echo YAYIN SAAT OKUMASI BASARISIZ & pause & exit /b 1)
echo.
echo SAAT OKUMA TAMAM: %CLK%
echo Simdi TESLIM-HAZIRLA.cmd calistirilabilir (okunan saatleri kendisi bulur).
pause
