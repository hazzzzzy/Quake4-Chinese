# -*- coding: utf-8 -*-
"""生成 mainmenu.gui 中文适配覆盖版（松散写入 savedata\\q4base\\guis\\mainmenu.gui）。

背景（2026-07-18 用户反馈"设置页 高级音频设置/自动检测设置/高级设置 这三个
按钮偏上"）：这三个是 mainmenu.gui 里的**按钮式条目**（有 `set_sys_XXX` 容器
+ `set_sys_t_XXX` 文字层），文字 rect 与容器同 y、rect h=18 而容器 h=25，
CJK 视觉在按钮里紧贴顶部 → 需要 y+4 让文字视觉与容器中线对齐。

其他每行"label + choiceDef"式设置项（视频质量/屏幕尺寸/全屏 等）用户表示
"没问题"，本次不动。

存档兼容性：mainmenu.gui 不进存档（菜单不参与 savegame 序列化，与 hud.gui
r4 教训无关），rect 数值改动完全安全，也允许改 windowDef 结构——本补丁仍
保持纯数值改动作为最保守选项。

底稿：pak021 版 mainmenu.gui（1.4 补丁最终版，25270 行）。
"""
import sys
import zipfile
from pathlib import Path

SRC_PAK = Path(r"D:\data\Quake 4\q4base\pak021.pk4")
DST = Path(r"D:\data\idTech4Apx\savedata\q4base\guis\mainmenu.gui")

# (旧串, 新串, 期望出现次数)
# 三个按钮的 t_ 文字层 rect y+4，容器与角标 corner 不动（角标在按钮右侧，不与文字重叠）
EDITS = [
    ("rect\t262,231,328,18", "rect\t262,235,328,18", 1),   # set_sys_t_auto  自动检测设置
    ("rect\t262,262,328,18", "rect\t262,266,328,18", 1),   # set_sys_t_adv   高级设置
    ("rect\t262,366,328,18", "rect\t262,370,328,18", 1),   # set_sys_t_b9    高级音频设置
]


def main() -> int:
    # 原版 mainmenu.gui 内含非 UTF-8 字符（例如 ® 0xAE），按 bytes 处理保真替换
    with zipfile.ZipFile(SRC_PAK) as zf:
        data = zf.read("guis/mainmenu.gui")

    ok = True
    for old, new, expect in EDITS:
        old_b, new_b = old.encode("ascii"), new.encode("ascii")
        n = data.count(old_b)
        if n != expect:
            print(f"FAIL: {old!r} 出现 {n} 次（期望 {expect}）")
            ok = False
            continue
        data = data.replace(old_b, new_b)
        print(f"OK  : {old!r} -> {new!r} x{expect}")

    if not ok:
        return 1

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_bytes(data)
    print(f"\n写入 {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
