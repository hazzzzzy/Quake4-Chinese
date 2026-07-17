# diii4a 引擎侧改动

本目录含在 [idTech4A++ (`com.n0n3m4.diii4a`)](https://github.com/glKarin/com.n0n3m4.diii4a) 之上的字幕系统、无线电字幕挂钩、speaker 字幕挂钩、AI 无头模型 else 分支等改动。

## 文件

| 文件 | 说明 |
|---|---|
| `0001-quake4-cn-runtime.patch` | 6 个文件差量（`CMakeLists.txt` / `Game_local.cpp` / `LipSync.cpp` / `Misc.cpp` / `Sound.cpp` / `ai/AI.cpp`） |
| `Subtitles.h` | 字幕系统头（`rvSubtitles` 单例、门控、断行接口） |
| `Subtitles.cpp` | 字幕系统实现（挂钩点、可听性门控、fontdat 度量断行、面板绘制） |

## 应用步骤

```bash
# 1. 克隆并切到 h70 tag（master 与 h70 ABI 不兼容，会进图即崩）
git clone https://github.com/glKarin/com.n0n3m4.diii4a.git
cd com.n0n3m4.diii4a
git checkout v1.1.0harmattan70

# 2. 应用差量
git apply /path/to/Quake4-Chinese/src/engine-patches/0001-quake4-cn-runtime.patch

# 3. 拷贝新增文件
cp /path/to/Quake4-Chinese/src/engine-patches/Subtitles.h    Q3E/src/main/jni/doom3/neo/quake4/
cp /path/to/Quake4-Chinese/src/engine-patches/Subtitles.cpp  Q3E/src/main/jni/doom3/neo/quake4/

# 4. 构建 q4game.dll（VS2022 + 自带 CMake）
cd Q3E/src/main/jni/doom3/neo
cmake . -B build \
  -DCORE=OFF -DBASE=OFF -DRAVEN=OFF -DQUAKE4=ON
cmake --build build --config Release --target q4game
```

## 修改摘要

| 文件 | 改动 |
|---|---|
| `CMakeLists.txt` | 把 `Subtitles.cpp` 加入 QUAKE4 目标源列表 |
| `Game_local.cpp` | `rvSubtitles::Get()` 单例挂到 `idGameLocal::RunFrame` 绘制回调 |
| `LipSync.cpp` | `StartLipSyncing` 时 `rvSubtitles::AddFromEntity` 推入字幕 |
| `Misc.cpp` | `idFuncRadioChatter::Event_Activate` 挂 `FindLipSync(snd_radiochatter, false)` 补无线电字幕 |
| `Sound.cpp` | `idSound::DoSound(play)` 按 shader 名找 lipsync decl，走 speaker/PA 字幕（fallbackSpeaker 参数区分来源前缀） |
| `ai/AI.cpp` | `idAI::Speak` else 分支对无头模型 NPC 补挂 lipsync 注入 |

## cvar

新增 3 个：

- `harm_g_subtitles` — 0 关 1 开（默认 1）
- `harm_g_subtitleHoldTime` — 字幕停留时间（秒，默认 2.5）
- `harm_g_subtitleMinTime` — 短句最小显示时长（秒，默认 0.8）
- `harm_g_subtitlePVSCheck` — PVS 隔墙过滤（默认 1）
- `harm_g_subtitleDebug` — 打印 `[SUB]` 决策日志（默认 0，验收开）

## 挂钩语义详情

见 [`docs/localization-guide.md § 6 字幕系统实装`](../../docs/localization-guide.md#6-字幕系统实装)。

## GPL 义务

`Subtitles.h` / `Subtitles.cpp` 与差量补丁均以 **GPL-3.0** 发布（与 idTech4 引擎同）。分发编译后的 `q4game.dll` 二进制时必须提供源码，本仓库满足此要求。
