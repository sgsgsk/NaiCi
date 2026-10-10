@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "发布\背诵单词.exe" (
  start "" "发布\背诵单词.exe"
  exit /b 0
)
echo 未找到 发布\背诵单词.exe
echo 请先双击 build_exe.bat 打包。
pause
