@echo off
setlocal enabledelayedexpansion
title Restarting CLAUSENT Services

cd /d "%~dp0"

echo ========================================================
echo             RESTARTING CLAUSENT SERVICES                
echo ========================================================
echo.

call "%~dp0stop.bat"
echo.
echo Restarting services now...
powershell -NoProfile -Command "Start-Sleep -Seconds 2"
call "%~dp0start.bat"
