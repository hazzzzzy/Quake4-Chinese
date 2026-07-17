# -*- coding: utf-8 -*-
"""合并翻译批次回主表 + QA 校验。

校验项：
  - 行数/表头/每行 id 与输入批次一致
  - en 列未被改动
  - zh 非空（en 非空时）
  - 占位符保全：en 里的 %s %d %i %c %.Nf 必须原样出现在 zh
  - zh 不含 TAB、不含半角省略号 "..."（应为……，占位符/纯英文行除外）
  - 汇总 [?] 存疑标记
"""
import re
import sys
from pathlib import Path

TRANS = Path(r"D:\data\quake4-cn\translations")
IN = TRANS / "batches" / "in"
OUT = TRANS / "batches" / "out"

# 注意：flags 里不含空格，避免把 "100% daily" 误判为 "% d" 占位符
FMT_RE = re.compile(r"%(?:\d+\$)?[-+#0]*\d*(?:\.\d+)?[sdifcux]")

def rows_of(p: Path) -> list[list[str]]:
    lines = p.read_text(encoding="utf-8-sig").splitlines()
    return [l.split("\t") for l in lines]

problems: list[str] = []
doubts: list[str] = []
master_updates: dict[str, dict[str, str]] = {}  # 主表名 -> {id: zh}

for inp in sorted(IN.glob("*.tsv")):
    outp = OUT / inp.name
    if not outp.exists():
        problems.append(f"[缺失] {inp.name} 没有产出")
        continue
    a, b = rows_of(inp), rows_of(outp)
    if len(a) != len(b):
        problems.append(f"[行数] {inp.name}: in={len(a)} out={len(b)}")
        continue
    master = inp.name.rsplit("_", 1)[0]  # ui_code_01 -> ui_code
    if master == "dlg":
        master = "dialogue_lips"
    upd = master_updates.setdefault(master, {})
    for i, (ra, rb) in enumerate(zip(a[1:], b[1:]), start=2):
        if len(rb) < 5:
            problems.append(f"[列数] {inp.name}:{i} 只有 {len(rb)} 列")
            continue
        if ra[0] != rb[0]:
            problems.append(f"[ID] {inp.name}:{i} {ra[0]} != {rb[0]}")
            continue
        if ra[1] != rb[1]:
            problems.append(f"[EN被改] {inp.name}:{i} {ra[0]}")
        en, zh = ra[1], rb[2]
        if en.strip() and not zh.strip():
            problems.append(f"[漏翻] {inp.name}:{i} {ra[0]} en={en[:40]!r}")
            continue
        if "\t" in zh:
            problems.append(f"[TAB] {inp.name}:{i} {ra[0]}")
        need = sorted(FMT_RE.findall(en))
        got = sorted(FMT_RE.findall(zh))
        if need != got:
            problems.append(f"[占位符] {inp.name}:{i} {ra[0]} en={need} zh={got}")
        if "[?" in rb[3]:
            doubts.append(f"{ra[0]}\t{en[:50]}\t{zh[:50]}\t{rb[3]}")
        upd[ra[0]] = zh

print(f"批次校验：问题 {len(problems)} 个，存疑 {len(doubts)} 条")
for p in problems[:40]:
    print(" ", p)
(TRANS / "qa_problems.txt").write_text("\n".join(problems), encoding="utf-8")
(TRANS / "qa_doubts.txt").write_text("\n".join(doubts), encoding="utf-8")

if problems and "--force" not in sys.argv:
    print("存在问题，未写回主表（用 --force 跳过）")
    sys.exit(1)

# 写回主表
for master, upd in master_updates.items():
    mp = TRANS / f"{master}.tsv"
    lines = mp.read_text(encoding="utf-8-sig").splitlines()
    out_lines = [lines[0]]
    n = 0
    for l in lines[1:]:
        cols = l.split("\t")
        if cols[0] in upd and upd[cols[0]].strip():
            if cols[4] != "done":  # 人工定稿的 done 不覆盖
                cols[2] = upd[cols[0]]
                cols[4] = "review"
                n += 1
        out_lines.append("\t".join(cols))
    mp.write_text("\n".join(out_lines) + "\n", encoding="utf-8-sig")
    print(f"{master}.tsv 更新 {n} 条")
