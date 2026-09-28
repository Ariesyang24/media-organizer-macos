@echo off
cd /d "%~dp0"
set "BUNDLED_PYTHONW=C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
if exist "%BUNDLED_PYTHONW%" (
  start "" "%BUNDLED_PYTHONW%" "%~dp0launch_media_organizer_scene_optional.pyw"
  exit /b
)
where pyw >nul 2>nul
if not errorlevel 1 (
  start "" pyw "%~dp0launch_media_organizer_scene_optional.pyw"
  exit /b
)
start "" pythonw "%~dp0launch_media_organizer_scene_optional.pyw"
