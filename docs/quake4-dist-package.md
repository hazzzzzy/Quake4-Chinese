---
name: quake4-dist-package
description: 汉化分发包已产出（quake4-cn/dist/Quake4-CN-v1.0-20260717.zip，77MB）：引擎+DLL+全部松散汉化资产+GBK 启动器+README，指向用户原版 1.4.2 数据即玩
metadata:
  node_type: memory
  type: project
  originSessionId: af264300-0f3e-460f-9332-cd68c241bb86
---

Quake 4 汉化分发包制作方法与内容清单（2026-07-17 首版 v1.0）。

**Why:** 用户要在自己电脑（只有原版 Q4）上游玩；后续汉化更新需重打包，清单和坑都在这里。

**How to apply:**

- 产物：`D:\data\quake4-cn\dist\Quake4-CN-v1.0-20260717.zip`（77MB，目录树在 dist/Quake4-CN）。
- 结构：`engine/`（Quake4.exe + SDL2/OpenAL32/libcurl/zlib1.dll + 我们的 q4game.dll + q4game.dll.official 备份）+ `savedata/q4base/`（fonts/chinese 74MB、strings 5 个 lang、guis/{hud,subtitles,maps/medlabs/med1_textchange}.gui、materials/zzz_chinese_font_alias.mtr、lipsync/zz_chinese_radio.lipsync、zzz_chinese_vo.pk4、quake4key/xpkey）+ `启动汉化版.cmd`（**GBK 编码**，cmd 中文必须 GBK）+ `README.txt`（UTF-8 BOM）。
- 启动器要点：用户只改 GAME_DIR= 原版安装目录；fs_savepath=%~dp0savedata（零污染原版目录，存档/配置都在包内）；内置两道检查——pak001.pk4（路径对不对）与 **pak021.pk4（必须 1.4.2 补丁，否则 hud.gui 覆盖结构错配会读档崩溃，r4 教训）**；cvar 全套：sys_lang chinese / harm_gui_wideCharLang 1 / gui_smallFontLimit 0 / r_mode -1 + W×H（默认 1920x1080，脚本顶部可改）。
- 排除项（勿打进包）：fonts/chinese_bak_r4（943MB 旧字库）、poc_*.cfg、demo_textchange.gui、screenshots/savegames/qconsole 日志、Quake4Config.cfg（首启自动生成）、zh_*.ttf 散件、引擎目录的 hardqore mod 与 run_*.bat。
- 注意：字体按 16:9 校准（ASPECT=0.75），README 已注明；重打包命令 `py -c "shutil.make_archive(...)"`（python zipfile 的 UTF-8 文件名旗标，Win10+ 解压中文名正常）。
- **v1.0.1（用户实机首个反馈）**：用户电脑首启菜单文字糊团——根因=新配置被 Q4 老式硬件检测判为低配，`image_downSize 1`+`downSizeLimit 256` 把 2048 字体页压到 256（本机 +set 复现完全一致）。修复：全部 54 条字体材质 decl 的 **stage 内**加 `nopicmip`（真正挡降采样的开关——GetDownsize 的 allowDownSize 就是 stage 的 allowPicmip；`forceHighQuality` 只管 TD_HIGH_QUALITY 不压缩、不挡降采样，且**这俩都是 stage 级关键字，写在材质全局层会解析异常导致文字消失**）+ `forceHighQuality`（防 DXT alpha 伪影），启动器补 `+set image_forceDownSize 0`（该 cvar 可无视 nopicmip）。低配画质强制复验：文字满清晰。产物 Quake4-CN-v1.0.1-20260717.zip。
- **v1.0.2**：用户用记事本编辑 GBK 启动器后被存成 UTF-8（BOM 被 cmd 按 GBK 读→'嫫舳?rem' 乱码报错）——**分发给用户的 .cmd 必须纯 ASCII**（用户必然会编辑 GAME_DIR，无法约束其编辑器编码；中文说明全部放 README）。启动器已全英文化，产物 Quake4-CN-v1.0.2-20260717.zip。
