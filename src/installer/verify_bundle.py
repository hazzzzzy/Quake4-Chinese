# -*- coding: utf-8 -*-
"""校验单文件安装器内嵌 payload 与公开分发目录完全一致。"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from PyInstaller.archive.readers import CArchiveReader


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_payload(engine: Path, savedata: Path) -> dict[str, Path]:
    expected: dict[str, Path] = {}
    for name, root in (("engine", engine), ("savedata", savedata)):
        for path in root.rglob("*"):
            if path.is_file():
                key = f"payload/{name}/{path.relative_to(root).as_posix()}"
                expected[key] = path
    return expected


def verify_bundle(installer: Path, engine: Path, savedata: Path) -> None:
    archive = CArchiveReader(str(installer))
    entries = {
        name.replace("\\", "/"): name
        for name in archive.toc
        if name.replace("\\", "/").startswith("payload/")
    }
    expected = expected_payload(engine, savedata)
    missing = sorted(set(expected) - set(entries))
    unexpected = sorted(set(entries) - set(expected))
    mismatched: list[str] = []

    for key in sorted(set(expected) & set(entries)):
        embedded = archive.extract(entries[key])
        if embedded is None or sha256_bytes(embedded) != sha256_bytes(
            expected[key].read_bytes()
        ):
            mismatched.append(key)

    problems = []
    if missing:
        problems.append("缺少：\n" + "\n".join(missing))
    if unexpected:
        problems.append("多余：\n" + "\n".join(unexpected))
    if mismatched:
        problems.append("内容不一致：\n" + "\n".join(mismatched))
    if problems:
        raise RuntimeError("安装器 payload 校验失败：\n" + "\n".join(problems))

    print(f"安装器 payload 校验通过：{len(expected)} 个文件")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--savedata", type=Path, required=True)
    args = parser.parse_args()
    verify_bundle(args.installer, args.engine, args.savedata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
