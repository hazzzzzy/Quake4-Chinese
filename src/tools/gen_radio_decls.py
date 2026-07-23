# -*- coding: utf-8 -*-
"""从 translations/radio_chatter.tsv 生成无线电台词 lipsync decl（松散覆盖）。

背景：全游戏 336 条 func_radiochatter 台词中 252 条原版无 lipsync decl
（纯电台线不做口型，Raven 未建），q4game.dll 的无线电字幕挂钩因此拿不到
文本。本工具为其补最小 decl（description=英文原文，text=#str_38xxxx），
译文由 build_lang.py 并入 chinese_lips.lang。

decl 名与原版不冲突（生成对象就是"原版没有"的名单）；decl 不进存档，
增删安全。英文原文来源：.sndshd 的 description 字段（见 build_radio_tsv3.py）。
"""
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
TSV = REPOSITORY / "src" / "translations" / "radio_chatter.tsv"
OUT = REPOSITORY / "savedata" / "q4base" / "lipsync" / "zz_chinese_radio.lipsync"
OUT.parent.mkdir(parents=True, exist_ok=True)

lines = TSV.read_text(encoding="utf-8-sig").splitlines()
blocks = ["// 汉化项目自建：无线电台词最小 lipsync decl（原版缺失，仅供字幕取文本）",
          "// 由 tools/gen_radio_decls.py 生成，勿手改", ""]
n = 0
seen = set()
for l in lines[1:]:
    cols = l.split("\t")
    if len(cols) < 5 or not cols[0].startswith("str_"):
        continue
    sid, snd, en = cols[0], cols[1], cols[3].replace('"', "'")
    # 同一声音可被多张地图引用（如 vo_2_1_2_220_1 在 medlabs 与 walker），decl 只出一份
    if snd in seen:
        continue
    seen.add(snd)
    blocks.append(f'lipSync {snd}\n{{\n\tdescription\t"{en}"\n\ttext\t\t"#{sid}"\n}}\n')
    n += 1

OUT.write_text("\n".join(blocks), encoding="utf-8")
print(f"{n} 条 decl → {OUT}")
