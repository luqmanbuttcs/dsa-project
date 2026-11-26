@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title Klondike Solitaire - CSC200 DSA Edition

where py >nul 2>nul
if not errorlevel 1 (
    py -3 tools\launch_game.py %*
    set "LAUNCH_EXIT=!ERRORLEVEL!"
) else (
    where python >nul 2>nul
    if errorlevel 1 goto :no_python
    python tools\launch_game.py %*
    set "LAUNCH_EXIT=!ERRORLEVEL!"
)

if not "!LAUNCH_EXIT!"=="0" goto :launch_failed
exit /b 0

:no_python
echo.
echo Python 3.12 or newer was not found.
echo Install Python from https://www.python.org/downloads/ and enable the Python launcher or PATH option.
echo Then double-click PLAY_SOLITAIRE.bat again.
echo.
pause
exit /b 2

:launch_failed
echo.
echo Solitaire could not start. Read the message above, fix the reported issue, and try again.
echo.
pause
exit /b !LAUNCH_EXIT!
