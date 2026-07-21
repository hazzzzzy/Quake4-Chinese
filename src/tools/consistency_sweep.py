# -*- coding: utf-8 -*-
"""跨批次一致性清扫：统一 squib 译名、检查 Rhodes 性别用语等。"""
import re
from pathlib import Path

p = Path(r"D:\PROJECT\quake4-translate-subtitle\Quake4-Chinese\src\translations\dialogue_lips.tsv")
lines = p.read_text(encoding="utf-8-sig").splitlines()

fixes = 0
rhodes_flags = []
out = [lines[0]]
for l in lines[1:]:
    cols = l.split("\t")
    if len(cols) >= 5 and cols[2]:
        zh = cols[2]
        # squib 统一为「杂碎」（dlg_03 用了「铁皮怪」）
        if "铁皮怪" in zh:
            zh = zh.replace("铁皮怪", "杂碎")
        # Rhodes 是男性：台词提及 Rhodes 且用「她」的行标记人工复核
        if "Rhodes" in cols[1] and "她" in zh:
            rhodes_flags.append(cols[0])
        if zh != cols[2]:
            cols[2] = zh
            fixes += 1
    out.append("\t".join(cols))
p.write_text("\n".join(out) + "\n", encoding="utf-8-sig")
print(f"squib 统一修正 {fixes} 条")
print(f"Rhodes+她 需人工复核: {len(rhodes_flags)} 条 {rhodes_flags[:10]}")
