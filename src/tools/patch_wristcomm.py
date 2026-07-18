# -*- coding: utf-8 -*-
"""生成 wristcomm.gui 中文适配覆盖版。

背景（2026-07-18 用户反馈"游戏已保存出现 2 次"）：wristcomm.gui (Kane 腕带
通讯 gui，即 objectiveSystem) 里也定义了 quicksave_msg windowDef rect y=64。
Player::SaveMessage 同时触发 hud + objectiveSystem 两个 gui 的 saveMessage
namedEvent；两个 gui 的 quicksave_msg 原本都在 y=64 完全重叠 → 玩家只看到一处。
v1.0.9 把 hud.gui 里 quicksave_msg y 从 64 改到 110（避开准星区），wristcomm.gui
未同步 → 现在两处不再重叠，出现 2 处"游戏已保存"。

修法：wristcomm.gui 里 quicksave_msg y 64→110 与 hud.gui 保持一致。

存档兼容性：wristcomm.gui 是 objectiveSystem 面板，与 hud.gui 一样在存档时序列化
运行时状态；本补丁只改 rect 数值，不动 windowDef 结构，与原版存档兼容。
"""
import sys
import zipfile
from pathlib import Path

SRC_PAK = Path(r"D:\data\Quake 4\q4base\pak001.pk4")
DST = Path(r"D:\data\idTech4Apx\savedata\q4base\guis\wristcomm.gui")

EDITS = [
    (b"rect\t0,64,640,20", b"rect\t0,110,640,20"),  # quicksave_msg y=64 -> y=110
]


def main() -> int:
    with zipfile.ZipFile(SRC_PAK) as zf:
        data = zf.read("guis/wristcomm.gui")

    ok = True
    for old, new in EDITS:
        n = data.count(old)
        if n != 1:
            print(f"FAIL: {old!r} 出现 {n} 次（期望 1）")
            ok = False
            continue
        data = data.replace(old, new)
        print(f"OK  : {old!r} -> {new!r}")

    if not ok:
        return 1

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_bytes(data)
    print(f"\n写入 {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
