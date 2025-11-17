@echo off
echo =======================================
echo  Staging all changes...
echo =======================================
git add .

echo.
echo =======================================
echo  Committing changes...
echo =======================================
git commit

echo.
echo =======================================
echo  Pushing to remote...
echo =======================================
git push

echo.
echo =======================================
echo  Push complete.
echo =======================================
pause
