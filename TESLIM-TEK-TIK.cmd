@echo off
rem One double-click for the whole delivery, on the team lead's computer only:
rem   1. tools/possession_place_files.py puts the files the organisers shipped (videos, Smart Tagging, tracking)
rem      into the bundle folder: a local copy that never replaces a file already there,
rem   2. GIT-YUKLE-V2.cmd commits and pushes the release (started from here it asks for no key unless something fails),
rem   3. tools/possession_deliver.py runs the whole delivery chain, as TESLIM-HAZIRLA.cmd, with the team name,
rem   4. the shareable status lines of steps 1 and 3 are copied to Desktop\logs (names and status words only).
rem Nothing here sends a match file anywhere; the files are read only by the release, on this computer.
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if exist "%~dp0viewer-local.cmd" call "%~dp0viewer-local.cmd"
set "LOGS=%USERPROFILE%\Desktop\logs"
if not exist "%LOGS%" mkdir "%LOGS%"
set "PRIV=%MTAH_PRIVATE_DIR%"
if not defined PRIV set "PRIV=%USERPROFILE%\FootballPrivate"
set "PYV="
for %%v in (3.10 3.11 3.12) do (
  if not defined PYV (
    py -%%v -c "import sys" >nul 2>&1 && set "PYV=%%v"
  )
)
if not defined PYV (
  echo Python 3.10, 3.11 veya 3.12 bulunamadi. python.org adresinden Python 3.10 kurup tekrar deneyin.
  pause
  exit /b 1
)
echo.
echo Bu pencere bir-iki saat acik kalabilir. Bilgisayari kapatmayin ve uyku moduna almayin.
echo Bir sorun olmazsa hicbir tusa basmaniz gerekmez. Ekranda "bir tusa basin" yazarsa bir tusa basin.
echo.
echo ===== 1/3 Mac dosyalari paket klasorune yerlestiriliyor =====
py -%PYV% -m tools.possession_place_files --status-file "%LOGS%\DOSYA-durum.txt"
if errorlevel 2 goto placed
if errorlevel 1 (
  echo.
  echo Zorunlu bir dosya bulunamadi. Yukaridaki BULUNAMADI satirlarina bakin.
  echo Organizatorun indirme baglantisindaki paketi Downloads klasorune indirip bu dosyayi tekrar calistirin.
  pause
  exit /b 1
)
:placed
echo.
echo ===== 2/3 GitHub'a yukleniyor =====
set "POSSESSION_NO_PAUSE=1"
call "%~dp0GIT-YUKLE-V2.cmd"
if errorlevel 1 (
  echo.
  echo Yukleme tamamlanmadi. Ekrandaki son satirlari Claude'a yazin.
  pause
  exit /b 1
)
echo.
echo ===== 3/3 Teslim zinciri: uzun surer =====
py -%PYV% -m tools.possession_deliver --team LittleSickle
set "RC=%ERRORLEVEL%"
if exist "%PRIV%\teslim\PAYLASILABILIR-durum.txt" copy /y "%PRIV%\teslim\PAYLASILABILIR-durum.txt" "%LOGS%\PAYLASILABILIR-durum.txt" >nul
echo.
echo BITTI. Claude'a "bitti" yazin; sonucu o kontrol edecek.
echo Paylasilabilir satirlar Masaustu\logs klasorune de kopyalandi.
pause
exit /b %RC%
