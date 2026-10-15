# OsEasy ManagerHelper

噢易（Os-Easy）极域多媒体电子教室 —— **管控解除 / 行为改造** 工具集（解耦式结构 + GUI）。

> 仅依赖 Python 3.8+ 标准库，无需 pip 安装任何第三方包。
> 定位：以**字节 patch** 为核心的逆向工程产物集合，用于在授权测试环境中解除/改造学生端管控行为。

## 功能

| 模块 | 类型 | 作用 |
|---|---|---|
| **禁用行为管控** | 固定偏移 patch | patch `MultiClient.exe` 行为管控（网络·USB·程序）入口，指令在学生机失效 |
| **禁用屏幕广播** | 固定偏移 patch | patch `MultiClient.exe` 屏幕广播入口（画面不再被截取）；**可勾选一并封禁键鼠锁** |
| **屏幕广播窗口化** | 固定偏移 patch | patch `ScreenRender.exe`，强制 `--fullscreen=0`，广播始终以可拖拽/可缩放窗口启动（广播保留） |
| **双开教师端 / 学生端** | PE+VA patch | patch `Teacher.exe` / `Student.exe` 的互斥检测原语（OpenEventW 恒返回 0），实现两端同时运行 |
| **阻止 / 使用假屏幕截图** | PE+VA+shellcode | patch `StudentLogic.dll`：NOP 停止截屏发送，或用本地 BMP 替换 BitBlt（教师端显示固定假画面） |
| **拦截远程关机 / 重启** | PE+VA patch | patch `Student.exe` 的 `FUN_004a9660` 入口，拦截教师端 远程重启 / 远程关机 指令；支持文件版（持久）与内存版（抗 ASLR） |
| **教师端 加密狗 / 点数限制 解除** | 锚点 / VA / 配置 | 教师端授权解除组合工具（4 方案可多选）：解除连接数上限[MainLogic.dll]、恒判有狗[Teacher.exe]、消除"未找到加密狗"弹窗[Teacher.exe]、改 `core.conf /Limit/` 并重签 |

## 运行

```bash
python main.py
```

GUI：`tkinter + ttk`（vista 主题），顶部导航栏 + 下部内容区，两个页面：主页 / Patch（统一 Patch 页含全部 7 个 patch 目标，按目标切换详情面板）。

## 项目结构（解耦式）

```
OsEasy-ManagerHelper/
├── main.py                  # 入口（启动 GUI）
├── config.py                # 全局常量 + 功能描述
├── requirements.txt         # （仅标准库，占位）
├── .gitignore
├── README.md
│
├── src/
│   ├── core/                # ── 核心层：纯逻辑，零 UI 依赖 ──
│   │   ├── paths.py         #     安装目录探测 + 数据目录
│   │   ├── fingerprint.py   #     MD5 / 大小指纹
│   │   ├── patch_engine.py  #     固定偏移型引擎（PatchTarget/PatchEngine）
│   │   ├── va_patch.py      #     VA 型统一执行器（PE 解析 / shellcode / 内存版 / BMP）
│   │   └── dog_patch.py     #     教师端授权解除执行器（anchor/multi/va/config 四定位）
│   │
│   ├── patches/             # ── 全部 patch 目标：纯配置（无执行逻辑） ──
│   │   ├── __init__.py          #   注册表：ALL_TARGETS(固定偏移) + VA_TARGETS(VA型) + DOG_SOLUTIONS
│   │   ├── multiclient_disable_behaviorcontrol.py  # 禁用行为管控（固定偏移）
│   │   ├── multiclient_disable_screenrender.py     # 禁用屏幕广播·含可选键鼠锁（固定偏移）
│   │   ├── screenrender_windowed.py                # 屏幕广播窗口化（固定偏移）
│   │   ├── duo_open.py                 # 双开教师端/学生端（VA）
│   │   ├── screen_capture.py           # 阻止/假截图·nop+shellcode（VA）
│   │   ├── noshutdown.py               # 拦截关机/重启·文件+内存版（VA）
│   │   └── dog_license.py              # 教师端加密狗/点数解除·4方案（anchor/multi/va/config）
│   │
│   └── gui/                 # ── 界面层 ──
│       ├── app.py           #     主框架（顶部导航 + 内容区 + 状态栏）
│       ├── style.py         #     ttk 主题（vista）
│       ├── widgets.py       #     通用控件（滚动容器 / 日志框）
│       └── pages/
│           ├── page_overview.py   # 主页（环境 + 状态 + 快捷入口）
│           ├── page_patches.py    # 统一 Patch 页（目标下拉 + 动态面板 + 共享日志）
│           └── patch_panels/      #   一个下拉项 = 一个面板文件（纯展示 + 调执行器）
│               ├── multiclient_disable_behaviorcontrol.py
│               ├── multiclient_disable_screenrender.py
│               ├── screenrender_windowed.py
│               ├── teacher_student_double_open.py
│               ├── student_fake_screenshot.py
│               ├── fake_shutdown.py
│               └── dog_license.py                 # 教师端授权解除（目录+方案勾选+批量）
│
├── tests/                   # engine / noshutdown / dog 往返 + gui build-only
└── docs/patches/            # 逆向 patch 点文档
```

## 分层约定

- **core**：纯逻辑，零 UI 依赖。三套执行器：
  - `patch_engine`（固定偏移型）：`PatchTarget` + `PatchEngine`，GUI/CLI 共用。
  - `va_patch`（VA 型统一执行器）：`VAPatchExecutor`，含 PE 解析 / VA→偏移 / shellcode 生成 / 内存版 / BMP 处理，是**唯一**执行 VA 型 patch 的入口。
  - `dog_patch`（教师端授权解除执行器）：`DogPatchExecutor`，承载 `anchor`（唯一锚点+双态）/ `multi`（一文件多锚点）/ `va` / `config`（文本改值+MD5 重签）四种定位范式，VA 复用 `va_patch.PE`。
- **patches**：全部 patch 目标的**纯配置**（无执行逻辑），平级存放，按驱动执行器分三组注册于 `__init__.py`：
  - 固定偏移型：每个文件一个 `PatchTarget` → `ALL_TARGETS`，由 `patch_engine.PatchEngine` 执行。
  - VA 型：每个文件一个 `VA_PatchTarget` → `VA_TARGETS`，由 `va_patch.VAPatchExecutor` 执行。
  - 教师端授权解除：`dog_license` 4 个 `DogSolution` → `DOG_SOLUTIONS`，由 `dog_patch.DogPatchExecutor` 执行。
  新增工具 = 加一个配置文件 + 一行注册，GUI 自动发现。
- **gui**：只负责展示与交互，调用 core 执行器 + 读取 patches 配置，不含业务逻辑。所有 patch 目标统一在 **Patch 页**（目标下拉 → 动态重建详情面板 → 共享日志），**一个下拉项 = 一个面板文件**（`patch_panels/<id>.py`，类名 = id 的 PascalCase）；新增目标 = 建一个面板文件 + 在 `patch_panels/__init__.REGISTRY` 登记一条，下拉框自动出现。

## 安全说明

- 所有 patch 前**自动备份**（`*.bak` / `*.duo_open.bak`），还原从备份恢复，字节级校验。
- 指纹（MD5）与大小校验，版本不匹配时按字节校验继续并二次确认（风险自担）。
- 仅供**授权测试环境**使用，请勿用于未授权场景。

## 逆向文档

各 patch 点的函数定位、字节依据、dry-run 验证结果见 `docs/patches/`。