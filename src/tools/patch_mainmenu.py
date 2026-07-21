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

SRC_PAK = Path(r"D:\Quake 4\q4base\pak021.pk4")
DST = Path(r"D:\PROJECT\quake4-translate-subtitle\savedata\q4base\guis\mainmenu.gui")

# (旧串, 新串, 期望出现次数)
# 三个按钮的 t_ 文字层 rect y+4，容器与角标 corner 不动（角标在按钮右侧，不与文字重叠）
EDITS = [
    ("rect\t262,231,328,18", "rect\t262,235,328,18", 1),   # set_sys_t_auto  自动检测设置
    ("rect\t262,262,328,18", "rect\t262,266,328,18", 1),   # set_sys_t_adv   高级设置
    ("rect\t262,366,328,18", "rect\t262,370,328,18", 1),   # set_sys_t_b9    高级音频设置
]

# 制作人员名单硬编码职位汉化（2026-07-18 用户反馈"制作人员名单的职位也汉化一下"）
# credits 段（line 8543-17150）内 text 字段直接是英文硬编码，不走 #str_id。
# 每个职位出现 2-4 次（背景/阴影双层或 SP+MP 分组）；用完整 text 引号包裹匹配
# 避免"Motion Capture" 误伤"Motion Capture Lead"等超集。含"人名 - 兼任"格式
# 保留人名，只翻译连字符右侧职位。人名/工作室名（Splash Damage/Womb Music
# /id Software 等）不译。
CREDITS_EDITS = [
    # 长字符串优先（子串安全兜底）
    ("Additional Internal Quality Assurance", "追加内部品保"),
    ("Voice Over Recording, Editing and Post", "配音录制、剪辑与后期"),
    ("Fred Hooper - Assistant Art Lead", "Fred Hooper - 副美术组长"),
    ("Michael Pleva - Assistant Animation Lead", "Michael Pleva - 副动画组长"),
    ("Squirrel Eiserloh - Ritual code", "Squirrel Eiserloh - Ritual 代码"),
    ("Director of Product Development", "产品开发总监"),
    ("Casting and Voice Direction", "选角与配音指导"),
    ("Dan Hay - Cinematic Consultant", "Dan Hay - 过场顾问"),
    ("Theme for Quake4 Composed by", "Quake 4 主题曲作曲"),
    ("Theme for Quake4 Produced by", "Quake 4 主题曲制作"),
    ("Todd Rose - Ritual levels", "Todd Rose - Ritual 关卡"),
    ("Eric Fowler - Ritual code", "Eric Fowler - Ritual 代码"),
    ("Additional Motion Capture", "追加动作捕捉"),
    ("Internal Quality Assurance", "内部品保"),
    ("QUAKE II Xbox Programming", "QUAKE II Xbox 编程"),
    ("Carlo Vogelsang - Creative", "Carlo Vogelsang - 创意"),
    ("Additional Programming", "追加编程"),
    ("Production Coordinator", "制作协调"),
    ("Motion Capture Lead", "动作捕捉组长"),
    ("Art/Animation Lead", "美术/动画组长"),
    ("Additional Animation", "追加动画"),
    ("Executive Producer", "执行制作人"),
    ("Associate Producer", "副制作人"),
    ("Bidwell, Announcer", "Bidwell（播音员）"),
    ("Computer, Pilot VO", "电脑/飞行员配音"),
    ("Programming Leads", "编程组长"),
    ("Studio Head", "工作室负责人"),
    ("Line Producer", "现场制作人"),
    ("Motion Capture", "动作捕捉"),
    ("Additional Art", "追加美术"),
    ("Special Thanks", "特别鸣谢"),
    ("Level Design", "关卡设计"),
    ("Sound Design", "音效设计"),
    ("Design Lead", "设计组长"),
    ("Audio Leads", "音频组长"),
    ("Project Lead", "项目主管"),
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

    # credits 段：完整 text 引号包裹匹配（子串安全）；中文写 UTF-8 bytes
    total_credits = 0
    for en, zh in CREDITS_EDITS:
        old_b = f'text\t"{en}"'.encode("ascii")
        new_b = f'text\t"{zh}"'.encode("utf-8")
        n = data.count(old_b)
        if n == 0:
            print(f"WARN: credits {en!r} 未匹配（可能已被替换或字符串变化）")
            continue
        data = data.replace(old_b, new_b)
        total_credits += n
        print(f"OK  : credits {en!r} -> {zh!r} x{n}")
    print(f"credits: {len(CREDITS_EDITS)} 条职位，共替换 {total_credits} 次")

    if not ok:
        return 1

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_bytes(data)
    print(f"\n写入 {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
