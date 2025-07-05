@echo off
echo Running Chaptrix Check for new chapters...
echo.
echo If this is your first time running Chaptrix, make sure you have installed the requirements:
echo pip install -r requirements.txt
echo.
pip show requests >nul 2>&1
if %errorlevel% neq 0 (
    echo Requirements not found. Installing...
    pip install -r requirements.txt
)
echo.
python main.py --check
echo.
echo Check completed.
pause