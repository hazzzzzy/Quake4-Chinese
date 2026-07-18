# -*- coding: utf-8 -*-
"""生成 hud.gui 中文适配覆盖版。

背景：中文全字库 fontdat 的 maxHeight 比英文原版大（chain 24pt: 28 vs 21），
引擎按 maxHeight 定文本基线，导致 HUD 大数字整体下移 7 虚拟像素、底部被
窗口 rect 裁切；marine 12pt 行高从 8.8 涨到 12px，"传入/通讯"两行重叠。
对策：数字窗口 y-7/h+7（0.5 档）、y-5/h+5（0.32 档）；无线电两行拉开到 4/17
并右移出波形图标（x 545→557）。

底稿必须用 pak021 版（1.4 补丁最终版，运行时实际生效的那份）——
存档会按 GUI 源文件结构逐窗口序列化 HUD 状态，覆盖版与存档时的结构
不一致会导致读档时状态流错位、内存踩坏、概率性崩溃（2026-07-16 已实证：
pak001 底稿的覆盖使所有原版结构存档 100% 读档崩溃）。
只允许改数值（rect/textscale 等），禁止增删 windowDef/脚本/变量。
"""
import sys

SRC = r"D:\data\quake4-cn\assets\hud_pak021_stock.gui"
DST = r"D:\data\idTech4Apx\savedata\q4base\guis\hud.gui"

# (旧串, 新串, 期望出现次数)
# 2026-07-17 自研字体导出器（export_font.py）上线后：新字库基线与英文原版
# 差 ≤1px（chain24 Δ=+1），HUD 数字不再被裁，数字窗口的 y-7/h+7 补偿全部撤销，
# 只保留无线电两行的修正。
# 可交互 bracket_text 字号加大（多行匹配保证唯一定位）——2026-07-18 用户反馈
# "可交互面板文字显示不全"根因：textscale .25 走 marine_24 useScale 0.5，屏幕
# 字号仅约 20px；原版 INTERACTIVE 视觉大字。textscale .4 让 CJK 视觉与原版接近。
EDITS_MULTILINE = [
    # SRC=hud_pak021_stock.gui 是 CRLF；用 \r\n 匹配
    (
        'text\t"#str_200277"\r\n\t\t\tfont\t"fonts/marine"\r\n\t\t\ttextalign\t1\r\n\t\t\tforecolor\t0.686,0.870,0.564,"brackets::alpha"\r\n\t\t\ttextscale\t.25',
        'text\t"#str_200277"\r\n\t\t\tfont\t"fonts/marine"\r\n\t\t\ttextalign\t1\r\n\t\t\tforecolor\t0.686,0.870,0.564,"brackets::alpha"\r\n\t\t\ttextscale\t.4',
        1,
    ),
]

EDITS = [
    # 无线电"传入/通讯"两行（marine 12pt，useScale=0.8，行高 12px）
    # y 拉开防重叠；x 右移出波形图标（图标 rect 513,7,41,25，右缘 554）
    ("rect\t545,6,81,12",   "rect\t557,4,69,13",   1),   # t_radio1
    ("rect\t545,13,81,12",  "rect\t557,17,69,13",  1),   # t_radio2
    # 切枪武器名 ws_name（用户 2026-07-18 反馈"向下移一点"）
    # 原 rect(0,42,640,40) + textscale 0.25 走 marine_24（gui_smallFontLimit=0），
    # 墨迹中线 y=49、rect 中线 y=62 → 视觉偏上 13 虚拟 px（≈15 屏幕像素）；
    # y 42→48 下移 6 虚拟 px（≈7 屏幕像素），并避开 ws_weapon0-10 图标 y=20-46 的重叠。
    ("rect\t0,42,640,40",   "rect\t0,48,640,40",   1),   # ws_name
    # 关卡末尾大门"EXIT"标签重定向到 str_200379 撤离（2026-07-18 用户反馈"EXIT
    # 翻译为退出了，应该是撤离"）。str_200013 EXIT 同时被主菜单退出按钮引用，
    # 直接改译文会误伤主菜单。改成引用 str_200379（关卡语境的 exit，v1.0.5
    # 已翻"撤离"）。仅 hud.gui 里 p_exit_level.p_exit_text 一处引用。
    ('text\t"#str_200013"', 'text\t"#str_200379"',    1),   # p_exit_text
    # 无线电背景条 radio_backbar rect 缩窄贴合中文（2026-07-18 用户反馈"传入
    # 通讯 4 字比原版 INCOMING TRANSMISSION 20 字短很多，背景条右侧留白"）。
    # 原 rect(520,5,113,28) 覆盖英文长度；中文 2 字/行 x=557 宽 69，缩窄背景
    # 到 x=556 宽 72（贴合 t_radio1/2 文本 rect 各留 3px 边距）。
    ("rect\t520,5,113,28",  "rect\t556,5,72,28",      1),   # radio_backbar
    # quicksave_msg 位置下移避开准星区 bracket_text（2026-07-18 用户反馈"可
    # 交互被游戏已保存遮挡"）。y 64→110 移到屏幕上方 1/4 位置，让"游戏已保存"
    # 与常见玩家瞄准高度（屏幕中央 y=240）之间保留净空。
    ("rect\t0,64,640,20",   "rect\t0,110,640,20",     1),   # quicksave_msg
    # HUD 大数字底裁修复已随 v1.0.9 chain 家族原版数字方案撤销：chain 家族现在
    # 基础段用原版 fontdat/tga，数字度量与原版 100% 一致，rect(h=26) 已够，
    # 不再需要 h+3 补丁。参见 export_font.py 里 use_original_base 分支。
]

with open(SRC, "rb") as f:
    data = f.read().decode("utf-8", errors="strict")

ok = True
for old, new, expect in EDITS + EDITS_MULTILINE:
    n = data.count(old)
    if n != expect:
        print(f"FAIL: '{old[:60]}...' 出现 {n} 次（期望 {expect}）")
        ok = False
        continue
    data = data.replace(old, new)
    tag = old[:50].replace("\n", "\\n").replace("\t", "\\t")
    print(f"OK  : {tag}... -> ... x{expect}")

if not ok:
    sys.exit(1)

with open(DST, "wb") as f:
    f.write(data.encode("utf-8"))
print(f"\n写入 {DST}")
