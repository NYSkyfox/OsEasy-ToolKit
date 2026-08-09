# OsEasy-ToolKit

> 🎓 噢易多媒体网络教室工具箱 | 简易的课堂学习辅助工具箱

基于 [ZiHaoSaMa66/OsEasy-ToolBox](https://github.com/ZiHaoSaMa66/OsEasy-ToolBox) 的第三方版。

---

## ✨ 功能概览

工具箱包含 **7 个页面**，按左侧导航栏依次排列：

| 页面 | 功能 |
|---|---|
| 🔧 进程管理 | 击杀/挂起学生端进程、cmd 外部守护进程、粘滞键劫持、删除键盘锁驱动、根服务(MmPc)启停 |
| 📦 其他管理 | USB/网络管控解锁、DLL 文件恢复、关机劫持（解除强制关机）、自身脚本清理 |
| 📺 广播管理 | 替换/恢复屏幕广播拦截程序、窗口化或全屏运行广播命令、杀广播进程(ScreenRender) |
| 🔑 广播命令 | 由教师机 IP 生成远程命令、手动编辑/自动替换 IP 更新命令、从日志文件提取拦截的命令 |
| 🖥️ DLL 工具 | USB/网络管控实时状态查询、删除/恢复关键 DLL、删除键盘锁驱动 |
| ⚙️ 设置 | 主题模式（浅色/深色/跟随系统）、系统主题色、背景图片/字体/一言、快捷键开关 |
| ℹ️ 关于 | 版本信息、GitHub 仓库入口、当前提权方式（fodhelper / eventvwr / UAC / manifest） |

> 🛡️ **UAC 提权**：启动时自动三级降级尝试 — fodhelper 注册表绕过（静默）→ eventvwr 备选绕过 → 标准 UAC 弹窗。提权后自动清理注册表劫持，不影响系统正常行为。

---

## 🚀 快速开始

### 下载

从 [Releases](https://github.com/NYSkyfox/OsEasy-ToolKit/releases) 下载最新 `ToolKit_v*.exe`。

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
OsEasy-ToolKit/
├── main.py              # 程序入口
├── config.py            # 静态配置
├── build.py             # 打包脚本
├── build.bat            # 打包批处理（便捷调用）
├── requirements.txt     # 依赖
├── app.manifest         # UAC 提权清单
├── logo.ico / logo.svg  # 图标
├── Fake_SCR.py          # 屏幕广播替换脚本
└── src/
    ├── core/            # 核心配置、常量、辅助方法
    ├── gui/             # Flet 界面、快捷键管理
    ├── modules/         # 功能模块
    │   ├── killer.py              # 击杀脚本、守护进程
    │   ├── usb_network_unlock.py  # USB/网络解锁
    │   ├── broadcast_handler.py   # 屏幕广播处理
    │   ├── dll_manager.py         # DLL 管理
    │   ├── shutdown_hijack.py     # 关机劫持
    │   ├── service_manager.py     # 服务管理
    │   ├── process_manager.py     # 进程管理
    │   ├── file_handler.py        # 文件备份/恢复
    │   └── script_generator.py    # bat 脚本生成器
    └── utils/
        ├── program/      # 持久化开关、配置工具
        ├── system/       # 系统工具（cmd、日志、UAC、IFE、窗口）
        └── web/          # 网络工具（版本检查）
```

---

## 🛠️ 技术栈

- **GUI**: [Flet](https://flet.dev/)（基于 Flutter）
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
  <img src="https://img.shields.io/badge/版本-1.8.0-blue" alt="version">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="python">
  <img src="https://img.shields.io/github/stars/NYSkyfox/OsEasy-ToolKit?color=blue" alt="stars">
</p>
