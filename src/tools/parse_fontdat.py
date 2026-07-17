# -*- coding: utf-8 -*-
"""解析 Quake 4 fontdat（含 idTech4A++ 宽字库扩展），输出纵向度量。

Q4 基础段: 256 字形 × 9 float32 (imageWidth,imageHeight,xSkip,pitch,top,s,t,s2,t2)
           + 5 float32 (pointSize, maxWidth, maxHeight, ph1, ph2) = 9236 字节
宽字库扩展段: magic u32, version u32, numFiles i32, width i32, height i32,
              numIndexes i32, indexes[n] i32, numGlyphs i32,
              每字形: 9 float32 + shaderName char[32] = 68 字节
运行时 maxHeight = max(基础段 header maxHeight 之外重算: ASCII top 与宽字形 top 的最大值,
                       以 header 第3个 float 为初值)。height 一律取 top。
"""
import struct
import sys

GLYPHS = 256

def parse(path):
    with open(path, "rb") as f:
        data = f.read()
    off = 0
    ascii_glyphs = []
    for i in range(GLYPHS):
        vals = struct.unpack_from("<9f", data, off)
        off += 36
        ascii_glyphs.append(dict(zip(
            ("imageWidth", "imageHeight", "xSkip", "pitch", "top",
             "s", "t", "s2", "t2"), vals)))
    point_size, max_w, max_h, ph1, ph2 = struct.unpack_from("<5f", data, off)
    off += 20
    wide = []
    if off + 20 <= len(data):
        magic, version, num_files, w, h = struct.unpack_from("<IIiii", data, off)
        off += 20
        num_idx = struct.unpack_from("<i", data, off)[0]
        off += 4 + num_idx * 4
        num_glyphs = struct.unpack_from("<i", data, off)[0]
        off += 4
        for i in range(num_glyphs):
            vals = struct.unpack_from("<9f", data, off)
            off += 36 + 32  # 9 floats + shaderName
            wide.append(dict(zip(
                ("imageWidth", "imageHeight", "xSkip", "pitch", "top",
                 "s", "t", "s2", "t2"), vals)))
    # 运行时 mh 计算（RegisterFont）：初值 header max_h，再并入宽表与 ASCII 的 top
    mh = int(max_h)
    for g in wide:
        mh = max(mh, int(g["top"]))
    for i in range(0x20, 0x7F):  # GLYPH_START..GLYPH_END
        mh = max(mh, int(ascii_glyphs[i]["top"]))
    digits = {chr(c): (int(ascii_glyphs[c]["top"]), int(ascii_glyphs[c]["imageHeight"]))
              for c in range(ord("0"), ord("9") + 1)}
    print(f"{path}")
    print(f"  header: pointSize={point_size:.0f} maxWidth={max_w:.0f} "
          f"maxHeight={max_h:.0f} wideGlyphs={len(wide)}")
    print(f"  runtime maxHeight = {mh}")
    if wide:
        wtops = sorted(int(g['top']) for g in wide)
        print(f"  wide top: min={wtops[0]} max={wtops[-1]}")
    print(f"  digits (top,imageHeight): { {k: v for k, v in list(digits.items())[:3]} } ... 0-9 "
          f"topMax={max(v[0] for v in digits.values())} "
          f"imgHMax={max(v[1] for v in digits.values())}")
    print()

if __name__ == "__main__":
    for p in sys.argv[1:]:
        parse(p)
