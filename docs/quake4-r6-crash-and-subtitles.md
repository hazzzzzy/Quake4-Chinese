---
name: quake4-r6-crash-and-subtitles
description: 第六轮（2026-07-17 深夜）：换图概率崩溃根因=rvSubtitles 缓存 gui 裸指针跨图悬空（c0000409，符号化转储定位）；speaker 播报字幕钩子/友军门控放宽/字幕面板上移缩窄；PDB+MAP+python minidump 排障流程
metadata:
  node_type: memory
  type: project
  originSessionId: af264300-0f3e-460f-9332-cd68c241bb86
  modified: 2026-07-18T14:15:09.429Z
---

Quake 4 汉化第六轮：用户实机（GTX 1650）反馈的换图崩溃与三项字幕改进，全部修复验证（承接 [[quake4-strogg-changeover]]、[[quake4-dist-package]]）。

**Why:** 崩溃排障流程（无 cdb 环境下的符号化）和 idTech4 GUI 生命周期教训极易复用；字幕系统的门控/钩子语义定案于此。

**How to apply:**

- **换图崩溃根因（重大）**：`rvSubtitles::Draw` 把 `uiManager->FindGui` 返回的 gui 指针存成员一次性缓存——**换图时 uiManager 释放重建 GUI 实例，缓存指针悬空**，Draw 再 SetState/Redraw 写坏堆 → CRT 快速失败 c0000409（概率性=悬空内存是否被复用；换图/退出时都可能触发，今晨 6:17 与用户实机崩溃同签名）。修复：**绝不缓存 GUI 裸指针跨图，每帧按名 FindGui**（内部有哈希缓存，开销可忽略）。教训通用于任何游戏 DLL 持有引擎对象指针跨地图。
- **无 cdb 的崩溃排障流程（可复用）**：(1) WER LocalDumps DumpType=1 抓 minidump；(2) DLL 编译加 /Zi、链接加 /DEBUG /MAP（CMakeCache.txt 改 CMAKE_CXX_FLAGS_RELEASE 与 CMAKE_SHARED_LINKER_FLAGS_RELEASE 后**必须 cmake . 重新生成**才生效）；(3) pip 装 minidump 包，python 解析：模块表定位段、thread.ThreadContext 是 LOCATION_DESCRIPTOR 需手解 CONTEXT（Rsp@0x98/Rip@0xF8）、栈内存分页读（跨段会抛异常）扫返回地址；(4) 用链接器 .map 的 Rva+Base 减基址二分映射符号。复现循环：跑 N 次数 dump 数变化即停。
- **speaker 播报字幕钩子**：idSound::DoSound(play) 内按 shader 名找 lipsync decl（先原名再 lipsync_ 前缀），AddFromEntity 走门控；环境音无 decl 自然跳过。开场女声广播=airdefense1 的 spkr_rc_1~4（vo_1_1_0_01_2/3/20/21），原版无 decl，已补 str_380251-380254 进 radio_chatter.tsv（decl 253 条、lips lang 4217 条）。**Sound.cpp 加中文注释后必须转 UTF-8 BOM**（C4819=码页误读前兆）。
- **可听性门控定案**：友军（同 team 的 idActor）剧情语音按无线电对待——不做 PVS 门控、距离容差 1.5×（Kovitch/Morris 缺字幕的根因：脚本让队友远处/隔墙发言被误拦，实测 Morris 912 vs max 900）；敌军保留 PVS 门控 + 1.15× 容差。
- **字幕面板布局 v2**（用户要求上移缩窄）：SUB_BOTTOM 428→410、SUB_TEXT_W 434→356（Subtitles.cpp）+ subtitles.gui 面板 rect 90/460→130/380、文本 96/448→136/368——**三处联动，改一处必须同步**。
- **帧率真相**：USERCMD_HZ=60 硬编码，无法解锁 144；1650 建议 harm_r_softStencilShadow 0 稳 60（v1.0.3 启动器已默认）。崩溃后桌面发白=硬件 gamma ramp 未复位，Win+Ctrl+Shift+B 或重启游戏正常退出即恢复。
- **v1.0.3 启动器**：加 +set logFile 2（用户日志常开，报障直接发 savedata\q4base\qconsole.log）。用户实机挂载 H:\Quake4-CN，可直接同步（保留 savedata 的存档/配置，只换 engine/资产/启动器）。
- **v1.0.4（第七轮反馈）**：(1) **第三类资产缺口=AI 对话 decl 缺失**：Kovitch 等 NPC 台词 aiSpeak 引用的 decl 原版就没有（引擎默认 decl 播声无文本无口型，"听得到嘴不动没字幕"）；全游戏审计 vo_* 缺口 1436、其中有 sndshd 台词的 726 条，同句复用已审译文 597 + 双代理翻译 129，生成 savedata lipsync/zz_chinese_aivo.lipsync（668 条，**纯音效指示如 (pain grunt)/laugh 已过滤不出字幕防刷屏**），表 translations/ai_vo_gap.tsv（str_385000 起），build_lang 已并入（lips 4941）、export_font 字符集来源已加该表（本次零新字）。审计法：map/def 的 "lipsync_*" 键值集 − 全部 .lipsync decl 名集。(2) **字幕来源前缀**：无线电→"无线电"、speaker→"广播"（AddFromEntity 新 fallbackSpeaker 参数）、无名友军 AI→"士兵"（同队 actor 兜底），中文一律 UTF-8 转义。(3) EXIT→撤离、transfer→转移（exitlevel/currentlevel gui 顶部字样）。(4) PA 4 条中 _3/_20 原版 intro.lipsync 已有 decl（探测正则漏检教训：用引擎告警"previously defined"反查最可靠），radio 表已去重回 251。用户确认换图崩溃修复有效。
- **v1.0.5（第八轮）**：**CJK 垂直对中定案**——汉字无降部且墨迹顶得高，在为拉丁设计的窗格里普遍偏上（loading 地名/载入中/设置行/切枪武器名）；解法=export_font rasterize 加 drop 参数（12→1、24→2、48→4 名义 px），**宽表字形位图顶部烘入透明行、top 度量不变**→墨迹相对基线整体下沉、基线/maxHeight/混排不受影响（r3"不能压 top"教训的正解就是这个）；ASCII 不动（HUD 数字无裁切风险）。EXIT LEVEL(str_200278)/exit(str_200379)/transfer(str_200377) → 撤离/撤离/转移；用户所述关卡末尾「离开」在全部译表无独立词条，待用户截图定位。死亡时「必须存活才能保存游戏」(str_104311)=引擎 exe 死亡状态拦截存档的原版提示，非 bug。设置页「No Choices Defined」=r_mode -1 自定义分辨率下引擎无预设可列，原版行为。
- **v1.0.10.1（其他会话 v1.0.6-10 之后本轮）**：hud.gui t_radio1 加 `shear 0,-.22` + `textalign 1` + textscale 0.16→单行 + 斜体贴合背景条平行四边形；radio_backbar 恢复原版 rect 520,5,113,28（v1.0.9 曾缩窄 72 被撤销）。**关键实验结论：idTech4 存档序列化的 gui 状态包括所有数值属性**（rect/textscale 等），本轮 loadGame gamestart 后即使把 textscale 从 0.2 改到 0.16，屏显字号仍是 0.2 原值——**gui 磁盘文件的最新配置只在换图/新档时生效，旧存档加载时被存档里的旧数值覆盖**。这解释了用户第 3 问："加载存档看到旧样式 / 换图后看到新样式"、"游戏已保存旧档能消失新地图不能"（quicksave_msg 淡出机制随 gui 状态一起被旧存档冻结）。加 shear/textalign 新字段可能加剧旧存档读写错位（r4 崩溃机制的软版本），风险与收益权衡后仍采纳（用户明确要求斜体）；建议用户接受"新档/换图后才见新版"。**"外星文字"是设计**：strogg 家族 v1.0.6+ 直通原版基础段，ASCII 显示外星字母；关卡末尾 EXIT 大门 / 可交互面板里的英文外星化是改造前正确表现，改造后由 r_strogg 变可读中文（med1_textchange 转译动画完成切换）。
