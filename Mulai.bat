@echo off
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 (
  echo Menyiapkan alat yang dibutuhkan ^(hanya sekali, perlu internet^)...
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 ^| iex"
)
where uv >nul 2>nul
if errorlevel 1 (
  echo Maaf, uv tidak bisa dipasang. Cek internet, lalu lihat README.md bagian "Kalau ada masalah".
  pause
  exit /b 1
)
if not exist .venv echo Pertama kali: menyiapkan aplikasi ^(sekitar 1 menit, perlu internet^)...
echo Membuka aplikasi di browser kamu... ^(jangan tutup jendela ini selama memakai aplikasi^)
uv run --frozen --quiet python -m app.main
if errorlevel 1 (
  echo.
  echo Maaf, aplikasi berhenti dengan error. Lihat README.md bagian "Kalau ada masalah".
  pause
)
