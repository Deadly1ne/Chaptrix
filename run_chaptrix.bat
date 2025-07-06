@echo off
setlocal enabledelayedexpansion

echo ========================================
echo           Chaptrix Launcher
echo ========================================
echo.

if "%1"=="" (
    echo Usage: run_chaptrix.bat [command]
    echo.
    echo Available commands:
    echo   check      - Check for new chapters
    echo   dashboard  - Start Streamlit dashboard
    echo   unified    - Run unified workflow
    echo   test       - Run automation tests
    echo   install    - Install/update requirements
    echo.
    echo Example: run_chaptrix.bat check
    echo.
    pause
    exit /b 1
)

set COMMAND=%1

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo Checking requirements...
if "%COMMAND%"=="dashboard" (
    pip show streamlit >nul 2>&1
    if !errorlevel! neq 0 (
        echo Streamlit not found. Installing requirements...
        pip install -r requirements.txt
    )
) else (
    pip show requests >nul 2>&1
    if !errorlevel! neq 0 (
        echo Requirements not found. Installing...
        pip install -r requirements.txt
    )
)

echo.
echo Running Chaptrix with command: %COMMAND%
echo.

if "%COMMAND%"=="check" (
    echo Running Chaptrix Check for new chapters...
    python main.py --check
    echo.
    echo Check completed.
) else if "%COMMAND%"=="dashboard" (
    echo Starting Chaptrix Dashboard...
    echo Opening Chaptrix Dashboard in your browser...
    streamlit run main.py
) else if "%COMMAND%"=="unified" (
    echo Running Unified Workflow...
    python unified_workflow.py
    echo.
    echo Unified workflow completed.
) else if "%COMMAND%"=="test" (
    echo Running Automation Test...
    python test_automation.py
    if !errorlevel! equ 0 (
        echo.
        echo Test completed successfully!
        echo Your setup is ready for automation.
    ) else (
        echo.
        echo Test failed with errors.
        echo Please check the logs above and fix any issues.
    )
) else if "%COMMAND%"=="install" (
    echo Installing/updating requirements...
    pip install -r requirements.txt --upgrade
    echo.
    echo Requirements updated.
) else (
    echo ERROR: Unknown command '%COMMAND%'
    echo Run 'run_chaptrix.bat' without arguments to see available commands.
    pause
    exit /b 1
)

echo.
echo Press any key to exit...
pause > nul