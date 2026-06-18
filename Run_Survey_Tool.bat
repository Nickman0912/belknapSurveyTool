@echo off
title Camp Belknap Survey Extraction Tool
echo ==================================================
echo Starting Camp Belknap Survey Extraction Tool...
echo ==================================================
echo.
echo Installing requirements (if any updates)...
python -m pip install -r requirements.txt
echo.
echo Starting web app in your browser...
python -m streamlit run app.py
echo.
echo If the tool stopped or errored, details are shown above.
pause
