@echo off
echo Chaptrix Stitcher Tests
echo =====================

python test_stitcher.py

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo Tests failed. Check the logs for details.
    exit /b 1
) ELSE (
    echo.
    echo All tests passed successfully!
)