@echo off
title AI4Kids.pk Dashboard
cd /d "%~dp0"
echo Starting AI4Kids.pk Dashboard...
python -m streamlit run "ai4kids_school.py"
if errorlevel 1 (
    echo.
    echo Something went wrong starting the dashboard.
    pause
)
