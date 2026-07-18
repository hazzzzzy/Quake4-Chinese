# Changelog

## v1.0.7 — 2026-07-18

### DLL 侧

- 字幕说话人前缀分隔符改为全角冒号：`"广播: xxx"` → `"广播：xxx"`（去掉半角冒号+空格，改中文标点）
- 字幕面板墨迹垂直居中：`SUB_ROW_ADJ = 1.0` 补偿 CJK drop 让墨迹中线接近面板中线（原偏顶 ~2 屏幕像素）

### hud.gui 补丁扩展

- 切枪武器名 `ws_name` rect y 42→48（用户反馈"向下移一点"；下移 6 虚拟 px ≈ 7 屏幕像素，避开图标 y=20-46 重叠）
- HUD 大数字 rect h 26→29（+3 名义 px，修 v1.0.6 后 ASCII drop=2 让数字位图底端 y=455 卡 rect 底边被裁 10% 的问题）
  - 覆盖 `ammo_amount` / `ammo_amount_nc` / `health_amount` / `armor_amount` 及 MP 版 7 处

### mainmenu.gui 补丁（新增补齐物）

- 设置页 3 按钮 rect y+4：`set_sys_t_auto` (自动检测设置) / `set_sys_t_adv` (高级设置) / `set_sys_t_b9` (高级音频设置)
- CJK 视觉与容器 rect 中线对齐（容器 h=25、文字 rect h=18 原贴容器顶）
- 加入 postinstall 版权敏感物补齐流程

## v1.0.6 — 2026-07-18

### 字体基线（中英混排视觉对齐）

- 修复 `export_font.py`：全档 `ascii_drop = drop`（12→1、24→2、48→4 名义 px）
- 用户反馈"MCC 着陆场 里 MCC 顶部偏上"根因：CJK 已 drop 后视觉在 rect 里居中，ASCII 未 drop 相对 rect 偏上 3.2 屏幕像素（不是相对 CJK）
- 修复后实机验证：`Sanchez 列兵`、`Raven 小队`、`传入 通讯` 中英混排完全齐平；HUD 数字（8/14/100/50）无裁切
- 该修复覆盖所有 UI 家族的 24/48 号（chain/marine/lowpixel/profont/r_strogg），受益场景：loading 地名标签、准星名牌、无线电两行、切枪武器名、菜单标题

## v1.0.5 — 2026-07-17

### CJK 字体质量

- 换字体到**思源黑体 Medium**（Adobe/Google，OFL 开源可分发；替代 v1.0.4 的微软雅黑常规）
- 全档 2x 超采样渲染（1x 灰度 AA 小字发虚参差，1x 单色小字锐利但放大锯齿，2x AA 两全）
- 按 16:9 分辨率预压缩宽高比 `ASPECT=0.75` 抵消引擎 GUI 640×480 → 16:9 拉伸（方块汉字被拉扁根源）
- CJK 视觉基线下沉 `drop=1/2/4`（12/24/48 号）修复"汉字在拉丁窗格里普遍偏上"

### 体积优化

- TGA 改 RLE (type 10) + 同源家族共享贴图（材质别名 `.mtr`），字体从 **1067MB → 131MB**（磁盘/显存同比例降）

### Strogg 转译

- `strogg` 家族改**原版直通** + CJK Knuth 乘散列稳定映射到原版 62 个符号（改造前终端外星文氛围恢复）
- `r_strogg` 家族沿用思源黑体（可读侧）
- `med1_textchange.gui` 中文化补丁（神经细胞植入转译动画）

## v1.0.4 — 2026-07-16 晚

### 读档崩溃根因（重大）

- `hud.gui` 覆盖必须基于 **pak021 版底稿**（1.4 补丁 2507 行，运行时实际生效）；上轮基于 pak001 版（2272 行）导致结构差 235 行，存档序列化流错位内存踩坏
- 覆盖只允许改数值（rect/textscale），禁止增删 windowDef/脚本/变量

### 字幕改进

- 换行按 fontdat 真实字体度量计算（原 MAX_UNITS=58 半角只用面板 64% 宽）
- 空格断点仅在行预算 70% 之后可取，防"瘫痪了 Strogg 的"式短行

### 无线电 decl 缺口补齐

- 全游戏 336 条 `func_radiochatter` 台词，原版仅 84 条有 lipsync decl；本轮补齐 251 条（`vo_1_2_20_50_1` 全资产无定义 = 死引用，跳过）
- 英文文本一手来源 = `.sndshd` 的 `description` 字段（3948 条 VO shader 全带台词全文）；辅助源 = Quake4[CC] 听障模组转写 archive.org 快照

### 自研 exporter 上线

- 替代引擎 `exportFont` 三大缺陷：bearing 烘位图 / xSkip 用真 advance / 尾字符不丢
- 废弃 48=24 复制、哨兵字符两个绕过

## v1.0.3 — 2026-07-17 凌晨

### 启动器

- 加 `+set logFile 2`（日志常开，报障直接发 `qconsole.log`）
- GTX 1650 稳 60 fps 默认关软阴影 `harm_r_softStencilShadow 0`

### 换图崩溃修复

- `rvSubtitles::Draw` 缓存 gui 裸指针跨图悬空 → CRT c0000409；改每帧按名 `FindGui`

## v1.0.2 — 2026-07-16 下午

### 第三轮反馈

- 字幕文本剥离 `{furrow}`/`{idle}` 等录音情绪标记（585 处保留在源 lang）
- 可听性门控：友军/敌军差异化 PVS+距离容差
- AI 无头模型走 `idAI::Speak` else 分支补挂 lipsync
- HUD 数字裁切根源分析：引擎运行时 `maxHeight = max(全部字形 top)`
- Strogg 两套字体全字库化（`chinese` 2048 宽）

## v1.0.1 — 2026-07-16 早

### 第二轮反馈

- 设置页问号根因：`gb1` 档只有 GB2312 一级，缺全角符号区；改用 `full` 档 = GB2312 全集 ∪ 主表实用字 ∪ ASCII
- 小队名全部中文化（Rhino→犀牛小队、Scorpion→天蝎小队等）

## v1.0.0 — 2026-07-16 深夜

### PoC 通过

- UI 2272 条 + 对白 3962 条全部翻译并部署（build_lang 99%）
- 字幕系统实装（`rvSubtitles` 单例 + LipSync/Game_local/AI 挂钩 + `subtitles.gui` 面板 + 3 个 cvar）
- 引擎选定 [idTech4A++ v1.1.0harmattan70](https://github.com/glKarin/com.n0n3m4.diii4a/tree/v1.1.0harmattan70)（master 与 h70 ABI 不兼容）
- 中文渲染链路打通：`sys_lang chinese` + `harm_gui_wideCharLang 1` + 5 个 lang（code/guis/lips/mappack/maps）+ 字体 fontdat/TGA + VO 路径别名 pk4
