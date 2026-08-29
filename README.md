# OsEasy-ToolKit

> 🎓 噢易多媒体网络教室工具箱 | 简易的课堂学习辅助工具箱

基于 [ZiHaoSaMa66/OsEasy-ToolBox](https://github.com/ZiHaoSaMa66/OsEasy-ToolBox) 的第三方版。

---

## ✨ 功能概览

工具箱包含 **10 个页面**，按左侧导航栏依次排列：

| 页面 | 功能 |
|---|---|
| 📊 概览 | 实时显示学生端路径/版本/进程/服务状态、功能劫持状态，每 3 秒自动刷新 |
| 🔧 进程管理 | 击杀/挂起学生端进程、cmd 外部守护进程、粘滞键劫持、关机/重启劫持 |
| ⚙️ 服务管理 | 学生端相关服务（MMPC/OeNetLimit/easyusbflt/KbFilter/ProcFireWall）启停 |
| 🔓 解锁管理 | 网络/USB/键盘鼠标/控屏/黑屏肃静的一键解锁或单项解锁 |
| 📺 广播管理 | 替换/恢复屏幕广播拦截程序、窗口化/全屏运行广播命令、广播日志监控、远程命令管理 |
| 🖥️ DLL 工具 | USB/网络管控实时状态查询、通过原生 DLL 启停管控 |
| 📁 文件管理 | OsEasy 关键文件备份与恢复（分组操作）、脚本文件清理 |
| ⚙️ 设置 | 背景图片/字体/一言/透明度、快捷键开关、窗口置顶 |
| ℹ️ 关于 | 版本信息、GitHub 仓库入口、当前提权方式(fodhelper / eventvwr / UAC / manifest) |
| 🚀 高级 | 按 IP/网段发送崩溃载荷，触发远端 Os-Easy 监控进程终止 |

> 🛡️ **UAC 提权**：启动时自动三级降级尝试 — fodhelper 注册表绕过（静默）→ eventvwr 备选绕过 → 标准 UAC 弹窗。

---

## 🚀 快速开始

### 下载

从 [Releases](https://github.com/NYSkyfox/OsEasy-ToolKit/releases) 下载最新 `OsEasyToolKit`。

### 运行

双击运行，程序会自动请求管理员权限。

### 开发

```bash
git clone https://github.com/NYSkyfox/OsEasy-ToolKit.git
cd OsEasy-ToolKit
pip install -r requirements.txt
python main.py
```

### 打包

```bash
python build.py
```

构建脚本自动下载 UPX 压缩、安装依赖、注入构建日期，输出 `dist/ToolKit_v版本号_哈希.exe`。

---

## 📁 目录结构

```
OsEasy-Trainer/
├── main.py                  # 程序入口
├── config.py                # 静态配置
├── build.py                 # 打包脚本
├── build.bat                # 打包批处理
├── dev.bat                  # 开发快捷启动
├── requirements.txt         # 依赖
├── app.manifest             # UAC 提权清单
├── logo.ico / logo.svg      # 图标
├── Fake_SCR.py              # 屏幕广播替换脚本
├── Install_Student_test.bat # 学生端安装测试
│
├── tests/
│   └── test_persistent_switch.py
│
├── docs/
│   └── ...
│
└── src/
    ├── core/                # 核心层：配置、路径、状态、UI 桥接
    │   ├── settings.py      # 运行时配置读写（RuntimeConfig 类）
    │   ├── paths.py         # 路径常量 + ensure_dirs()
    │   ├── state.py         # 全局运行时状态标志
    │   ├── bridge.py        # UI 回调桥接（pass_ui_class / show_snack）
    │   └── constants.py     # 向后兼容 re-export
    │
    ├── utils/               # 工具层：纯系统能力，零 UI 依赖
    │   ├── cmd.py           # 命令行执行（run_single_cmd / runbat）
    │   ├── process.py       # 进程控制（枚举/挂起/恢复/终止）
    │   ├── service.py       # 服务控制（SCM API）
    │   ├── ifeo.py          # IFEO 注册表劫持
    │   ├── logger.py        # 日志系统
    │   ├── uac.py           # UAC 提权（三级降级）
    │   ├── aumid.py         # AUMID 注册（Toast 来源）
    │   ├── fs.py            # 文件系统工具（时间/路径/文件存在）
    │   ├── network.py       # 网络工具（IP 获取 / GitHub 跳转）
    │   ├── screenshot.py    # 截图工具（纯 GDI）
    │   └── display.py       # 资源路径/字体/主题色
    │
    ├── gui/                 # GUI 层：界面基础设施 + 页面
    │   ├── app.py           # Ui 主类（窗口框架 + 标签页 + 生命周期）
    │   ├── hotkey.py        # 全局快捷键管理（pynput）
    │   ├── switch.py        # 持久化开关控件（PersistentSwitch）
    │   └── pages/
    │       ├── overview.py       # 概览页（实时状态）
    │       ├── process.py        # 进程管理页
    │       ├── service.py        # 服务管理页
    │       ├── unlock.py         # 解锁管理页
    │       ├── broadcast.py      # 广播管理页
    │       ├── dll.py            # DLL 工具页
    │       ├── backup.py         # 文件管理页
    │       ├── settings.py       # 设置页
    │       ├── about.py          # 关于页
    │       └── advanced.py       # 高级页（远程崩溃）
    │
    └── modules/             # 业务层：功能逻辑，编排 utils
        ├── student_detector.py   # 学生端检测（路径 + 版本）
        ├── killer.py             # 击杀脚本 + 守护进程 + 粘滞键劫持
        ├── service_manager.py    # 服务管理（MMPC 控制）
        ├── unlock_native.py      # 解锁实现（原生 winreg + 服务/进程控制）
        ├── broadcast_handler.py  # 广播处理（日志解析 + 窗口控制 + 监控）
        ├── dll_manager.py        # DLL 调用封装
        ├── file_handler.py       # 文件备份/恢复/清理
        ├── power_control.py      # 电源管控（关机/重启劫持）
        ├── remote_crasher.py     # 远程崩溃
        ├── student_launcher.py   # Student.exe 启动器（IFEO 摘权）
        ├── script_generator.py   # 击杀/删文件脚本生成
        └── script_templates.py   # bat 脚本模板
```

---

## 🛠️ 技术栈

- **打包**: PyInstaller + UPX
- **热键**: pynput
- **进程管理**: psutil
- **UAC 提权**: fodhelper / eventvwr registry bypass

---

## 📝 更新日志

详见 [Releases](https://github.com/NYSkyfox/OsEasy-ToolKit/releases)。

---

## ⚠️ 免责声明

本工具仅供学习交流使用，请遵守当地法律法规及学校规章制度。使用者自行承担一切后果。

---

## 📄 开源协议

[MIT License](https://github.com/ZiHaoSaMa66/OsEasy-ToolBox) — 继承自上游项目。

---

<p align="center">
  <img src="https://img.shields.io/badge/版本-1.9.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python">
  <img src="https://img.shields.io/github/stars/NYSkyfox/OsEasy-ToolKit?color=blue" alt="Stars">
</p>
