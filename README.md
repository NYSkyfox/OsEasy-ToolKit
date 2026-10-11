# OsEasy ManagerHelper

噢易（Os-Easy）极域多媒体电子教室 —— **管控解除 / 行为改造** 工具集（解耦式结构 + GUI）。

> 仅依赖 Python 3.8+ 标准库，无需 pip 安装任何第三方包。
> 定位：以**字节 patch** 为核心的逆向工程产物集合，用于在授权测试环境中解除/改造学生端管控行为。

## 功能

| 模块 | 类型 | 作用 |
|---|---|---|
| **禁用教学管控** | 固定偏移 patch | patch `MultiClient.exe`，使教师端下发的 键鼠锁 / 行为管控（网络·USB·程序）指令失效；屏幕广播点可选 |
| **屏幕广播窗口化** | 固定偏移 patch | patch `ScreenRender.exe`，强制 `--fullscreen=0`，广播始终以可拖拽/可缩放窗口启动（广播保留） |
| **双开教师端 / 学生端** | PE+VA patch | patch `Teacher.exe` / `Student.exe` 的互斥检测原语（OpenEventW 恒返回 0），实现两端同时运行 |
| **阻止 / 使用假屏幕截图** | PE+VA+shellcode | patch `StudentLogic.dll`：NOP 停止截屏发送，或用本地 BMP 替换 BitBlt（教师端显示固定假画面） |
| **拦截远程关机 / 重启** | PE+VA patch | patch `Student.exe` 的 `FUN_004a9660` 入口，拦截教师端 远程重启 / 远程关机 指令；支持文件版（持久）与内存版（抗 ASLR） |

## 运行

```bash
python main.py
```

GUI：`tkinter + ttk`（vista 主题），顶部导航栏 + 下部内容区，四个页面：主页 / Patch / 双开 / 截屏。

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
│   ├── core/                # ── 核心层 ──
│   │   ├── paths.py         #     安装目录探测 + 数据目录
│   │   ├── fingerprint.py   #     MD5 / 大小指纹
│   │   └── patch_engine.py  #     PatchPoint/PatchTarget/PatchEngine（apply/restore/status/dry_run）
│   │
│   ├── patches/             # ── 固定偏移 patch（注册表驱动） ──
│   │   ├── multiclient_disable.py    # 禁用教学管控
│   │   └── screenrender_windowed.py  # 屏幕广播窗口化
│   │
│   ├── modules/             # ── PE+VA+shellcode 型工具（独立维护） ──
│   │   ├── duo_open.py            # 双开教师端/学生端
│   │   ├── screen_capture.py      # 阻止/使用假屏幕截图
│   │   └── noshutdown.py          # 拦截远程关机/重启（文件版+内存版）
│   │
│   └── gui/                 # ── 界面层 ──
│       ├── app.py           #     主框架（顶部导航 + 内容区 + 状态栏）
│       ├── style.py         #     ttk 主题（vista）
│       ├── widgets.py       #     通用控件（滚动容器 / 日志框）
│       └── pages/
│           ├── page_overview.py   # 主页（环境 + 状态 + 快捷入口）
│           ├── page_patches.py    # Patch 管理
│           ├── page_duo.py        # 双开
│           ├── page_capture.py    # 截屏
│           └── page_noshutdown.py # 拦截远程关机/重启
│
├── tests/                   # （预留）
└── docs/patches/            # 逆向 patch 点文档
```

## 分层约定

- **core**：纯逻辑，零 UI 依赖。`patch_engine` 是统一引擎，GUI 与 CLI 共用。
- **patches**：固定偏移 patch 目标，每个文件定义一个 `PatchTarget` 并注册到 `__init__.ALL_TARGETS`；新增工具 = 加一个文件 + 一行注册，GUI/CLI 自动发现。
- **modules**：`PE+VA+shellcode` 型工具，逻辑与偏移型差异大，独立维护、自带核心函数。
- **gui**：只负责展示与交互，调用 core/patches/modules，不含业务逻辑。

## 安全说明

- 所有 patch 前**自动备份**（`*.bak` / `*.duo_open.bak`），还原从备份恢复，字节级校验。
- 指纹（MD5）与大小校验，版本不匹配时按字节校验继续并二次确认（风险自担）。
- 仅供**授权测试环境**使用，请勿用于未授权场景。

## 逆向文档

各 patch 点的函数定位、字节依据、dry-run 验证结果见 `docs/patches/`。