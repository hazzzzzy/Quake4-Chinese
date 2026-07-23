# Windows 图形安装器

安装器将公开分发包中的开源引擎和汉化资源部署到玩家的 Quake 4 游戏目录，并从玩家自己的 `pak001.pk4`、`pak014.pk4`、`pak021.pk4` 和 `zpak_english*.pk4` 现场生成不随补丁分发的运行资产。

安装后的目录：

```text
Quake 4\
├── Quake4中文启动器.exe
├── q4base\
└── Quake4-Chinese\
    ├── engine\
    └── savedata\
```

`Quake4中文启动器.exe` 使用 `Quake4-Chinese\savedata` 作为 `fs_savepath`，所以汉化版存档和原版存档分别保存。汉化版存档实际位于 `Quake4-Chinese\savedata\q4base\savegames`。

安装进度按资源复制字节、GUI 生成步骤和语音文件处理字节推进。安装器会从游戏目录中的原版 `Quake4.exe` 读取图标并写入 `Quake4中文启动器.exe`；桌面快捷方式始终引用该启动器的同一图标。重复安装会更新程序和汉化资产，同时保留已有配置与存档。

安装完成后可打开“存档管理”：窗口分别显示原版与汉化版的存档目录、存档数量和最近更新时间，并提供打开目录与独立备份操作。备份写入 `Quake4-Chinese\save-backups`，不会移动或覆盖原存档。

## 构建

在工程根目录使用项目虚拟环境安装 PyInstaller 后运行：

```powershell
& .\src\installer\build.ps1
```

构建脚本先编译原生启动器，再将启动器、现场生成工具以及 `dist\engine`、`dist\savedata` 中的公开 payload 打入单文件图形安装器。冻结运行时从 `_MEIPASS\payload` 读取这些资产，因此最终 EXE 可以脱离 ZIP 和同级资源目录独立运行。

最终文件写入 `dist\Quake4-Chinese-Installer.exe`。运行 `src\tools\package_release.ps1` 时会复制成带版本号的 Release 资产。
