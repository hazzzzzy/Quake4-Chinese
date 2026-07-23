# -*- coding: utf-8 -*-
"""Quake 4 简体中文汉化图形安装器。"""

from __future__ import annotations

import contextlib
import ctypes
import io
import os
import queue
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import traceback
import winreg
import zipfile
from datetime import datetime
from pathlib import Path
from tkinter import (
    BOTH,
    END,
    LEFT,
    RIGHT,
    X,
    BooleanVar,
    StringVar,
    Tk,
    Toplevel,
    filedialog,
    messagebox,
)
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import pefile


if not getattr(sys, "frozen", False):
    TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
    sys.path.insert(0, str(TOOLS_DIR))

from build_dist_extras import build_assets  # noqa: E402


APP_NAME = "Quake 4 简体中文汉化安装器"
INSTALL_DIRECTORY_NAME = "Quake4-Chinese"
LAUNCHER_NAME = "Quake4中文启动器.exe"
BUNDLED_LAUNCHER_NAME = "Q4CNLauncher.exe"
SHORTCUT_NAME = "Quake 4 简体中文汉化.lnk"
REQUIRED_PAKS = ("pak001.pk4", "pak014.pk4", "pak021.pk4", "zpak_english.pk4")
CREATE_NO_WINDOW = 0x08000000
RT_ICON = 3
RT_GROUP_ICON = 14


class InstallError(RuntimeError):
    """安装前置条件或部署步骤失败。"""


class CallbackWriter(io.TextIOBase):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.pending = ""
        self.callback_stdout = sys.stdout
        self.callback_stderr = sys.stderr

    def emit(self, line: str) -> None:
        with contextlib.redirect_stdout(self.callback_stdout), \
             contextlib.redirect_stderr(self.callback_stderr):
            self.callback(line)

    def write(self, value: str) -> int:
        self.pending += value
        while "\n" in self.pending:
            line, self.pending = self.pending.split("\n", 1)
            if line.strip():
                self.emit(line)
        return len(value)

    def flush(self) -> None:
        if self.pending.strip():
            self.emit(self.pending)
        self.pending = ""


def application_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2] / "dist"


def bundled_launcher() -> Path:
    override = os.environ.get("Q4CN_LAUNCHER_PATH")
    if override:
        return Path(override).resolve()
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / BUNDLED_LAUNCHER_NAME
    return Path(__file__).resolve().parents[2] / "tmp" / "build-installer-native" / BUNDLED_LAUNCHER_NAME


def validate_game_directory(game_directory: Path) -> None:
    if not game_directory.is_dir():
        raise InstallError("请选择 Quake 4 游戏目录。")
    missing = [
        name for name in REQUIRED_PAKS
        if not (game_directory / "q4base" / name).is_file()
    ]
    if missing:
        joined = "、".join(missing)
        raise InstallError(
            f"所选目录缺少 {joined}。请选择包含 q4base 的 Quake 4 1.4.2 游戏目录。"
        )
    if not (game_directory / "Quake4.exe").is_file():
        raise InstallError("所选目录缺少原版 Quake4.exe，游戏图标来源未找到。")


def validate_payload(payload_directory: Path, launcher: Path) -> None:
    required = (
        payload_directory / "engine" / "Quake4.exe",
        payload_directory / "engine" / "q4game.dll",
        payload_directory / "savedata" / "q4base" / "strings" / "chinese_guis.lang",
        launcher,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise InstallError("安装包文件不完整：\n" + "\n".join(missing))


def desktop_directory() -> Path:
    buffer = ctypes.create_unicode_buffer(32768)
    result = ctypes.windll.shell32.SHGetFolderPathW(
        None, 0x0010, None, 0, buffer
    )
    if result != 0:
        raise InstallError(f"读取桌面目录失败，系统返回值：0x{result & 0xFFFFFFFF:08X}")
    return Path(buffer.value)


def copy_directories(pairs, progress) -> None:
    files: list[tuple[Path, Path, int]] = []
    for source_root, target_root in pairs:
        for source in source_root.rglob("*"):
            if source.is_file():
                files.append((source, target_root / source.relative_to(source_root), source.stat().st_size))

    total = sum(size for _source, _target, size in files)
    completed = 0
    for source, target, size in files:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        completed += size
        progress(completed, total)


def current_user_sid() -> str:
    token_query = 0x0008
    token_user_class = 1
    token = ctypes.c_void_p()
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    advapi32.OpenProcessToken.argtypes = (
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.POINTER(ctypes.c_void_p),
    )
    advapi32.OpenProcessToken.restype = ctypes.c_int
    advapi32.GetTokenInformation.argtypes = (
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.POINTER(ctypes.c_ulong),
    )
    advapi32.GetTokenInformation.restype = ctypes.c_int
    advapi32.ConvertSidToStringSidW.argtypes = (
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    )
    advapi32.ConvertSidToStringSidW.restype = ctypes.c_int
    kernel32.LocalFree.argtypes = (ctypes.c_void_p,)
    kernel32.LocalFree.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
    kernel32.CloseHandle.restype = ctypes.c_int
    if not advapi32.OpenProcessToken(
        kernel32.GetCurrentProcess(), token_query, ctypes.byref(token)
    ):
        raise InstallError(f"读取当前用户令牌失败，系统错误码：{ctypes.get_last_error()}")

    try:
        required = ctypes.c_ulong()
        advapi32.GetTokenInformation(
            token, token_user_class, None, 0, ctypes.byref(required)
        )
        buffer = ctypes.create_string_buffer(required.value)
        if not advapi32.GetTokenInformation(
            token,
            token_user_class,
            buffer,
            required.value,
            ctypes.byref(required),
        ):
            raise InstallError(f"读取当前用户 SID 失败，系统错误码：{ctypes.get_last_error()}")
        sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
        sid_text = ctypes.c_void_p()
        if not advapi32.ConvertSidToStringSidW(sid, ctypes.byref(sid_text)):
            raise InstallError(f"转换当前用户 SID 失败，系统错误码：{ctypes.get_last_error()}")
        try:
            return ctypes.wstring_at(sid_text)
        finally:
            kernel32.LocalFree(sid_text)
    finally:
        kernel32.CloseHandle(token)


def grant_install_access(install_directory: Path) -> None:
    sid = current_user_sid()
    process = subprocess.run(
        [
            "icacls.exe",
            str(install_directory),
            "/inheritance:e",
            "/grant:r",
            f"*{sid}:(OI)(CI)M",
            "/T",
            "/C",
            "/Q",
        ],
        check=False,
        capture_output=True,
        creationflags=CREATE_NO_WINDOW,
    )
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).decode("mbcs", errors="replace").strip()
        raise InstallError(
            f"设置汉化目录访问权限失败，icacls 返回码：{process.returncode}\n{detail}"
        )


def resource_bytes(pe: pefile.PE, entry) -> tuple[bytes, int]:
    language_entry = entry.directory.entries[0]
    data = language_entry.data.struct
    return pe.get_data(data.OffsetToData, data.Size), language_entry.id


def apply_game_icon(game_executable: Path, launcher: Path) -> None:
    source = pefile.PE(str(game_executable), fast_load=False)
    source.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]]
    )
    try:
        root_entries = source.DIRECTORY_ENTRY_RESOURCE.entries
    except AttributeError as error:
        raise InstallError("原版 Quake4.exe 中未找到图标资源。") from error

    group_type = next((entry for entry in root_entries if entry.id == RT_GROUP_ICON), None)
    icon_type = next((entry for entry in root_entries if entry.id == RT_ICON), None)
    if group_type is None or icon_type is None or not group_type.directory.entries:
        raise InstallError("原版 Quake4.exe 图标资源不完整。")

    group_entry = group_type.directory.entries[0]
    group_data, group_language = resource_bytes(source, group_entry)
    if len(group_data) < 6:
        raise InstallError("原版 Quake4.exe 图标组数据损坏。")
    reserved, icon_kind, icon_count = struct.unpack_from("<HHH", group_data)
    if reserved != 0 or icon_kind != 1 or len(group_data) < 6 + icon_count * 14:
        raise InstallError("原版 Quake4.exe 图标组格式异常。")

    icon_ids = {
        struct.unpack_from("<H", group_data, 6 + index * 14 + 12)[0]
        for index in range(icon_count)
    }
    icon_entries = {
        entry.id: entry for entry in icon_type.directory.entries
        if entry.id in icon_ids
    }
    if set(icon_entries) != icon_ids:
        raise InstallError("原版 Quake4.exe 图标图像不完整。")

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    begin_update = kernel32.BeginUpdateResourceW
    update_resource = kernel32.UpdateResourceW
    end_update = kernel32.EndUpdateResourceW
    begin_update.argtypes = (ctypes.c_wchar_p, ctypes.c_int)
    begin_update.restype = ctypes.c_void_p
    update_resource.argtypes = (
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_ushort,
        ctypes.c_void_p,
        ctypes.c_ulong,
    )
    update_resource.restype = ctypes.c_int
    end_update.argtypes = (ctypes.c_void_p, ctypes.c_int)
    end_update.restype = ctypes.c_int
    update_handle = begin_update(str(launcher), False)
    if not update_handle:
        raise InstallError(f"打开启动器图标资源失败，系统错误码：{ctypes.get_last_error()}")

    committed = False
    buffers = []
    try:
        for icon_id in sorted(icon_ids):
            icon_data, icon_language = resource_bytes(source, icon_entries[icon_id])
            icon_buffer = ctypes.create_string_buffer(icon_data)
            buffers.append(icon_buffer)
            if not update_resource(
                update_handle,
                ctypes.c_void_p(RT_ICON),
                ctypes.c_void_p(icon_id),
                icon_language,
                icon_buffer,
                len(icon_data),
            ):
                raise InstallError(f"写入启动器图标图像失败，系统错误码：{ctypes.get_last_error()}")

        group_buffer = ctypes.create_string_buffer(group_data)
        buffers.append(group_buffer)
        group_name_buffer = None
        if group_entry.name is None:
            group_name = ctypes.c_void_p(group_entry.id)
        else:
            group_name_buffer = ctypes.create_unicode_buffer(str(group_entry.name))
            group_name = ctypes.cast(group_name_buffer, ctypes.c_void_p)
        if not update_resource(
            update_handle,
            ctypes.c_void_p(RT_GROUP_ICON),
            group_name,
            group_language,
            group_buffer,
            len(group_data),
        ):
            raise InstallError(f"写入启动器图标组失败，系统错误码：{ctypes.get_last_error()}")
        if not end_update(update_handle, False):
            raise InstallError(f"保存启动器图标失败，系统错误码：{ctypes.get_last_error()}")
        committed = True
    finally:
        source.close()
        if not committed:
            end_update(update_handle, True)


def create_shortcut(launcher: Path) -> Path:
    shortcut = desktop_directory() / SHORTCUT_NAME
    process = subprocess.run(
        [str(launcher), "--create-shortcut", str(shortcut)],
        check=False,
        creationflags=CREATE_NO_WINDOW,
    )
    if process.returncode != 0:
        raise InstallError(f"桌面快捷方式创建失败，启动器返回码：{process.returncode}")
    if not shortcut.is_file():
        raise InstallError("启动器返回成功，但桌面快捷方式未生成。")
    return shortcut


def save_directories(game_directory: Path) -> dict[str, Path]:
    return {
        "official": game_directory / "q4base" / "savegames",
        "localized": (
            game_directory
            / INSTALL_DIRECTORY_NAME
            / "savedata"
            / "q4base"
            / "savegames"
        ),
    }


def save_directory_summary(directory: Path) -> tuple[int, str]:
    save_files = list(directory.glob("*.save")) if directory.is_dir() else []
    if not save_files:
        return 0, "-"
    latest = max(path.stat().st_mtime for path in save_files)
    return len(save_files), datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M")


def backup_savegames(
    source_directory: Path,
    backup_directory: Path,
    backup_name: str,
) -> Path:
    if not source_directory.is_dir():
        raise InstallError(f"存档目录尚未生成：\n{source_directory}")
    files = sorted(path for path in source_directory.rglob("*") if path.is_file())
    if not any(path.suffix.lower() == ".save" for path in files):
        raise InstallError(f"存档目录中没有可备份的存档：\n{source_directory}")

    backup_directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = backup_directory / f"{backup_name}-{timestamp}.zip"
    suffix = 2
    while target.exists():
        target = backup_directory / f"{backup_name}-{timestamp}-{suffix}.zip"
        suffix += 1
    temporary = target.with_suffix(".zip.tmp")
    try:
        with zipfile.ZipFile(
            temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6
        ) as archive:
            for path in files:
                archive.write(path, path.relative_to(source_directory).as_posix())
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
    if not target.is_file():
        raise InstallError("存档备份写入后未找到目标文件。")
    return target


def install_localization(
    game_directory: Path,
    create_desktop_shortcut: bool,
    report,
    progress=lambda _value, _message: None,
) -> Path:
    game_directory = game_directory.resolve()
    payload_directory = application_directory()
    launcher_source = bundled_launcher()
    validate_game_directory(game_directory)
    validate_payload(payload_directory, launcher_source)

    install_directory = game_directory / INSTALL_DIRECTORY_NAME
    staging_directory = Path(tempfile.mkdtemp(
        prefix=".Quake4-Chinese-install-",
        dir=game_directory,
    ))
    try:
        report("正在复制开源引擎和汉化资源……")
        copy_directories(
            (
                (payload_directory / "engine", staging_directory / "engine"),
                (payload_directory / "savedata", staging_directory / "savedata"),
            ),
            lambda done, total: progress(
                20 * done / max(total, 1), "正在复制汉化资源"
            ),
        )

        report("正在从正版游戏数据生成补齐资源……")
        writer = CallbackWriter(report)
        with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
            result = build_assets(
                game_directory,
                staging_directory / "savedata" / "q4base",
                progress=lambda value, message: progress(20 + 55 * value, message),
            )
        writer.flush()
        if result != 0:
            raise InstallError(f"补齐资源生成失败，返回码：{result}")

        install_directory.mkdir(parents=True, exist_ok=True)
        copy_directories(
            (
                (staging_directory / "engine", install_directory / "engine"),
                (staging_directory / "savedata", install_directory / "savedata"),
            ),
            lambda done, total: progress(
                75 + 20 * done / max(total, 1), "正在部署汉化文件"
            ),
        )
    finally:
        if staging_directory.exists():
            shutil.rmtree(staging_directory)

    report("正在设置汉化目录访问权限……")
    grant_install_access(install_directory)
    progress(97, "汉化目录权限设置完成")

    launcher_target = game_directory / LAUNCHER_NAME
    shutil.copy2(launcher_source, launcher_target)
    if not launcher_target.is_file():
        raise InstallError("汉化资源已生成，但游戏目录中的启动器未写入。")
    apply_game_icon(game_directory / "Quake4.exe", launcher_target)
    progress(99, "游戏启动器已生成")

    if create_desktop_shortcut:
        report("正在创建桌面快捷方式……")
        shortcut = create_shortcut(launcher_target)
        report(f"桌面快捷方式：{shortcut}")

    report(f"汉化启动器：{launcher_target}")
    progress(100, "汉化安装完成")
    return launcher_target


def registry_install_locations() -> list[Path]:
    locations: list[Path] = []
    roots = (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER)
    uninstall_keys = (
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    )
    for root in roots:
        for key_name in uninstall_keys:
            try:
                with winreg.OpenKey(root, key_name) as key:
                    for index in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, index)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if "quake 4" not in str(display_name).lower():
                                    continue
                                location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                if location:
                                    locations.append(Path(location))
                        except (FileNotFoundError, OSError):
                            continue
            except (FileNotFoundError, OSError):
                continue
    return locations


def detect_game_directory() -> Path | None:
    candidates: list[Path] = []
    base = application_directory()
    candidates.extend((base, base.parent))
    candidates.extend(registry_install_locations())

    for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        drive = Path(f"{letter}:\\")
        if drive.exists():
            candidates.append(drive / "Quake 4")

    program_roots = (
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
    )
    for root in filter(None, program_roots):
        candidates.append(Path(root) / "Steam" / "steamapps" / "common" / "Quake 4")

    seen: set[str] = set()
    for candidate in candidates:
        key = os.path.normcase(os.path.abspath(candidate))
        if key in seen:
            continue
        seen.add(key)
        try:
            validate_game_directory(candidate)
            return candidate.resolve()
        except InstallError:
            continue
    return None


class SaveManagerWindow:
    def __init__(self, parent: Tk, game_directory: Path):
        self.game_directory = game_directory.resolve()
        self.paths = save_directories(self.game_directory)
        self.window = Toplevel(parent)
        self.window.title("Quake 4 存档管理")
        self.window.geometry("900x290")
        self.window.minsize(760, 260)
        self.window.transient(parent)

        main = ttk.Frame(self.window, padding=18)
        main.pack(fill=BOTH, expand=True)
        ttk.Label(
            main,
            text="原版与汉化版存档",
            font=("Microsoft YaHei UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        table = ttk.Frame(main)
        table.pack(fill=X)
        self.tree = ttk.Treeview(
            table,
            columns=("version", "count", "latest", "directory"),
            show="headings",
            height=2,
        )
        self.tree.heading("version", text="版本")
        self.tree.heading("count", text="存档数")
        self.tree.heading("latest", text="最近更新")
        self.tree.heading("directory", text="目录")
        self.tree.column("version", width=90, anchor="center", stretch=False)
        self.tree.column("count", width=70, anchor="center", stretch=False)
        self.tree.column("latest", width=145, anchor="center", stretch=False)
        self.tree.column("directory", width=530, anchor="w")
        self.tree.pack(fill=X)
        horizontal_scroll = ttk.Scrollbar(
            table,
            orient="horizontal",
            command=self.tree.xview,
        )
        horizontal_scroll.pack(fill=X)
        self.tree.configure(xscrollcommand=horizontal_scroll.set)

        buttons = ttk.Frame(main)
        buttons.pack(fill=X, pady=(14, 8))
        ttk.Button(
            buttons,
            text="打开原版目录",
            command=lambda: self.open_directory("official"),
        ).pack(side=LEFT)
        ttk.Button(
            buttons,
            text="备份原版存档",
            command=lambda: self.backup("official"),
        ).pack(side=LEFT, padx=(8, 0))
        ttk.Button(
            buttons,
            text="打开汉化目录",
            command=lambda: self.open_directory("localized"),
        ).pack(side=LEFT, padx=(20, 0))
        ttk.Button(
            buttons,
            text="备份汉化存档",
            command=lambda: self.backup("localized"),
        ).pack(side=LEFT, padx=(8, 0))
        ttk.Button(buttons, text="刷新", command=self.refresh).pack(side=RIGHT)

        self.status = StringVar(value="")
        ttk.Label(main, textvariable=self.status).pack(anchor="w", pady=(6, 0))
        self.refresh()

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        labels = {"official": "原版", "localized": "汉化版"}
        for key in ("official", "localized"):
            directory = self.paths[key]
            count, latest = save_directory_summary(directory)
            self.tree.insert(
                "",
                "end",
                iid=key,
                values=(labels[key], count, latest, str(directory)),
            )

    def open_directory(self, key: str) -> None:
        directory = self.paths[key]
        if not directory.is_dir():
            messagebox.showinfo(
                APP_NAME,
                f"存档目录尚未生成：\n{directory}",
                parent=self.window,
            )
            return
        os.startfile(directory)

    def backup(self, key: str) -> None:
        labels = {"official": "original", "localized": "chinese"}
        backup_directory = (
            self.game_directory / INSTALL_DIRECTORY_NAME / "save-backups"
        )
        try:
            target = backup_savegames(
                self.paths[key], backup_directory, labels[key])
        except (InstallError, OSError) as error:
            messagebox.showerror(APP_NAME, str(error), parent=self.window)
            return
        self.status.set(f"备份完成：{target}")
        self.refresh()
        messagebox.showinfo(
            APP_NAME,
            f"存档备份完成：\n{target}",
            parent=self.window,
        )


class InstallerWindow:
    def __init__(self, root: Tk):
        self.root = root
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.game_directory = StringVar()
        self.desktop_shortcut = BooleanVar(value=True)
        self.status = StringVar(value="请选择 Quake 4 1.4.2 游戏目录")
        self.installed_launcher: Path | None = None

        root.title(APP_NAME)
        root.geometry("720x560")
        root.minsize(680, 520)
        root.option_add("*Font", ("Microsoft YaHei UI", 10))

        main = ttk.Frame(root, padding=20)
        main.pack(fill=BOTH, expand=True)

        ttk.Label(main, text="Quake 4 简体中文汉化", font=("Microsoft YaHei UI", 17, "bold")).pack(anchor="w")
        ttk.Label(main, text="游戏目录").pack(anchor="w", pady=(20, 6))

        path_row = ttk.Frame(main)
        path_row.pack(fill=X)
        self.path_entry = ttk.Entry(path_row, textvariable=self.game_directory)
        self.path_entry.pack(side=LEFT, fill=X, expand=True)
        self.browse_button = ttk.Button(path_row, text="浏览…", command=self.browse)
        self.browse_button.pack(side=RIGHT, padx=(8, 0))

        self.desktop_check = ttk.Checkbutton(
            main,
            text="创建桌面快捷方式",
            variable=self.desktop_shortcut,
        )
        self.desktop_check.pack(anchor="w", pady=(14, 10))

        self.progress = ttk.Progressbar(main, mode="determinate", value=0)
        self.progress.pack(fill=X, pady=(0, 8))
        ttk.Label(main, textvariable=self.status).pack(anchor="w", pady=(0, 8))

        self.log = ScrolledText(main, height=10, wrap="word", state="disabled")
        self.log.pack(fill=BOTH, expand=True)

        buttons = ttk.Frame(main)
        buttons.pack(fill=X, pady=(14, 0))
        self.install_button = ttk.Button(buttons, text="安装汉化", command=self.start_install)
        self.install_button.pack(side=RIGHT)
        self.launch_button = ttk.Button(
            buttons,
            text="启动汉化版",
            command=self.launch_game,
            state="disabled",
        )
        self.launch_button.pack(side=RIGHT, padx=(0, 8))
        self.save_button = ttk.Button(
            buttons,
            text="存档管理",
            command=self.manage_saves,
            state="disabled",
        )
        self.save_button.pack(side=RIGHT, padx=(0, 8))

        detected = detect_game_directory()
        if detected is not None:
            self.game_directory.set(str(detected))
            self.status.set("已识别 Quake 4 1.4.2 游戏目录")
            self.set_existing_install(detected)

        root.after(100, self.process_events)

    def browse(self) -> None:
        initial = self.game_directory.get() or str(Path.home())
        selected = filedialog.askdirectory(title="选择 Quake 4 游戏目录", initialdir=initial)
        if selected:
            self.game_directory.set(selected)
            self.set_existing_install(Path(selected))

    def set_existing_install(self, game_directory: Path) -> None:
        launcher = game_directory / LAUNCHER_NAME
        self.installed_launcher = launcher if launcher.is_file() else None
        action_state = "normal" if self.installed_launcher is not None else "disabled"
        self.launch_button.configure(state=action_state)
        self.save_button.configure(state=action_state)

    def append_log(self, line: str) -> None:
        self.log.configure(state="normal")
        self.log.insert(END, line.rstrip() + "\n")
        self.log.see(END)
        self.log.configure(state="disabled")

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.path_entry.configure(state=state)
        self.browse_button.configure(state=state)
        self.desktop_check.configure(state=state)
        self.install_button.configure(state=state)
        if busy:
            self.launch_button.configure(state="disabled")
            self.save_button.configure(state="disabled")
        else:
            installed = (
                self.installed_launcher is not None
                and self.installed_launcher.is_file()
            )
            action_state = "normal" if installed else "disabled"
            self.launch_button.configure(state=action_state)
            self.save_button.configure(state=action_state)
        self.progress.configure(mode="determinate")

    def start_install(self) -> None:
        game_directory = Path(self.game_directory.get().strip())
        try:
            validate_game_directory(game_directory)
        except InstallError as error:
            messagebox.showerror(APP_NAME, str(error), parent=self.root)
            return

        install_directory = game_directory / INSTALL_DIRECTORY_NAME
        if install_directory.exists():
            proceed = messagebox.askyesno(
                APP_NAME,
                "检测到已有汉化目录。继续安装将更新程序和汉化资产，并保留现有配置与存档。",
                parent=self.root,
            )
            if not proceed:
                return

        self.installed_launcher = None
        self.launch_button.configure(state="disabled")
        self.progress.configure(value=0)
        self.set_busy(True)
        self.status.set("正在安装汉化……")
        self.append_log("开始安装")
        thread = threading.Thread(
            target=self.install_worker,
            args=(game_directory, self.desktop_shortcut.get()),
            daemon=True,
        )
        thread.start()

    def install_worker(self, game_directory: Path, desktop_shortcut: bool) -> None:
        try:
            launcher = install_localization(
                game_directory,
                desktop_shortcut,
                lambda line: self.events.put(("log", line)),
                lambda value, message: self.events.put(
                    ("progress", (value, message))
                ),
            )
            self.events.put(("success", launcher))
        except Exception as error:
            detail = traceback.format_exc()
            self.events.put(("failure", (error, detail)))

    def process_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "log":
                    line = str(payload)
                    self.status.set(line)
                    self.append_log(line)
                elif event == "progress":
                    value, message = payload
                    self.progress.configure(value=max(0.0, min(100.0, float(value))))
                    self.status.set(str(message))
                elif event == "success":
                    self.installed_launcher = Path(payload)
                    self.set_busy(False)
                    self.status.set("汉化安装完成")
                    self.progress.configure(value=100)
                    self.append_log("汉化安装完成")
                    messagebox.showinfo(
                        APP_NAME,
                        f"汉化安装完成。\n\n启动器：\n{self.installed_launcher}",
                        parent=self.root,
                    )
                elif event == "failure":
                    error, detail = payload
                    self.set_busy(False)
                    self.status.set("安装失败")
                    self.append_log(detail)
                    messagebox.showerror(APP_NAME, str(error), parent=self.root)
        except queue.Empty:
            pass
        self.root.after(100, self.process_events)

    def launch_game(self) -> None:
        if self.installed_launcher is None or not self.installed_launcher.is_file():
            messagebox.showerror(APP_NAME, "游戏目录中的汉化启动器不存在。", parent=self.root)
            return
        subprocess.Popen([str(self.installed_launcher)], cwd=self.installed_launcher.parent)

    def manage_saves(self) -> None:
        if self.installed_launcher is None or not self.installed_launcher.is_file():
            messagebox.showerror(APP_NAME, "请先完成汉化安装。", parent=self.root)
            return
        SaveManagerWindow(self.root, self.installed_launcher.parent)


def main() -> int:
    if os.name != "nt":
        raise InstallError("本安装器面向 Windows 10/11。")
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = Tk()
    ttk.Style(root).theme_use("vista")
    InstallerWindow(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
