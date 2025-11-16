@echo off
CHCP 65001
echo Installing required packages...
py -m pip install -r requirements.txt
echo.
echo Running the game...
py src/main.py
pause
