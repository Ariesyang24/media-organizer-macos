@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Please install Python 3.12 64-bit first, then run this file again.
  pause
  exit /b 1
)
py -3.12 -m pip install --upgrade pip
py -3.12 -m pip install -r "%~dp0requirements-windows.txt"
if errorlevel 1 (
  echo Installation failed. Check the network and try again.
  pause
  exit /b 1
)
echo Installation completed. You can now run the media organizer.
pause
