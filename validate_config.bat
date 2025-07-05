@echo off
echo Chaptrix Configuration Validator
echo ===============================
echo.

python config_validator.py

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo Configuration validation found issues. Please fix them before running Chaptrix.
    pause
    exit /b 1
) ELSE (
    echo.
    echo Configuration is valid! You can now run Chaptrix.
    pause
)