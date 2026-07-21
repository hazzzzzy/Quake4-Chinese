# -*- coding: utf-8 -*-
"""生成翻译总表（TSV）与对白说话人上下文映射。

产出：
  translations/ui_code.tsv / ui_guis.tsv / ui_maps.tsv / ui_mappack.tsv
  translations/dialogue_lips.tsv        （含 speaker/level 上下文列）
  translations/vo_context.json          （str_id -> 声音路径/说话人/关卡 完整映射）

TSV 列：id <TAB> en <TAB> zh <TAB> context <TAB> status
status: todo | done | review
"""
import glob
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path

Q4BASE = Path(r"D:\Quake 4\q4base")
TRANS = Path(r"D:\PROJECT\quake4-translate-subtitle\Quake4-Chinese\src\translations")
TRANS.mkdir(parents=True, exist_ok=True)

LINE_RE = re.compile(r'^(\s*)"(#str_\d+)"(\s+)"(.*)"(\s*)$')

# PoC 已定稿的 10 条
DONE = {
    "#str_200000": "新游戏",
    "#str_200001": "读取存档",
    "#str_200003": "保存游戏",
    "#str_200009": "设置",
    "#str_200012": "制作人员名单",
    "#str_200013": "退出",
    "#str_200322": "退出 Quake 4",
    "#str_200938": "载入中……",
    "#str_104343": "正在载入……",
    "#str_104350": "正在载入游戏……",
}

# ---- 1. 合并 lang（同 build_chinese_assets 逻辑） ---------------------------
merged: dict[str, dict[str, str]] = {}
for f in sorted(glob.glob(str(Q4BASE / "*.pk4"))):
    z = zipfile.ZipFile(f)
    for n in z.namelist():
        if n.startswith("strings/english") and n.endswith(".lang"):
            d = merged.setdefault(n.rsplit("/", 1)[-1], {})
            for line in z.read(n).decode("cp1252").splitlines():
                m = LINE_RE.match(line)
                if m:
                    d[m.group(2)] = m.group(4)

# ---- 2. VO 说话人上下文：解析全部 sndshd 的 description ---------------------
SND_RE = re.compile(
    r'sound\s+(\S+)\s*\{([^}]*)\}', re.S)
DESC_RE = re.compile(r'description\s+"((?:[^"\\]|\\.)*)"')
VOPATH_RE = re.compile(r'(sound/vo/\S+)')

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()

# lips 文本 -> [str_id]（一句可能多 id）
lips = merged.get("english_lips.lang", {})
text2ids = defaultdict(list)
for k, v in lips.items():
    text2ids[norm(v)].append(k)

vo_ctx: dict[str, dict] = {}   # str_id -> {speaker, level, sound, shader}
unmatched = []
for f in sorted(glob.glob(str(Q4BASE / "*.pk4"))):
    z = zipfile.ZipFile(f)
    for n in z.namelist():
        if n.startswith("sound/") and n.endswith(".sndshd") and "vo" in n.lower():
            speaker = re.sub(r"_vo\.sndshd$", "", n.rsplit("/", 1)[-1], flags=re.I)
            content = z.read(n).decode("cp1252", "replace")
            for m in SND_RE.finditer(content):
                shader, body = m.group(1), m.group(2)
                dm = DESC_RE.search(body)
                pm = VOPATH_RE.search(body)
                if not dm:
                    continue
                desc = dm.group(1).replace('\\"', '"')
                sound = pm.group(1) if pm else ""
                level = sound.split("/")[2] if sound.count("/") >= 3 else ""
                ids = text2ids.get(norm(desc), [])
                if ids:
                    for i in ids:
                        # 不覆盖已有（首个 shader 为准），冲突记录
                        if i not in vo_ctx:
                            vo_ctx[i] = {"speaker": speaker, "level": level,
                                         "sound": sound, "shader": shader}
                else:
                    unmatched.append((n, shader, desc[:60]))

print(f"lips 条目: {len(lips)}, 匹配到说话人上下文: {len(vo_ctx)}, "
      f"sndshd 台词未匹配到 lips: {len(unmatched)}")
(TRANS / "vo_context.json").write_text(
    json.dumps(vo_ctx, ensure_ascii=False, indent=1), encoding="utf-8")
(TRANS / "vo_unmatched.txt").write_text(
    "\n".join(f"{a}\t{b}\t{c}" for a, b, c in unmatched), encoding="utf-8")

# ---- 3. 输出 TSV ------------------------------------------------------------
def esc(s: str) -> str:
    return s.replace("\t", "\\t")

def write_tsv(path: Path, d: dict[str, str], ctx_fn=None):
    rows = ["id\ten\tzh\tcontext\tstatus"]
    for k, v in d.items():
        zh = DONE.get(k, "")
        status = "done" if zh else "todo"
        ctx = ctx_fn(k) if ctx_fn else ""
        rows.append(f"{k}\t{esc(v)}\t{zh}\t{ctx}\t{status}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8-sig")
    print(f"{path.name}: {len(d)} 条")

write_tsv(TRANS / "ui_code.tsv", merged["english_code.lang"])
write_tsv(TRANS / "ui_guis.tsv", merged["english_guis.lang"])
write_tsv(TRANS / "ui_maps.tsv", merged["english_maps.lang"])
write_tsv(TRANS / "ui_mappack.tsv", merged["english_mappack.lang"])

def lips_ctx(k: str) -> str:
    c = vo_ctx.get(k)
    return f"{c['speaker']} @ {c['level']}" if c else ""

write_tsv(TRANS / "dialogue_lips.tsv", lips, lips_ctx)
