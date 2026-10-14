@echo off
cd /d "%~dp0"
set "BUNDLED_PYTHONW=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
if exist "%BUNDLED_PYTHONW%" (
  start "" "%BUNDLED_PYTHONW%" "%~dp0launch_media_organizer_safe_drag_v53.pyw"
  exit /b
)
where pyw >nul 2>nul
if not errorlevel 1 (
  start "" pyw "%~dp0launch_media_organizer_safe_drag_v53.pyw"
  exit /b
)
where pythonw >nul 2>nul
if not errorlevel 1 (
  start "" pythonw "%~dp0launch_media_organizer_safe_drag_v53.pyw"
  exit /b
)
echo 未检测到 Python，正在打开一键安装程序……
call "%~dp0一键安装并启动.cmd"
