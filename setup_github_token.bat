@echo off
setlocal

echo This script will help you set up your GitHub Personal Access Token as an environment variable.
echo.
echo IMPORTANT: Your token will be stored in your Windows environment variables.
echo This means it will persist between sessions but is visible to anyone with access to your computer.
echo.

:: Check if GITHUB_TOKEN is already set as an environment variable
set "_GITHUB_TOKEN_CHECK=%GITHUB_TOKEN%"
if defined _GITHUB_TOKEN_CHECK (
    echo GITHUB_TOKEN is already set.
    echo Current value (first 5 chars): %_GITHUB_TOKEN_CHECK:~0,5%.....
    set /p OVERWRITE="Do you want to overwrite it? (y/n): "
    if /i "%OVERWRITE%" neq "y" (
        echo Aborting. GITHUB_TOKEN not changed.
        goto :eof
    )
)

:: Prompt the user to enter their GitHub Personal Access Token
set /p GITHUB_TOKEN="Please enter your GitHub Personal Access Token: "

if "%GITHUB_TOKEN%"=="" (
    echo No token provided. Exiting.
    pause
    exit /b 1
)

echo.
echo Setting GITHUB_TOKEN as a user environment variable...

:: Set the token as a user environment variable (persists between sessions)
setx GITHUB_TOKEN "%GITHUB_TOKEN%"

echo.
echo Token has been set successfully!
echo You will need to restart any open command prompts for the change to take effect.
echo.
echo You can now use the push_to_github.bat and push_to_github_custom.bat scripts without
echo entering your token each time.

:: Clear the variable from the current session for security
set GITHUB_TOKEN=

pause
endlocal