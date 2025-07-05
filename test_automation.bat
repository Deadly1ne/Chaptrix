@echo off
echo Running Chaptrix Automation Test...
echo.

python test_automation.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Test completed successfully!
    echo Your setup is ready for automation.
) else (
    echo.
    echo Test failed with errors.
    echo Please check the logs above and fix any issues before setting up automation.
)

echo.
echo Press any key to exit...
pause > nul