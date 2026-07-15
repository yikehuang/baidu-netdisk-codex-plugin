@echo off
setlocal

where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0server.py"
  exit /b %errorlevel%
)

where python >nul 2>nul
if not errorlevel 1 (
  python "%~dp0server.py"
  exit /b %errorlevel%
)

echo Python 3 was not found. Install Python 3.10 or newer and try again. 1>&2
exit /b 1
