---
name: quake4-strogg-changeover
description: "Strogg 文字转译动画机制与最终方案（已实装验证）：strogg=原版外星字形直通+CJK→符号合成宽表，r_strogg=思源 Medium，med1_textchange.gui 中文化覆盖（神经细胞已植入）；含实机演示方法"
metadata:
  node_type: memory
  type: project
  originSessionId: af264300-0f3e-460f-9332-cd68c241bb86
---

Quake 4 斯特罗格改造后「文字转译」动画的机制与现状（2026-07-17 实机演示验证，承接 [[quake4-font-aspect-and-size]]）。

**Why:** 该动画是汉化观感的关键节目效果，两套 Strogg 字体的语义区分（外星文 vs 可读文）决定全游戏 Strogg 终端的氛围正确性；演示方法可复用。

**How to apply:**

- **机制**：`guis/maps/medlabs/med1_textchange.gui`（pak001，1395 行）即 Kane 改造苏醒后监视器上"neurocyte implanted"的转译动画。18+7+7 个单字符 windowDef 各有两层：`fonts/strogg`（原版=外星字形）与 `fonts/r_strogg`（原版=可读字形），`onNamedEvent changeover` → `resettime "anim" 0` 启动，anim 时间线每 200ms 一批、乱序对各字母做 forecolor_w 交叉淡变（250ms）+ bluradd 泛光（500ms）+ guisound_beep2，由 medlabs 地图脚本在改造过场后发事件。
- **字体语义**：strogg 家族全游戏只用于装饰文本（医疗站数字 84278.324、乱码序号），不承载翻译中文；r_strogg 承载可读标签（#str，已译中文）。
- **最终方案（2026-07-17 已实装，实机 GIF 验证通过）**：
  - strogg 家族=原版直通：export_font.py `passthrough_original`（FAMILIES 值=ORIGINAL 哨兵）从 pak001 拷 fonts/english/strogg_* 的 fontdat base 段+贴图原样，**附加合成宽表把全量 CJK 按 Knuth 乘散列（cp×2654435761 % 池大小）稳定映射到原版 62 个字母/数字符号字形**（shaderName="<字号>.tga"指回 base 单页）——中文文本经 strogg 字体自动"外星化"。多数装饰窗可继续与可读窗共用译文；但固定短标签若中文字符数明显少于原英文，改造前会显得缺字。2026-07-21 实机确认生命补给器、撤离屏和升降梯属于该例外，改造前窗口改用原英文常量保持字母数量，改造后窗口继续引用中文 str。
  - r_strogg 的 CJK 宽字表使用思源黑体 Medium；ASCII/数字基础段保留原版 r_strogg 字形，使改造后生命、护甲、弹药与计时数字保持 Raven 原版 HUD 风格。该家族不能再整份复用 marine fontdat。
  - r_strogg 的 CJK 下沉量只取普通中文家族的一半（12/24/48 档为 0/1/2，而非 1/2/4），否则不可交互 Strogg 面板的第三行会压住下边线。中文宽字表与原版基础段必须分别验证，不能用整文件哈希代替。
  - 改造后无线电 `t_radio1` 的磁盘正确值仍是 `rect 556,3,72,22`；旧存档可能恢复更早的 rect，表现为“传入通讯”贴近背景条上沿。用新流程或 `reloadGuis all` 后另存新档清除冻结状态，不应继续下移磁盘 GUI。
  - 制作可交付的改造后测试档应从新流程执行同一条命令 `devmap game/medlabs skipall`；把 `skipall` 拆成独立命令会得到 `Unknown command 'skipall'` 并把存档落在红色改造过场中。也不要加载旧档后执行 `reloadGuis all` 再直接保存，实测会把护甲面板的可见状态冻结为隐藏。
  - zh_glow_norm 荧黑弃用（用户要求全体思源，嫌荧黑不够圆润）。
  - med1_textchange.gui 松散覆盖（savedata guis/maps/medlabs/）：可读侧 18 字母格改「神经细胞」（t_ar1-4，x=80/126/172/218）+「已植入」（t_ar10-12，x=400/446/492），subject 面板 t_sr1-3 改「实验体」（x=120/166/212），其余格 text 置空；**只改 text/rect 数值不动结构=存档安全**；用词与 chinese_guis.lang 的 str_200474/475（神经细胞/已植入）一致。10 个用字都已确认在 48 号 UI 字符集。
  - 效果：改造前终端全部外星符号（医疗站装饰读数/背景滚动文本实机确认），转译动画=外星符号逐字解码成思源中文。`_emptyname` 图像告警系原版遗留与此无关。
- **实机演示方法（可复用）**：拷贝原 gui 加 Desktop `onTime 1200 { resettime "anim" "0"; }` 存 savedata\q4base\guis\demo_textchange.gui（新路径不覆盖原件）→ cfg：loadGame rescue2054 → testGui guis/demo_textchange.gui → 每 wait 9（约150ms）screenshot 连拍 22 张 → PIL 合成 GIF/条带。产物：tmp\strogg_changeover_demo.gif、strogg_changeover_strip.png；演示文件 poc_strogg_demo.cfg 留存可复用。
- 第五轮字体 A/B（雅黑基线 vs 思源/HarmonyOS/MiSans Medium）对比图：tmp\font_ab_compare.png；候选字体文件在 tmp\fonts\candidates\。字幕 24 号档量化修复已部署（gui_smallFontLimit=0 + DLL r5_sub24，见 [[quake4-font-aspect-and-size]]）。
