# -*- coding: utf-8 -*-
"""从玩家自己的原版 Quake 4（pak001.pk4 + pak021.pk4）现场补齐版权敏感物：

  1. fonts/chinese/strogg_{12,24,48}.{fontdat,tga}     — 原版外星文字体直通
  2. guis/hud.gui                                       — 无线电两行 rect 数值补丁
  3. guis/maps/medlabs/med1_textchange.gui              — 神经细胞植入转译动画中文化
  4. zzz_vo_chinese_alias.pk4（含 sound/vo_chinese/*）  — 中文语音路径别名（英文原声）

这些资产因涉及 Raven Software / id Software 版权，不能随汉化补丁一起分发；
玩家运行本脚本从自己合法拥有的原版数据里现场生成到 savedata 树，
不修改玩家的原版游戏目录、不复制原始音频到别处，仅在 zip 内改路径。

用法（Windows）：
  python build_dist_extras.py --game-dir "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Quake 4"

或由 dist\\postinstall.cmd 自动调用（会读取「启动汉化版.cmd」里的 GAME_DIR）。
"""
import argparse
import io
import os
import shutil
import sys
import zipfile
from pathlib import Path


# ---- med1_textchange.gui 补丁：按 windowDef 名字定位，避免行号/上下文歧义 ----
# 可读侧（r_strogg 字体格）字母 → 中文；不用到的格 text 置空；rect x 平移让中文居中。
# 依据：docs/localization-guide.md § Strogg 转译动画机制
MEDLAB_EDITS = {
    "t_ar1":  {"x": 80,  "text": "神"},
    "t_ar2":  {"x": 126, "text": "经"},
    "t_ar3":  {"x": 172, "text": "细"},
    "t_ar4":  {"x": 218, "text": "胞"},
    "t_ar5":  {"text": ""},
    "t_ar6":  {"text": ""},
    "t_ar7":  {"text": ""},
    "t_ar8":  {"text": ""},
    "t_ar9":  {"text": ""},
    "t_ar10": {"x": 400, "text": "已"},
    "t_ar11": {"x": 446, "text": "植"},
    "t_ar12": {"x": 492, "text": "入"},
    "t_ar13": {"text": ""},
    "t_ar14": {"text": ""},
    "t_ar15": {"text": ""},
    "t_ar16": {"text": ""},
    "t_ar17": {"text": ""},
    "t_ar18": {"text": ""},
    "t_sr1":  {"x": 120, "text": "实"},
    "t_sr2":  {"x": 166, "text": "验"},
    "t_sr3":  {"x": 212, "text": "体"},
    "t_sr4":  {"text": ""},
    "t_sr5":  {"text": ""},
    "t_sr6":  {"text": ""},
    "t_sr7":  {"text": ""},
}


def patch_mainmenu_gui(data: bytes) -> bytes:
    """mainmenu.gui 补丁：三按钮 rect y+4 + credits 段职位汉化（2026-07-18）。

    - 设置页 set_sys_t_auto/adv/b9 三按钮文字 rect y+4 让 CJK 视觉与容器中线对齐
    - credits 段（line 8543-17150）内 text 字段直接是英文硬编码不走 #str_id，
      共 36 条职位翻译（用完整 text 引号包裹匹配避免 "Motion Capture" 误伤
      "Motion Capture Lead" 等超集）；人名/工作室名不译

    按 bytes 处理：原版 mainmenu.gui 含非 UTF-8 字符（® 0xAE）；rect 数值全 ASCII。
    菜单 gui 不参与存档序列化，与 hud.gui r4 存档兼容约束无关。
    """
    edits = [
        (b"rect\t262,231,328,18", b"rect\t262,235,328,18"),  # set_sys_t_auto
        (b"rect\t262,262,328,18", b"rect\t262,266,328,18"),  # set_sys_t_adv
        (b"rect\t262,366,328,18", b"rect\t262,370,328,18"),  # set_sys_t_b9
    ]
    for old, new in edits:
        assert data.count(old) == 1, f"mainmenu.gui 找不到唯一匹配：{old!r}"
        data = data.replace(old, new)

    # credits 段职位汉化（长串在前避免子串误伤；例 Motion Capture Lead 先于 Motion Capture）
    credits_edits = [
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
    for en, zh in credits_edits:
        old_b = f'text\t"{en}"'.encode("ascii")
        new_b = f'text\t"{zh}"'.encode("utf-8")
        if old_b in data:
            data = data.replace(old_b, new_b)
    return data


def patch_hud_gui(text: str) -> str:
    """无线电两行 rect 补丁：右移出波形图标 + 拉开两行防重叠。

    只做纯数值替换、不动 windowDef 结构 → 与原版结构存档兼容（避免读档崩溃，
    见 docs/localization-guide.md § 存档兼容性）。
    """
    edits = [
        ("rect\t545,6,81,12",  "rect\t557,4,69,13"),   # t_radio1
        ("rect\t545,13,81,12", "rect\t557,17,69,13"),  # t_radio2
        ("rect\t0,42,640,40",  "rect\t0,48,640,40"),   # ws_name 切枪武器名下移
        # 关卡末尾大门 EXIT 标签重定向 str_200013 -> str_200379 (撤离，避免误伤主菜单)
        ('text\t"#str_200013"', 'text\t"#str_200379"'),  # p_exit_text
        # HUD 大数字底裁修复（chain_24 ASCII drop=2 后位图底端卡 rect 底边）
        ("rect\t44,429,49,26",  "rect\t44,429,49,29"),   # ammo_amount
        ("rect\t82,429,49,26",  "rect\t82,429,49,29"),   # ammo_amount_nc
        ("rect\t256,429,52,26", "rect\t256,429,52,29"),  # health_amount
        ("rect\t392,429,52,26", "rect\t392,429,52,29"),  # armor_amount
        ("rect\t81,429,50,26",  "rect\t81,429,50,29"),   # ammo_amount_mp
        ("rect\t258,429,50,26", "rect\t258,429,50,29"),  # health_amount_mp
        ("rect\t394,429,50,26", "rect\t394,429,50,29"),  # armor_amount_mp
    ]
    for old, new in edits:
        assert text.count(old) == 1, f"hud.gui 找不到唯一匹配：{old!r}"
        text = text.replace(old, new)
    return text


def patch_medlab_gui(text: str) -> str:
    """按 windowDef 名字定位（t_ar1..18 / t_sr1..7），替换 rect x 与 text 字段。"""
    lines = text.splitlines(keepends=True)
    i = 0
    applied = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("windowDef "):
            name = stripped.split()[1]
            if name in MEDLAB_EDITS:
                edit = MEDLAB_EDITS[name]
                j = i + 1
                while j < len(lines) and lines[j].strip() != "}":
                    ln = lines[j]
                    ls = ln.strip()
                    if "x" in edit and ls.startswith("rect\t"):
                        # rect	18,351,50,59 → 保留缩进/前缀，只换 x
                        prefix = ln[: ln.index("rect")]
                        parts = ls.split()[1].split(",")
                        parts[0] = str(edit["x"])
                        eol = ln[-2:] if ln.endswith("\r\n") else ln[-1:]
                        lines[j] = f'{prefix}rect\t{",".join(parts)}{eol}'
                    if "text" in edit and ls.startswith("text\t\""):
                        prefix = ln[: ln.index("text")]
                        eol = ln[-2:] if ln.endswith("\r\n") else ln[-1:]
                        lines[j] = f'{prefix}text\t"{edit["text"]}"{eol}'
                    j += 1
                applied += 1
                i = j
        i += 1
    assert applied == len(MEDLAB_EDITS), \
        f"medlab 补丁未完全应用：{applied}/{len(MEDLAB_EDITS)}"
    return "".join(lines)


def write_utf8(dst: Path, text: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(text.encode("utf-8"))


def extract_strogg_fonts(pak021: Path, out_fonts: Path) -> None:
    """从 pak021 提取 fonts/english/strogg_{12,24,48}.{fontdat,tga}，
    改名为 fonts/chinese/strogg_* 放入 savedata（松散文件）。"""
    with zipfile.ZipFile(pak021) as zf:
        for name in zf.namelist():
            if name.startswith("fonts/english/strogg_") and \
               name.endswith((".fontdat", ".tga")):
                data = zf.read(name)
                dst = out_fonts / Path(name).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(data)


def build_vo_alias_pk4(pak001: Path, out_pk4: Path) -> int:
    """把 pak001 里 sound/vo_english/*.* 全部改路径为 sound/vo_chinese/*.* 打进新 pk4。

    使用 zipfile 的 ZipInfo 保留原压缩方法（stored/deflate）+ 原压缩数据流复制，
    避免解压→重压的耗时（约 3-5 分钟 vs 秒级）。
    """
    count = 0
    with zipfile.ZipFile(pak001) as src, \
         zipfile.ZipFile(out_pk4, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            if info.filename.startswith("sound/vo_english/") and not info.is_dir():
                data = src.read(info)  # 解压→重压（65MB 的音频不用 stored 也可接受）
                new_info = zipfile.ZipInfo(
                    info.filename.replace("sound/vo_english/", "sound/vo_chinese/", 1))
                new_info.compress_type = info.compress_type
                new_info.date_time = info.date_time
                dst.writestr(new_info, data)
                count += 1
    return count


def extract_and_patch(pak: Path, entry: str, patch_fn, out_file: Path) -> None:
    with zipfile.ZipFile(pak) as zf:
        raw = zf.read(entry).decode("utf-8")
    write_utf8(out_file, patch_fn(raw))


def main() -> int:
    ap = argparse.ArgumentParser(description="补齐 Quake 4 汉化版权敏感资产")
    ap.add_argument("--game-dir", required=True,
                    help="原版 Quake 4 安装目录（包含 q4base 子目录）")
    ap.add_argument("--out", required=True,
                    help="补齐物输出根（一般 = dist\\savedata\\q4base）")
    ap.add_argument("--skip-vo", action="store_true",
                    help="跳过语音别名 pk4（调试用；正常玩家务必生成）")
    args = ap.parse_args()

    game_dir = Path(args.game_dir)
    q4base = game_dir / "q4base"
    pak001 = q4base / "pak001.pk4"
    pak021 = q4base / "pak021.pk4"
    for p in (pak001, pak021):
        if not p.exists():
            print(f"[错误] 找不到 {p}", file=sys.stderr)
            print("请检查 --game-dir 是否指向 Quake 4 安装目录 (1.4.2 补丁必需)。")
            return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print("[1/4] 提取 Strogg 外星文字体（pak021 → fonts/chinese/strogg_*）...", flush=True)
    extract_strogg_fonts(pak021, out / "fonts" / "chinese")

    print("[2/4] 补丁 hud.gui（pak021 → guis/hud.gui，无线电两行 rect 数值）...", flush=True)
    extract_and_patch(pak021, "guis/hud.gui",
                      patch_hud_gui, out / "guis" / "hud.gui")

    print("[2b] 补丁 mainmenu.gui（pak021 → guis/mainmenu.gui，设置页 3 按钮 rect y+4）...", flush=True)
    with zipfile.ZipFile(pak021) as zf:
        mm = zf.read("guis/mainmenu.gui")
    mm_out = out / "guis" / "mainmenu.gui"
    mm_out.parent.mkdir(parents=True, exist_ok=True)
    mm_out.write_bytes(patch_mainmenu_gui(mm))

    print("[3/4] 补丁 med1_textchange.gui（pak001 → 神经细胞植入转译动画中文化）...", flush=True)
    extract_and_patch(pak001, "guis/maps/medlabs/med1_textchange.gui",
                      patch_medlab_gui,
                      out / "guis" / "maps" / "medlabs" / "med1_textchange.gui")

    if args.skip_vo:
        print("[4/4] 已跳过语音别名 pk4（--skip-vo）")
    else:
        pk4 = out / "zzz_vo_chinese_alias.pk4"
        print(f"[4/4] 生成中文语音路径别名 pk4（pak001 vo_english → vo_chinese, {pk4.name}，约需 1-3 分钟）...", flush=True)
        n = build_vo_alias_pk4(pak001, pk4)
        print(f"      OK：{n} 个音频文件已别名到 sound/vo_chinese/")

    print()
    print("全部补齐物已就位；现在可以双击「启动汉化版.cmd」进游戏了。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
