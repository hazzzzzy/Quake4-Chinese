---
name: quake4-poc-passed
description: Quake 4 汉化 PoC 已通过（2026-07-16）：idTech4A++ h70 跑正版数据画面达标，中文渲染全链路打通，含关键 cvar/命令/上游 bug 绕过
metadata:
  node_type: memory
  type: project
  originSessionId: 5921d973-6786-437e-8a4c-f1b0be19e135
---

Quake 4 简体中文汉化项目 PoC 于 2026-07-16 通过（G2 画面+G3 中文双通过），完整报告在 `D:\data\Quake 4\tests\poc-report.md`。

**Why:** 后续会话进入正式翻译期，这些实测结论决定工具链与参数，勿重新摸索。

**How to apply:**
- 引擎：idTech4A++ v1.1.0harmattan70 装在 `D:\data\idTech4Apx\quake4\Quake4.exe`；启动参数 `+set fs_basepath "D:\data\Quake 4" +set fs_savepath "D:\data\idTech4Apx\savedata"`（零污染，已验证）；统一入口 `D:\data\Quake 4\tmp\scripts\run_apx.cmd`。
- 中文渲染：`+set sys_lang chinese +set harm_gui_wideCharLang 1`；lang 用 Raven 分文件名 `strings/chinese_code.lang`/`chinese_guis.lang`（UTF-8 with BOM 硬性要求），放 savedata\q4base\strings\ 松散即生效；字体用引擎控制台 `exportFont <ttf> <chain|marine|...> chinese <纹理宽>` 生成到 fonts/chinese/。
- 上游 exportFont 两个 bug 及绕过：48 号 fontdat 度量坏→用 24 号 fontdat 复制为 48 号；字符集最后一个字符丢失→尾部垫哨兵字符（￥）。待给 glKarin 提 issue（可能已修复则去掉绕过）。
- 无人值守自动化：`com_skipLevelLoadPause 1` 跳 CLICK TO CONTINUE；启动落全屏控制台用 `disconnect` 回菜单；cfg 里 `+attack` 无效，战斗特效靠 `spawn monster_*`；编排器 `tmp\scripts\drive_engine.ps1`（引擎 TGA 截图→Pillow 转 PNG 查看）。
- 已知问题：带 spawn AI 时 quit 有 ~75% 概率退出崩溃（0xC0000005，仅退出时）；原版 Quake4.exe 无头会话卡 intro 视频无法自动化对照；原版运行会刷新 q4base\quake4key 时间戳（无害）。
- 相关脚本：build_chinese_assets.py（一键生成全套 5 个中文 lang + VO 别名 pk4，取代早期 make_lang.py）、make_subset.py（fonttools 子集化，min/gb1 两档）。
- 用户复验发现并已修复的两个问题（2026-07-16）：(1) 准星指队友显示裸 #str_id——因为中文模式只有 code/guis 两个 lang；引擎跨 pk4 按条目合并同名 lang（日志 "N strings read" 是累计计数），中文无底包必须自己合并全量，`build_chinese_assets.py` 已生成全部 5 个（code 695/guis 1098/lips 3962/mappack 3/maps 476）。(2) 队友语音消失——VO 文件在 pk4 内的真实路径是 sound/vo_english/，引擎按 sys_lang 把 sound/vo/ 映射到 sound/vo_<语言>/，中文模式找 vo_chinese 落空即静音；修复=生成 zzz_chinese_vo.pk4（3406 个文件别名为 vo_chinese，64.7MB，英文原声）放 savedata\q4base。
- 字体已从黑体换微软雅黑粗体（msyhbd.ttc，fontTools --font-number=0 抽 ttc）；UI 四套（chain/marine/lowpixel/profont）gb1 档 1024 宽，Strogg 装饰两套 min 档；可随时换任意 TTF/TTC 重跑 exportFont。
- 正式汉化工程根 `D:\data\quake4-cn\`（translations/ 翻译主表 TSV + tools/ 管线 + docs/glossary.md 术语表 v1.0 已定稿 + diii4a/ 源码克隆）。WP1 UI 全量翻译初稿已完成部署（2230/2272，9 个并行子代理翻译，104 条存疑在 qa_doubts.txt 待复核）；管线：merge_batches.py（QA+合并）→ build_lang.py（生成部署 lang）。
- WP3 字幕工程基线成立：**源码必须用 v1.1.0harmattan70 tag**（master 编译的 DLL 与 h70 引擎 ABI 不兼容会进图即崩；h70 时源码路径在 Q3E/src/main/jni/doom3/neo 而非顶层 doom3/neo）。VS2022+自带 cmake 配置：-DCORE=OFF -DBASE=OFF -DRAVEN=OFF -DQUAKE4=ON 只编 q4game.dll，需本地补丁把 WIN32 的 SDL2 find_package 挡在引擎目标后（补丁在克隆区未提交）。官方 DLL 备份为 q4game.dll.official。字幕挂点已定位：idAI::Speak → idAFAttachment::StartLipSyncing（LipSync.cpp），speechDecl 即 lipsync decl 名。
- 用户要求启动脚本全屏（run_apx_chinese.cmd 已改 r_fullscreen 1）。
- 汉化主体完成（2026-07-16 深夜）：UI 2272 + 对白 3962 全部翻译并部署（build_lang 报 99%），183 条存疑在 translations/qa_doubts.txt 待复核；对白经 8 个并行代理翻译，一致性清扫统一了 squib→杂碎，Rhodes 确认为男性（我早期简报误写女性，台词已核无误用）。字幕系统完成：quake4/Subtitles.{h,cpp}（rvSubtitles 单例，UTF-8 拆行 40 半角/行）+ LipSync.cpp/Game_local.cpp 挂钩 + savedata guis/subtitles.gui；cvar harm_g_subtitles/HoldTime/MinTime；实机验证截图 tests\screenshots（含 shot00122 说话人前缀字幕）。**源码含中文注释必须存 UTF-8 with BOM**（MSVC GBK 码页会吞行导致诡异编译错）。自编 DLL 已部署引擎目录（官方备份 q4game.dll.official）。
- 用户复验二轮修复（2026-07-16）：(1) 设置页问号=字符集缺字形——gb1 档只有 GB2312 一级汉字，缺全角符号区（（）。等）和二级字（霰）；改用 full 档 = GB2312 全集（0xA1-0xF7 全区）∪ 翻译主表实际用字 ∪ ASCII，7543 字形，UI 四套字体 2048 宽重导已部署验证。字体档位定案用 full。(2) 小队名全部中文化（用户拍板）：犀牛/天蝎/猛獾/神鹰/棕熊/渡鸦/毒蛇/野狼/雄鹰/眼镜蛇/疣猪小队（fix_squads.py，术语表需同步）。
