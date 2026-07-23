# -*- coding: utf-8 -*-
"""只更新 dialogue_lips.tsv 的 context 列（模糊匹配提升说话人覆盖率）。
不触碰其他列（zh 可能已有翻译）。同时切分对白批次。
"""
import glob
import re
import zipfile
from collections import defaultdict
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
Q4BASE = Path(r"D:\Quake 4\q4base")
TRANS = REPOSITORY / "src" / "translations"

SND_RE = re.compile(r'sound\s+(\S+)\s*\{([^}]*)\}', re.S)
DESC_RE = re.compile(r'description\s+"((?:[^"\\]|\\.)*)"')
VOPATH_RE = re.compile(r'(sound/vo/\S+)')

def norm(s: str) -> str:
    # 模糊归一：只留字母数字，小写
    return re.sub(r"[^a-z0-9]", "", s.lower())

# 1) 读 lips 主表
p = TRANS / "dialogue_lips.tsv"
lines = p.read_text(encoding="utf-8-sig").splitlines()
rows = [l.split("\t") for l in lines]

text2rows = defaultdict(list)
for i, r in enumerate(rows[1:], start=1):
    text2rows[norm(r[1])].append(i)

# 2) 扫 sndshd
matched = {}
for f in sorted(glob.glob(str(Q4BASE / "*.pk4"))):
    z = zipfile.ZipFile(f)
    for n in z.namelist():
        if n.startswith("sound/") and n.endswith(".sndshd") and "vo" in n.lower():
            speaker = re.sub(r"_vo\.sndshd$", "", n.rsplit("/", 1)[-1], flags=re.I)
            content = z.read(n).decode("cp1252", "replace")
            for m in SND_RE.finditer(content):
                body = m.group(2)
                dm = DESC_RE.search(body)
                pm = VOPATH_RE.search(body)
                if not dm:
                    continue
                key = norm(dm.group(1))
                if not key:
                    continue
                level = pm.group(1).split("/")[2] if pm and pm.group(1).count("/") >= 3 else ""
                for ri in text2rows.get(key, []):
                    if ri not in matched:
                        matched[ri] = f"{speaker} @ {level}"

# 3) 写回 context 列（第 4 列）
n_upd = 0
for ri, ctx in matched.items():
    if len(rows[ri]) >= 5 and not rows[ri][3]:
        rows[ri][3] = ctx
        n_upd += 1
    elif len(rows[ri]) >= 5:
        rows[ri][3] = ctx
        n_upd += 1
p.write_text("\n".join("\t".join(r) for r in rows) + "\n", encoding="utf-8-sig")
have = sum(1 for r in rows[1:] if len(r) >= 4 and r[3])
print(f"说话人上下文覆盖：{have}/{len(rows)-1}")

# 4) 切批（500/批）
IN = TRANS / "batches" / "in"
IN.mkdir(parents=True, exist_ok=True)
BATCH = 500
data = lines[0]
body = ["\t".join(r) for r in rows[1:]]
for i in range(0, len(body), BATCH):
    chunk = body[i:i + BATCH]
    bp = IN / f"dlg_{i // BATCH + 1:02d}.tsv"
    bp.write_text(rows[0][0] and lines[0] + "\n" + "\n".join(chunk) + "\n", encoding="utf-8-sig")
    print(bp.name, len(chunk))
