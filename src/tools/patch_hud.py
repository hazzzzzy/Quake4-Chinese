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
    # HUD 大数字底裁修复（2026-07-18 用户反馈"生命值数字被吞 10%"）
    # v1.0.6 让 chain_24 ASCII 加 drop=2 → 数字位图 h 从 19→21，位图底端 y=455
    # 卡在原 rect(y=429, h=26) 底 455 边界，视觉底 10% 被裁。h 26→29 (+3 名义 px
    # 留 1 px 冗余)；y 与 windowDef 结构不变，存档兼容。
    ("rect\t44,429,49,26",  "rect\t44,429,49,29",  1),   # ammo_amount   SP 弹药
    ("rect\t82,429,49,26",  "rect\t82,429,49,29",  1),   # ammo_amount_nc SP 无夹弹药
    ("rect\t256,429,52,26", "rect\t256,429,52,29", 1),   # health_amount SP 血量（用户反馈）
    ("rect\t392,429,52,26", "rect\t392,429,52,29", 1),   # armor_amount  SP 护甲
    ("rect\t81,429,50,26",  "rect\t81,429,50,29",  1),   # ammo_amount_mp
    ("rect\t258,429,50,26", "rect\t258,429,50,29", 1),   # health_amount_mp
    ("rect\t394,429,50,26", "rect\t394,429,50,29", 1),   # armor_amount_mp
]

with open(SRC, "rb") as f:
    data = f.read().decode("utf-8", errors="strict")

ok = True
for old, new, expect in EDITS:
    n = data.count(old)
    if n != expect:
        print(f"FAIL: '{old}' 出现 {n} 次（期望 {expect}）")
        ok = False
        continue
    data = data.replace(old, new)
    print(f"OK  : {old!r} -> {new!r} x{expect}")

if not ok:
    sys.exit(1)

with open(DST, "wb") as f:
    f.write(data.encode("utf-8"))
print(f"\n写入 {DST}")
