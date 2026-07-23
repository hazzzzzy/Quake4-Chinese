---
name: quake4-feedback-fixes-r4
description: 第四轮修复（2026-07-16 晚）：读档崩溃根因=hud.gui 覆盖必须基于 pak021 底稿/字幕换行按 fontdat 真实度量/无线电 decl 缺口全游戏审计 252 条/MSVC 中文字面量 GBK 坑/引擎自动化测试方法论
metadata:
  node_type: memory
  type: project
  originSessionId: e42aed6b-d0af-4b59-b9bc-ed2bf1d0b864
---

Quake 4 汉化第四轮修复（承接 [[quake4-feedback-fixes-r3]]），三项反馈全部定位，两项已修复部署，一项为原版资产缺口待决策。

**Why:** 读档崩溃的根因链极易复发（任何 gui 覆盖改动都会踩），排查中还推翻了上轮"全屏环境问题"的错误结论，必须记录完整证据链与纪律。

**How to apply:**

- **读档崩溃根因（重大）**：idTech4 存档按 GUI 源文件结构逐窗口顺序序列化 HUD 状态（idWindow::WriteToSaveGame，无长度前缀，仅 SyncId 校验），**结构不匹配→状态流错位→内存踩坏→概率性崩在引擎 exe 后续资源加载**（偏移 0x6af7ed/0x30b8c0，官方 DLL 同样崩）。上轮 hud.gui 覆盖基于 pak001 版底稿（2272 行），而运行时原版是 **pak021 版（2507 行，1.4 补丁，q4base 有 4 份 hud.gui，加载序最高者生效）**——结构差 235 行。修复：patch_hud.py 底稿换 pak021（固化在 `D:\data\quake4-cn\assets\hud_pak021_stock.gui`），**gui 覆盖只允许改数值（rect/textscale），禁止增删 windowDef/脚本/变量**；纯数值差异与存档兼容（已 3/3 验证）。上轮"全屏环境问题"结论是错的（混淆变量：那些实验全用旧结构存档）；全屏本身 6/6 干净。
- **错配存档的表现**：旧档（原版结构）+新覆盖=正常加载但 HUD 恢复存档时的旧 rect/旧语言文本（外观回退，换图恢复）；**用 pak001 版覆盖存的档（用户 checkPoint/a0717，2026-07-16 15:41）与现行 pak021 覆盖错配，加载约五成崩且侥幸加载也可能带隐性状态污染，不可信**。旧档主线：202607162054 / rescue2054 全部正常。
- **字幕换行修复**：Subtitles.cpp 改为按真实屏幕宽度断行——DLL 启动时经 fileSystem 解析 `fonts/chinese/lowpixel_12.fontdat`（结构见 tools/parse_fontdat.py：基础段 256×9float+5float，宽表头 20B+numIndexes+indexes+numGlyphs+68B/字形，xSkip 在 float[2]），逐字符累计 xSkip×useScale（0.19×48/12=0.76），行预算 SUB_TEXT_W=434px（gui 文本区 448 留禁则余量）。实测 CJK xSkip=13→9.88px/字→43 字/行（原 MAX_UNITS=58 半角只用了 64% 面板宽）。中英混排空格断行已实机截图验证。
- **无线电字幕 decl 缺口（已补齐，2026-07-17 凌晨）**：全游戏 336 条 func_radiochatter 台词原版仅 84 条有 lipsync decl。**英文文本一手来源 = .sndshd 的 description 字段**（全游戏 3948 条 VO shader 全带台词全文，块头格式 `sound <名> {`），辅助源 = Quake4[CC] 听障模组转写（原站已死，archive.org 快照 `web/20120209143213/http://gamescc.rbkdesign.com/mods/q4cc_v1.3.zip`，.dcc 按音频文件名给多段转写——sndshd 只有主段，音频含基地警报等次段时用 CC 补）。252 条中 251 条补齐（vo_1_2_20_50_1 全资产无定义=死引用），管线：`translations/radio_chatter.tsv`（str_380000-380250，三代理并译+同句复用 dialogue_lips 已审译文）→ `tools/gen_radio_decls.py` 生成松散 `savedata\q4base\lipsync\zz_chinese_radio.lipsync`（最小 decl 只需 description+text，rvDeclLipSync::Parse 其余字段可省；**跨地图重复声音要去重**否则引擎刷 previously defined 警告）→ `build_lang.py` 已扩展将 radio 表并入 chinese_lips.lang（4213 条）。实机验证通过。剩余缺口类别：非 radiochatter 的广播（如基地 PA `1_1_0_*` 声库）走 speaker/脚本，无字幕挂点，未纳入。
- **断行贪心 bug 修复（r5）**：空格断点只在行预算 70% 之后才可取（中西文混排中"瘫痪了 Strogg 的"前部空格曾把整行断到 30%），溢出点落在英文单词中间时才允许回退任意空格防断词。实机验证 Voss 长句满宽换行。
- **译文修正**：str_300727 "We're clear!"（登机完毕语境，下句是发射倒计时）误译"我们摆脱了！"→"全员就位！"（用户指出）。
- **中西文空格是术语表第七条排版规范**（用户审定过的定稿），非残留 bug；用户再次质疑，是否取消待其拍板。截图里拉丁字母间距松散是中文字库里英文字形自带步进，非文本空格。
- **自研字体导出器已上线（2026-07-17，quake4-cn/tools/export_font.py，实机回归通过）**：PIL+fontTools 重产全部 6 家族×12/24/48 fontdat+TGA 图集，bearing 烘进位图、xSkip=真 advance、基础段（ASCII/Latin-1）同 TTF 自渲染独立单页 fonts/chinese/<家族>_<字号>.tga（引擎硬编码该名为基础段材质）——**曾试过拼接原版英文段恢复原版美术，但原版 marine 是小型大写风格，与雅黑混排参差不齐，用户否决，中英统一雅黑**；标点修形：U+2014 拉伸满格（——连线不断，NEAREST 保硬边）、U+2014/U+2026 垂直居中到 CJK 视觉中线（以"中"字 ink 中心为基准）；字体定案 msyh.ttc 常规体（粗体 msyhbd 在 12 号单色下笔画粘连锯齿重，用户要求换瘦体；再换可选 Deng 等线）；**渲染最终定案：SS=2 全档超采样**（用户拍板）——位图按 2 倍字号 AA 渲染进贴图、度量按名义字号写整数（裁剪边界对齐 SS 倍数防半像素基线抖动、UV 覆盖 2x 区域），引擎双线性过滤缩小采样完成抗锯齿；解决位图字体"源<屏显尺寸放大出锯齿"（名牌/HUD/医疗站/字幕）。三代演进教训：1x 灰度 AA=小字发虚参差（否）→ 1x 单色=小字锐利但放大锯齿（否）→ **2x AA 超采样=两全（定案）**。代价贴图 1054MB 磁盘/约 900MB 显存——**已被第五轮优化推翻：.mtr 材质别名可跨家族共享贴图 + RLE，降到 131MB，见 [[quake4-font-aspect-and-size]]**；单色模式代码路径保留（draw.fontmode='1'，现未用）——引擎老导出器就是 1-bit 单色，硬边像素+笔画网格对齐才是原有观感；PIL 默认灰度 AA 在小字号发虚、浓淡不一，用户评"参差不齐/丑"两轮否决（AA+原版英文拼接、AA+雅黑统一都被否），mono hinting 与 AA 的度量差 ±1px，须画到宽裕画布后按实际墨迹重算 w/top；基础段只渲染 ASCII 32-126——引擎存在按字节绘制的老路径（启动屏 LOADING/INITIALIZING 系列 str_104343/104346-51），Latin-1 高位字形会把 UTF-8 字节显形成乱码，该组字符串已在 ui_code.tsv 置空 zh 回退英文（备注 en-only）；宽表只收 charcode≥256（GLYPH_END=255 以下永远走基础段）；真 48 号（引擎按槽位 glyphScale=48/48=1，旧"48=24 复制"导致大字号减半，已修正；48 号用 UI 字符集 1138 字省显存）；新字库运行时 maxHeight 与英文原版差 ≤3（chain24 Δ=+1），**HUD 数字裁切根源消失，patch_hud.py 已裁剪为只剩无线电两行修正**；字幕断行 DLL 运行时读新 fontdat 自适应（CJK advance 13→12）。UI 字体源=系统 msyhbd.ttc（保证新增翻译字符全覆盖），Strogg=zh_glow_norm.ttf（子集，缺字回退 ?）。旧字库备份 fonts/chinese_bak_r4。exportFont 的哨兵字符/48 复制两个绕过就此废弃。
- **字符间隙忽宽忽窄的根因（已诊断并被上述导出器修复）**：三层引擎侧机制叠加——(1) DrawText/PaintChar 从不读字形 bearing（pitch 字段全工程无人使用），字形位图画在字元格左缘，空白全堆右侧；(2) exportFont 用 FT 紧贴位图（丢 bearing）且宽度按 4px 对齐量化 `(w+3)&-4`，实测 lowpixel_12 的"目" ink=8/skip=13 右空 5px 而多数字 ink=12 右空 1px（marine_24 更甚：目空 7px、标/移 空 -1 重叠）→ 菜单/字幕"目 标"式伪空格；(3) exportFont 手加 xSkip=advance+1 整体偏松。RAVEN SOFTWARE 开场分散=同机制+ASCII 字形已是雅黑（原版特制窄体）+gui 按原字体调的 textspacing。引擎 exe 不可改，修复方向：Python 自研导出器（fontTools/PIL）重产 fontdat+TGA 图集——bearing 烘进位图、xSkip 用真 advance、可顺带拼接原版英文 base-256 段（字形 shaderName 指回原版贴图，ASCII 恢复原版美术）并消灭 48=24 复制与哨兵字符两个绕过。fontdat 逐字形自带 32B 材质名，拼接可行。
- **MSVC 中文字面量坑**：窄字符字面量按系统码页（GBK）编进二进制，与 UTF-8 运行时数据比较永远不等——Subtitles.cpp 的"未命名"过滤曾因此失效（过场出现"未命名:"前缀），必须写显式 UTF-8 转义 `"\xE6\x9C\xAA\xE5\x91\xBD\xE5\x90\x8D"`。
- **引擎自动化测试方法论**：keybd_event 合成按键对 SDL 无效（按扫描码解键），bind 驱动不可靠；改用**纯 cfg 帧等待驱动**（wait N 帧 + trigger/screenshot/quit 顺序编排）。cfg 里 `set` 中文值必须**加引号**否则静默失效。`trigger <实体名>` 在 loadGame 后可直接用。airdefense1 开场过场 >3 分钟，devmap 后截 HUD 需等足。判定崩溃看 Application 事件日志 Id=1000 + qconsole.log 尾部；批测时临时 HKLM WER DontShowUI=1（测完还原）。
- **r4b DLL 已部署**（含 r3 全部修复+换行+未命名过滤+decl 缺失调试日志 `[SUB] radio: no lipsync decl`）；可听性门控实测工作正常（[SUB] skip dist 912>max 900）。哨兵字符（U+FFE5）使 numIndexes=65510。
- 右上角"传入/通讯"首字被波形图标（rect 513,7,41,25）遮挡已随 pak021 重打修复：t_radio1/2 x 545→557、宽 81→69（纯数值，存档安全）；视觉待用户下次无线电时确认。
- **一键直达开场脚本**：`D:\data\Quake 4\tmp\scripts\run_q4_start.cmd`（全屏中文 + 命令行 `+loadGame gamestart` 直达，实测 9 秒进游戏）；`gamestart` 存档 = airdefense1 开场过场结束刚获得操控权（坠毁船旁，血 72），由 poc_make_startsave.cfg 制作（devmap + wait 12600 帧等过场自然放完 + saveGame，过场约 200 秒不可跳过——skipCinematic 只有玩家 ESC 输入路径，无控制台命令）。
