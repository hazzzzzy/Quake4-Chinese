---
name: quake4-font-aspect-and-size
description: 第五轮（2026-07-17）：字体拉伸根因=引擎 GUI 640×480 虚拟坐标拉到宽屏（横向多拉 4/3）→ 导出器 ASPECT=0.75 预压缩；字体体积 1067MB→131MB（RLE TGA + 同源家族 .mtr 材质别名共享贴图）
metadata:
  node_type: memory
  type: project
  originSessionId: af264300-0f3e-460f-9332-cd68c241bb86
---

Quake 4 汉化第五轮修复（承接 [[quake4-feedback-fixes-r4]]），字体拉伸与体积两项均已修复并实机验证。

**Why:** 拉伸是引擎级机制（所有 GUI 文本都受影响），换字体/重导必然再遇到；材质别名与 RLE 的引擎侧依据查证过源码，勿重新怀疑。

**How to apply:**

- **拉伸根因**：引擎全部 GUI 按 640×480 虚拟坐标绘制，idDeviceContext::AdjustCoords 把 x/w 乘 屏宽/640、y/h 乘 屏高/480（DeviceContext.cpp:456-485）——1080p 下横向 3.0 vs 纵向 2.25，多拉 4/3，方块汉字被拉扁宽（实测屏显比 1.33）。原版英文一直如此，窄拉丁字形不显眼。**与导出器无关，老字库同样拉伸**。
- **修复**：export_font.py 增加 `ASPECT = 0.75`（=(640/480)/(1920/1080)），字形位图宽度（LANCZOS 缩放，bearing 等比）与 xSkip 都预乘，ASCII 同步压缩保证混排节奏。实测屏显比恢复 0.94–1.04。**仅对 16:9 正确，换非 16:9 屏需按 (4/3)/(屏宽/屏高) 改 ASPECT 重导**。引擎自带 r_scaleMenusTo43 只修主菜单且加黑边（HUD/字幕不生效），未采用。
- **体积优化（1067MB→131MB 磁盘，显存同比例降）**：
  - TGA 改 RLE（type 10）：引擎 LoadTGA 支持（Image_files.cpp:723，含 0x20 顶向下翻转 :825）；逐行等值区段全编 RLE 包。
  - 同源家族共享贴图：4 套 UI 家族（都是 msyh）只渲染 chain 一套，r_strogg 复用 strogg。宽表 shaderName 只存"1_24.tga"后缀、家族前缀是引擎运行时用 fontName 拼的（tr_font.cpp:616/632），故 alias 家族 fontdat=本尊字节复制；材质用松散 `materials/zzz_chinese_font_alias.mtr` 显式 decl（名字=引擎拼出的含 .tga 后缀全名，如 fonts/chinese/marine_1_24.tga），模板照抄 idMaterial::SetDefaultText（blend blend/colored/map/clamp），map 指向本尊贴图；显式 decl 优先于隐式生成（FindMaterial），引擎按 image 路径去重 → 显存只留一份。基础段材质名=fontName_字号.tga（tr_font.cpp:557）也要别名。
- **验证（3/3 通过，无字体告警）**：主菜单 48 号（marine/profont 别名）、字幕 12 号（lowpixel 别名+断行自适应，Voss 长句单行放下）、Strogg 医疗站（strogg 家族），poc_zh_menu.cfg / poc_verify_fonts.cfg 帧驱动截图 shot00227-232。
- **待用户决策**：旧字库备份 fonts/chinese_bak_r4（943MB）、chinese_strogg_bak（1MB）是否删除；换字体只需改 FAMILIES 一行重跑（几分钟），若公开发布补丁注意微软雅黑位图再分发有版权风险（思源黑体/HarmonyOS Sans/MiSans 等开源/免费商用字体无此问题）。
