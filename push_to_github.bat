@echo off
setlocal

echo Pushing changes to GitHub...

:: Check if GITHUB_TOKEN environment variable exists
if "%GITHUB_TOKEN%"=="" (
    echo GITHUB_TOKEN environment variable not found.
    echo Please set your GitHub Personal Access Token as an environment variable:
    echo.
    echo     set GITHUB_TOKEN=your_personal_access_token_here
    echo.
    echo Or enter your token now (it will not be saved):
    set /p GITHUB_TOKEN=Enter GitHub token: 
    
    if "%GITHUB_TOKEN%"=="" (
        echo No token provided. Exiting.
        pause
        exit /b 1
    )
)

:: Configure git to use the token for this push
git add .
git commit -m "Update code with latest changes"

:: Use the token for authentication
echo Pushing with token authentication...

:: Use git credential helper to temporarily store the credentials
git -c credential.helper="!f() { echo username=x-access-token; echo password=%GITHUB_TOKEN%; }; f" push origin main

echo.
echo Done!
pause
endlocal