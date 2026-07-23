---
name: quake4-feedback-fixes-r3
description: 第三轮用户反馈修复（2026-07-16 下午）：字幕标签清理/可听性门控/无线电字幕/HUD 数字裁切/传入通讯重叠/Strogg 字体 full 化，含字体基线机制与米勒卡关分析
metadata:
  node_type: memory
  type: project
  originSessionId: 0800a440-2bfc-417e-8d15-db1cd7cd0c87
---

Quake 4 汉化第三轮反馈修复，全部已实现并部署，实机验证移交用户（见 [[quake4-poc-passed]]）。

**Why:** 这轮查清了引擎文本纵向布局机制和 Q4 对话/无线电机制，后续遇到同类问题直接查此记录。

**How to apply:**

- **字幕文本污染**：英文源串（lips lang）本身带 `{furrow}`/`{idle}` 等录音情绪标记（585 处保留在 chinese_lips.lang），显示端在 `rvSubtitles::Sanitize`（Subtitles.cpp）剥离 `{…}` + 折叠连续空格；译文/主表不清洗（保持源对应）。字幕已左对齐（subtitles.gui textalign 0）。
- **可听性门控**（rvSubtitles::IsAudible）：过场/全局声/IsVO_ForPlayer/玩家自己→一律显示；距离 > shader maxDistance → 不显示（**_RAVEN 分支声音距离直接是游戏单位，不转米**，见 sound.h `//#if !defined(_RAVEN)` 注释）；>240 单位且不在玩家 PVS（隔墙）→ 不显示。cvar：harm_g_subtitlePVSCheck（默认 1）、harm_g_subtitleDebug（打 [SUB] 决策日志，验收必开）。
- **无线电字幕**：`idFuncRadioChatter::Event_Activate`（Misc.cpp）挂 `FindLipSync(snd_radiochatter 值, false)`——radio 的 sound shader 名与 lipsync decl 同名（vo_*），decl 的 text 字段即 #str。无头模型 AI 走不到 StartLipSyncing，已在 idAI::Speak 的 else 分支补注入（AI.cpp）。
- **字体基线机制**（HUD 数字被裁的根因）：引擎 RegisterFont 运行时 maxHeight = max(全部字形 top)（宽字库 height:=top，tr_font.cpp:410）；文本基线 = rect.y + maxHeight*useScale（useScale=textscale*48/pointSize）。中文全字库 maxHeight 比英文大（chain24: 28 vs 21）→ 所有文本相对英文原版下移、紧 rect 底部被裁。**不能靠改 fontdat 修**（压 top 会破坏中英混排基线），只能松散覆盖 gui 调 rect。已做 savedata\q4base\guis\hud.gui（生成器 quake4-cn/tools/patch_hud.py，13 处：数字窗口 y-7/h+7、total_ammo y-5/h+5、无线电两行 y=4/17）。**注意：本轮覆盖误用 pak001 底稿导致读档崩溃，r4 已换 pak021 底稿修复，见 [[quake4-feedback-fixes-r4]]**。GUI 字号档位：textscale ≤0.30→12 号、≤0.60→24 号、否则 48 号。
- **Strogg 两套字体已 full 化**：exportFont zh_glow_norm.ttf strogg/r_strogg chinese 2048（7424 字形，与 UI v5 同源未来荧黑），48 号仍用 24 号复制绕过。医疗站 ??? 根因就是 min 档缺"生命值/站点/已耗尽"字形。
- **米勒"卡关"分析**（scripts/maps/airdefense1.script）：millerHelpsWoundedMarine 过场结束即 trigger $objectiveMedic（任务：回登陆点带医疗兵 Anderson）+ setTalkState(TALK_OK)；截图中 Miller 站立 relaxed_idle = 过场已走完，**关卡没有卡**，需玩家跑回出生点。Q4 对话机制 = 准星名牌（talkCursor）+ 按开火键才触发 TalkTo，且 TALKMSG 轮完一圈后不再响应——"不会向我发话"是机制误解 + 远处台词字幕误导（门控修复后缓解）。复现工具：tmp\scripts\verify_miller.ps1（读 checkPoint 存档+自动点击对话+截图）、verify_features.ps1（无线电/医疗站/HUD 验证），配套 savedata 的 poc_verify_*.cfg。
- **编码坑扩展**：.ps1 中文注释也必须 UTF-8 with BOM（PS 5.1 无 BOM 按 GBK 解析直接炸）；MSVC 源文件同理（C4819 警告=码页错读，必须处理）。
- fontdat 结构解析器：quake4-cn/tools/parse_fontdat.py（Q4 基础段 9float×256+5float，宽表 magic+indexes+68B/字形）。
- **字幕消失时垂直抖动已修**：原行定位从面板顶按行号算，旧行删除→剩余行号-1 瞬跳 13px 再被面板收缩送回。改为行锚定面板底（restY），面板生长期取 max(restY, 顶部滑入位) 保留新行顶入平滑（Subtitles.cpp Draw）。
