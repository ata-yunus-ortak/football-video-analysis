@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m tools.tracking_viewer --demo --port 8766 --open
if errorlevel 1 pause
