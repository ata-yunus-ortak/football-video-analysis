@echo off
rem Final test of the frozen possession release on the reserved external match (public DFL data, CC BY 4.0).
rem Registered in possession-final-test-plan.json. It is run once: downloads about 420 MB, then runs for about an hour.
rem Nothing about the provided match is read. The printed numbers and possession-final-test-results.json may be shared.
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv-possession\Scripts\python.exe" (
  echo .venv-possession ortami yok. Once TESLIM-HAZIRLA.cmd ya da SAHIPLIK-V2-KURULUM.cmd calistirin.
  pause
  exit /b 1
)
if exist "possession-final-test-results.json" (
  echo Son test daha once calistirilmis: possession-final-test-results.json var. Bir kez calistirilir.
  pause
  exit /b 1
)
set "OUT=%USERPROFILE%\FootballPrivate\possession-final-test"
echo Ayrilmis dis mac (DFL J03WMX) indirilecek ve dondurulmus surum bir kez sinanacak.
echo Yaklasik 420 MB indirme ve yaklasik bir saat calisma. Yarida kesilirse ayni komut kaldigi yerden surer.
echo Devam etmek icin bir tusa basin; iptal icin pencereyi kapatin.
pause >nul
".venv-possession\Scripts\python.exe" -m tools.possession_final_test --out "%OUT%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo SON TEST TAMAM. Yukaridaki satirlar ve possession-final-test-results.json paylasilabilir: kamuya acik dis veri.
  echo Sonuc dosyasini GitHub'a gondermek icin GIT-YUKLE-V2.cmd calistirin.
) else (
  echo SON TEST TAMAMLANMADI. Yukaridaki hata satirlarini iletin. Ayni komut kaldigi yerden surer.
)
pause
exit /b %RC%
