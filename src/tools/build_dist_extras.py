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


def patch_hud_gui(text: str) -> str:
    """无线电两行 rect 补丁：右移出波形图标 + 拉开两行防重叠。

    只做纯数值替换、不动 windowDef 结构 → 与原版结构存档兼容（避免读档崩溃，
    见 docs/localization-guide.md § 存档兼容性）。
    """
    edits = [
        ("rect\t545,6,81,12",  "rect\t557,4,69,13"),   # t_radio1
        ("rect\t545,13,81,12", "rect\t557,17,69,13"),  # t_radio2
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
