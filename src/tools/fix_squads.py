# -*- coding: utf-8 -*-
"""小队名改为全中文译名（用户 2026-07-16 拍板）。"""
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
TRANS = REPOSITORY / "src" / "translations"

SQUADS = {
    "Rhino": "犀牛", "Scorpion": "天蝎", "Badger": "猛獾", "Condor": "神鹰",
    "Kodiak": "棕熊", "Raven": "渡鸦", "Viper": "毒蛇", "Wolf": "野狼",
    "Eagle": "雄鹰", "Cobra": "眼镜蛇", "Warthog": "疣猪",
}

for tsv in ("ui_code.tsv", "ui_guis.tsv", "ui_maps.tsv", "ui_mappack.tsv"):
    p = TRANS / tsv
    lines = p.read_text(encoding="utf-8-sig").splitlines()
    out, n = [lines[0]], 0
    for l in lines[1:]:
        cols = l.split("\t")
        if len(cols) >= 3 and cols[2]:
            zh = cols[2]
            for en, cn in SQUADS.items():
                zh = zh.replace(f"{en} 小队", f"{cn}小队")
                zh = zh.replace(f"{en} Squad", f"{cn}小队")
                zh = zh.replace(f"{en}小队", f"{cn}小队")
            if zh != cols[2]:
                cols[2] = zh
                n += 1
        out.append("\t".join(cols))
    p.write_text("\n".join(out) + "\n", encoding="utf-8-sig")
    print(f"{tsv}: 修订 {n} 条")
