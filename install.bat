@echo off
rem Sales Studio installer (Windows). Downloads the app from GitHub (no git needed) and starts it.
rem   curl -L -o install.bat https://raw.githubusercontent.com/sfrnld/jackrabbits/main/install.bat   then double-click it.
rem Running it again updates the app in place; your data (.env, state\) is never touched.
setlocal
set "REPO=sfrnld/jackrabbits"
set "BRANCH=main"
if "%SALES_STUDIO_DIR%"=="" set "SALES_STUDIO_DIR=%USERPROFILE%\Sales-Studio"
if "%SALES_STUDIO_SRC%"=="" (
  set "SALES_STUDIO_SRC=https://github.com/%REPO%/archive/refs/heads/%BRANCH%.zip"
)
set "TMPD=%TEMP%\sales-studio-dl"
if exist "%TMPD%" rmdir /s /q "%TMPD%"
mkdir "%TMPD%"
echo Mengunduh Sales Studio dari GitHub... ^(sekitar 1 MB, perlu internet^)
curl.exe -fL -o "%TMPD%\app.zip" "%SALES_STUDIO_SRC%"
if errorlevel 1 ( echo Maaf, gagal mengunduh. Cek koneksi internet. & pause & exit /b 1 )
tar.exe -xf "%TMPD%\app.zip" -C "%TMPD%"
if errorlevel 1 ( echo Maaf, file unduhan rusak. & pause & exit /b 1 )
set "SRC="
for /d %%D in ("%TMPD%\*") do set "SRC=%%D"
if not exist "%SRC%\Mulai.bat" ( echo Maaf, isi unduhan tidak dikenali. & pause & exit /b 1 )
if exist "%SALES_STUDIO_DIR%\Mulai.bat" ( echo Memperbarui aplikasi di %SALES_STUDIO_DIR% ^(data kamu aman^)... ) else ( echo Memasang ke %SALES_STUDIO_DIR% ... )
xcopy "%SRC%\*" "%SALES_STUDIO_DIR%\" /E /Y /I /Q >nul
if errorlevel 1 ( echo Maaf, tidak bisa menulis ke %SALES_STUDIO_DIR%. & pause & exit /b 1 )
rmdir /s /q "%TMPD%"
echo Selesai. Lain kali cukup double-click Mulai.bat di folder: %SALES_STUDIO_DIR%
if not "%SALES_STUDIO_NO_RUN%"=="" exit /b 0
cd /d "%SALES_STUDIO_DIR%"
call Mulai.bat
