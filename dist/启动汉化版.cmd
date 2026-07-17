@echo off
rem =====================================================================
rem  Quake 4 Chinese Localization Launcher
rem  First use: edit GAME_DIR below to your Quake 4 install folder
rem  (the folder that contains the "q4base" subfolder)
rem  Details / help: see README.txt
rem =====================================================================
set GAME_DIR=C:\Program Files (x86)\Steam\steamapps\common\Quake 4

rem Resolution (16:9 recommended, fonts are calibrated for 16:9)
set W=1920
set H=1080

if not exist "%GAME_DIR%\q4base\pak001.pk4" (
  echo [ERROR] Not found: "%GAME_DIR%\q4base\pak001.pk4"
  echo Edit this file and set GAME_DIR to your Quake 4 install folder.
  pause
  exit /b 1
)
if not exist "%GAME_DIR%\q4base\pak021.pk4" (
  echo [ERROR] Your Quake 4 is not patched to 1.4.2 ^(pak021.pk4 missing^).
  echo Retail/CD version: install the official 1.4.2 patch first.
  echo Steam version already includes it.
  pause
  exit /b 1
)

"%~dp0engine\Quake4.exe" ^
 +set fs_basepath "%GAME_DIR%" ^
 +set fs_savepath "%~dp0savedata" ^
 +set sys_lang chinese +set harm_gui_wideCharLang 1 ^
 +set gui_smallFontLimit 0 ^
 +set image_forceDownSize 0 ^
 +set com_allowConsole 1 ^
 +set logFile 2 ^
 +set r_fullscreen 1 +set r_mode -1 +set r_customWidth %W% +set r_customHeight %H% ^
 +set r_useShadowMapping 1 +set harm_r_softStencilShadow 0
