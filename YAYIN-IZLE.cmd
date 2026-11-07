@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "%~dp0viewer-local.cmd" call "%~dp0viewer-local.cmd"
if not defined MTAH_DATA_DIR set "MTAH_DATA_DIR=%USERPROFILE%\FootballPrivate\mtah2027\bundle"
if not defined MTAH_BROADCAST_VIDEO set "MTAH_BROADCAST_VIDEO=%USERPROFILE%\Downloads\BAR-ATH_broadcast.mp4"
if not exist "%MTAH_DATA_DIR%\broadcast\BAR-ATH_broadcast_atd.xml" goto missing
if not exist "%MTAH_DATA_DIR%\broadcast\BAR-ATH_broadcast_atd.txt" goto missing
if not exist "%MTAH_DATA_DIR%\broadcast\BAR-ATH_broadcast_homography.csv" goto missing
if not exist "%MTAH_BROADCAST_VIDEO%" goto missing
echo Yayin videosu kendi ATD ve homografi verisiyle aciliyor. Bu pencereyi acik birakin.
python -m tools.tracking_viewer --meta "%MTAH_DATA_DIR%\broadcast\BAR-ATH_broadcast_atd.xml" --tracking "%MTAH_DATA_DIR%\broadcast\BAR-ATH_broadcast_atd.txt" --homography "%MTAH_DATA_DIR%\broadcast\BAR-ATH_broadcast_homography.csv" --video "%MTAH_BROADCAST_VIDEO%" --source-name "Yayin / broadcast" --port 8767 --open
if errorlevel 1 pause
exit /b
:missing
echo Yayin dosyalarindan biri bulunamadi. viewer-local.cmd icinde MTAH_DATA_DIR ve MTAH_BROADCAST_VIDEO yollarini ayarlayin.
pause
exit /b 1
