@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Please close 背诵单词 if it is running.
taskkill /F /IM "背诵单词.exe" >nul 2>&1

echo [1/3] install deps
python -m pip install -r requirements.txt -q

echo [2/3] build onefile exe
if exist "release_build" rmdir /s /q "release_build"
if exist "release_dist" rmdir /s /q "release_dist"
python -m PyInstaller --noconfirm --onefile --windowed --noupx --name "背诵单词" --icon "assets\app_icon.ico" --add-data "assets;assets" --distpath "release_dist" --workpath "release_build" main.py
if errorlevel 1 (
  echo BUILD FAILED
  pause
  exit /b 1
)

echo [3/3] copy to release folder
if not exist "发布" mkdir "发布"
if not exist "发布\记录文件" mkdir "发布\记录文件"
copy /Y "release_dist\背诵单词.exe" "发布\背诵单词.exe" >nul
if not exist "发布\记录文件\说明.txt" (
  echo wordbooks go here> "发布\记录文件\说明.txt"
)
if exist "记录文件" rmdir /s /q "记录文件"
if exist "release_build" rmdir /s /q "release_build"
if exist "release_dist" rmdir /s /q "release_dist"
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo Done: 发布\背诵单词.exe
echo Wordbooks: 发布\记录文件\
pause
