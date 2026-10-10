@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 请先关闭正在运行的「背诵单词」。
taskkill /F /IM "背诵单词.exe" >nul 2>&1

echo [1/3] 安装依赖...
python -m pip install -r requirements.txt -q

echo [2/3] 打包单文件 exe（带图标）...
if exist "release_build" rmdir /s /q "release_build"
if exist "release_dist" rmdir /s /q "release_dist"
rem --noupx：避免 UPX 压缩导致杀软误报、他机异常或需管理员
python -m PyInstaller --noconfirm --onefile --windowed --noupx --name "背诵单词" --icon "assets\app_icon.ico" --add-data "assets;assets" --distpath "release_dist" --workpath "release_build" main.py
if errorlevel 1 (
  echo 打包失败
  pause
  exit /b 1
)

echo [3/3] 更新发布目录（保留已有词库）...
if not exist "发布" mkdir "发布"
if not exist "发布\记录文件" mkdir "发布\记录文件"
copy /Y "release_dist\背诵单词.exe" "发布\背诵单词.exe" >nul
if not exist "发布\记录文件\说明.txt" (
  echo 词库 md 文件保存在此文件夹（与 背诵单词.exe 同级）。> "发布\记录文件\说明.txt"
)
rem 删除根目录多余的记录文件，统一只用 发布\记录文件
if exist "记录文件" rmdir /s /q "记录文件"

rem 清理临时目录
if exist "release_build" rmdir /s /q "release_build"
if exist "release_dist" rmdir /s /q "release_dist"
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo ========================================
echo 请双击运行：发布\背诵单词.exe
echo 或双击：启动.bat
echo 词库目录：发布\记录文件\
echo ========================================
pause
