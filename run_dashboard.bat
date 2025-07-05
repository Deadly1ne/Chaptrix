@echo off
echo Starting Chaptrix Dashboard...
echo.
echo If this is your first time running Chaptrix, make sure you have installed the requirements:
echo pip install -r requirements.txt
echo.
pip show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo Streamlit not found. Installing requirements...
    pip install -r requirements.txt
)
echo.
echo Opening Chaptrix Dashboard in your browser...
streamlit run main.py
pause