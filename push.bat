@echo off
echo.
echo =======================================
echo  GitHub Push Utility
echo =======================================
echo.

set /p commit_message="Enter commit message: "

if "%commit_message%"=="" (
    echo.
    echo Commit message cannot be empty. Aborting.
    goto end
)

echo.
echo Staging all files...
git add .
echo.

echo Committing changes...
git commit -m "%commit_message%"
echo.

echo Pushing to GitHub...
git push origin master
echo.

echo =======================================
echo  Push complete.
echo =======================================
echo.

:end
pause
