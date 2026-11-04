@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Tracking ve video oynaticisi baslatiliyor. Bu pencereyi acik birakin.
python -m tools.tracking_viewer --meta "C:\Users\Abra\FootballPrivate\mtah2027\bundle\tactical\BAR-ATH_tactical_atd.xml" --tracking "C:\Users\Abra\FootballPrivate\mtah2027\bundle\tactical\BAR-ATH_tactical_atd.txt" --video "C:\Users\Abra\Downloads\BAR-ATH_tactical.mp4" --smart-tagging "C:\Users\Abra\FootballPrivate\mtah2027\bundle\tactical\BAR-ATH_tactical_smart_tagging.xml" --open
if errorlevel 1 pause
