@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "%~dp0viewer-local.cmd" call "%~dp0viewer-local.cmd"
if not defined MTAH_DATA_DIR set "MTAH_DATA_DIR=%USERPROFILE%\FootballPrivate\mtah2027\bundle"
if not defined MTAH_VIDEO set "MTAH_VIDEO=%USERPROFILE%\Downloads\BAR-ATH_tactical.mp4"
if not exist "%MTAH_DATA_DIR%\tactical\BAR-ATH_tactical_atd.xml" (
  echo Metadata bulunamadi. viewer-local.example.cmd dosyasini viewer-local.cmd olarak kopyalayip veri yolunu ayarlayin.
  echo Veriniz yoksa TRACKING-DEMO.cmd dosyasini calistirabilirsiniz.
  pause
  exit /b 1
)
echo Yerel tracking oynaticisi baslatiliyor. Bu pencereyi acik birakin.
if exist "%MTAH_VIDEO%" (
  python -m tools.tracking_viewer --meta "%MTAH_DATA_DIR%\tactical\BAR-ATH_tactical_atd.xml" --tracking "%MTAH_DATA_DIR%\tactical\BAR-ATH_tactical_atd.txt" --video "%MTAH_VIDEO%" --smart-tagging "%MTAH_DATA_DIR%\tactical\BAR-ATH_tactical_smart_tagging.xml" --open
) else (
  python -m tools.tracking_viewer --meta "%MTAH_DATA_DIR%\tactical\BAR-ATH_tactical_atd.xml" --tracking "%MTAH_DATA_DIR%\tactical\BAR-ATH_tactical_atd.txt" --smart-tagging "%MTAH_DATA_DIR%\tactical\BAR-ATH_tactical_smart_tagging.xml" --open
)
if errorlevel 1 pause
