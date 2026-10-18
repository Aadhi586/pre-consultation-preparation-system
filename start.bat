@echo off
cd /d "%~dp0"
echo Starting Pre-care. Keep this window open while you use the app.
where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
      set "PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
      set "PY_ARGS="
    ) else (
      echo Python 3.10 or newer was not found. Install Python and run this file again.
      pause
      exit /b 1
    )
  ) else (
    set "PYTHON=python"
    set "PY_ARGS="
  )
) else (
  set "PYTHON=py"
  set "PY_ARGS=-3"
)
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000'"
"%PYTHON%" %PY_ARGS% server.py
if errorlevel 1 pause
