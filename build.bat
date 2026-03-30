@echo off
echo Building Leramot...
pyinstaller --onefile --noconsole --name Leramot --add-data "assets;assets" main.py
echo.
echo Done! Check dist\Leramot.exe
pause
