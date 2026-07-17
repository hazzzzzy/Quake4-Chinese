@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

rem =====================================================================
rem  Quake 4 汉化 - 一次性补齐脚本（首次使用运行一次即可）
rem
rem  从你自己的 Quake 4 原版 pak001.pk4 + pak021.pk4 现场生成汉化包不能
rem  分发的四类版权敏感物：Strogg 外星文字体、HUD 无线电两行、神经细胞
rem  植入转译动画、中文语音路径别名。
rem  不修改你的原版游戏目录。
rem =====================================================================

rem --- 定位原版游戏目录（从「启动汉化版.cmd」读 GAME_DIR）---
set GAME_DIR=
for /f "tokens=1,* delims==" %%A in ('type "%~dp0启动汉化版.cmd" ^| findstr /b "set GAME_DIR="') do (
  set "GAME_DIR=%%B"
)
rem 允许命令行覆盖：postinstall.cmd "D:\Games\Quake 4"
if not "%~1"=="" set "GAME_DIR=%~1"

if not defined GAME_DIR (
  echo [错误] 未能识别原版 Quake 4 安装目录。
  echo 请先编辑「启动汉化版.cmd」把 GAME_DIR 设为你的安装目录（包含 q4base 的那个）。
  pause
  exit /b 1
)
if not exist "%GAME_DIR%\q4base\pak001.pk4" (
  echo [错误] 目录里没找到 q4base\pak001.pk4：%GAME_DIR%
  echo 请检查 GAME_DIR 是否正确。
  pause
  exit /b 1
)
if not exist "%GAME_DIR%\q4base\pak021.pk4" (
  echo [错误] 你的 Quake 4 不是 1.4.2 版本 ^(缺 pak021.pk4^)。
  echo Steam 版自带 1.4.2；光盘/下载版需先装官方 1.4.2 补丁。
  pause
  exit /b 1
)

rem --- 检测 Python 3 ---
set PY=
for %%C in (py.exe python.exe python3.exe) do (
  where %%C >nul 2>nul && (set "PY=%%C" && goto :found_py)
)
:found_py
if not defined PY (
  echo [错误] 未检测到 Python 3。补齐脚本需要 Python 才能运行。
  echo 建议安装方式（任选其一）：
  echo   1^) 打开 Microsoft Store 搜索 "Python 3"
  echo   2^) winget install Python.Python.3.12
  echo   3^) https://www.python.org/downloads/  下载安装包
  echo 装好后重新双击本脚本即可。
  pause
  exit /b 1
)

rem --- 调用 build_dist_extras.py ---
echo GAME_DIR = %GAME_DIR%
echo Python   = %PY%
echo.
%PY% "%~dp0..\src\tools\build_dist_extras.py" ^
  --game-dir "%GAME_DIR%" ^
  --out "%~dp0savedata\q4base"
set RET=%errorlevel%
echo.
if %RET% NEQ 0 (
  echo [失败] 补齐脚本以退出码 %RET% 结束。
  pause
  exit /b %RET%
)
echo 现在双击「启动汉化版.cmd」进游戏吧。
pause
