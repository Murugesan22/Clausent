@echo off
setlocal enabledelayedexpansion
title Stopping CLAUSENT Services

echo ========================================================
echo              STOPPING CLAUSENT SERVICES                 
echo ========================================================
echo.

echo [1/3] Terminating CLAUSENT terminal windows...
taskkill /FI "WINDOWTITLE eq CLAUSENT-Backend*" /F /T >nul 2>&1
taskkill /FI "WINDOWTITLE eq CLAUSENT-Frontend*" /F /T >nul 2>&1

echo [2/3] Freeing Backend port (8000) and Frontend port (5173)...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ports = @(8000, 5173); " ^
  "foreach ($port in $ports) { " ^
  "  $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue; " ^
  "  if ($conns) { " ^
  "    foreach ($c in $conns) { " ^
  "      try { " ^
  "        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue; " ^
  "        Write-Host ('[+] Successfully terminated process on port ' + $port + ' (PID ' + $c.OwningProcess + ')'); " ^
  "      } catch {} " ^
  "    } " ^
  "  } else { " ^
  "    Write-Host ('[-] Port ' + $port + ' was already free.'); " ^
  "  } " ^
  "}"

echo [3/3] Checking remaining Node and Python child processes...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-CimInstance Win32_Process | Where-Object { ($_.Name -match 'python.exe' -and $_.CommandLine -match 'app.main:app') -or ($_.Name -match 'node.exe' -and $_.CommandLine -match 'vite') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host ('[+] Cleaned up process ' + $_.Name + ' (PID ' + $_.ProcessId + ')') }"

echo.
echo ========================================================
echo   [OK] All CLAUSENT services have been stopped.
echo ========================================================
powershell -NoProfile -Command "Start-Sleep -Seconds 2"
exit /b 0

