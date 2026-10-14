@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Media Organizer 一键安装
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0安装并启动.ps1"
if errorlevel 1 (
  echo.
  echo 安装没有完成，请保留此窗口并查看上方提示。
  pause
)
