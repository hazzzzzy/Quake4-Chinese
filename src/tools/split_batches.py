# -*- coding: utf-8 -*-
"""把 UI 翻译总表切成翻译批次（每批约 300 条）。"""
from pathlib import Path

TRANS = Path(r"D:\data\quake4-cn\translations")
IN = TRANS / "batches" / "in"
IN.mkdir(parents=True, exist_ok=True)
(TRANS / "batches" / "out").mkdir(parents=True, exist_ok=True)

BATCH = 300
for name in ("ui_code", "ui_guis", "ui_maps", "ui_mappack"):
    lines = (TRANS / f"{name}.tsv").read_text(encoding="utf-8-sig").splitlines()
    header, rows = lines[0], lines[1:]
    for i in range(0, len(rows), BATCH):
        chunk = rows[i:i + BATCH]
        p = IN / f"{name}_{i // BATCH + 1:02d}.tsv"
        p.write_text(header + "\n" + "\n".join(chunk) + "\n", encoding="utf-8-sig")
        print(p.name, len(chunk))
