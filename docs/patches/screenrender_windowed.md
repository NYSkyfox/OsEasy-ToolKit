# ScreenRender.exe —— 屏幕广播窗口化 patch 点

## 样本
- 文件：`ScreenRender.exe`（屏幕下行渲染器，FFmpeg 解码 + SDL2 渲染）
- MD5：`76cfa20119b247685827d9341132570a`
- 大小：`450048` B
- PE32，ImageBase `0x400000`

## 背景
`ScreenRender.exe` 由 MultiClient/StudentLogic 以 `--fullscreen N` 参数拉起。
构造函数 `FUN_0041c7d0`（构造 `ScreenRenderApp`）把命令行 `--fullscreen` 值写入
`this+0x844`：

- `1` = 全屏（`WS_POPUP` = `0x80000000`）
- `0` = 窗口（`0xc40000`）
- `2` = 窗口（缩放）

默认教师端下发 `--fullscreen 1`（全屏）。窗口化代码路径**已存在**，只需强制
读到的参数值为 0。

## Patch 点

| 项 | 值 |
|---|---|
| 位置 | `FUN_0041c7d0`，file_off `0x1BDA6` |
| 原指令 | `8b 45 58`（`mov eax,[ebp+0x58]`，读 `--fullscreen` 参数值） |
| 新指令 | `31 c0 90`（`xor eax,eax; nop`，强制 0） |
| 语义校验 | 紧随 off `0x1BDA9` 处须为 `89 82 44 08 00 00`（`mov [edx+0x844],eax`） |

## 说明
- 该 patch 点读参数 → 紧随其后的 store 写入 `this+0x844`，语义校验确保定位正确。
- 窗口化尺寸 = 屏宽 × 3/4（`==0` 分支里 `nWidth*3>>2`），会是个较大窗口；
  如需更小/可自由缩放的窗口，可能需额外 patch 尺寸计算（待实机确认）。

## 验证
`8b 45 58` 3 字节 → `31 c0 90`，dry-run 写入 + 语义 store 校验 + 读回 + 还原
零残留，字节级通过。