# OsEasy-ToolKit v1.8.0

> 🎓 噢易多媒体网络教室工具箱 | 简易的课堂学习辅助工具箱

基于 [ZiHaoSaMa66/OsEasy-ToolBox](https://github.com/ZiHaoSaMa66/OsEasy-ToolBox) 的第三方增强版。

---

## ✨ 功能概览

| 模块 | 功能 |
|---|---|
| 🔪 进程管理 | 击杀学生端进程、循环守护、粘滞键劫持 |
| 🌐 网络管控 | 停止网络管控服务、关闭 USB 管控服务 |
| 📺 屏幕广播 | 解除控屏锁定、替换/还原屏幕广播程序 |
| 🖥️ DLL 管理 | 删除/恢复关键 DLL 文件、删除键盘锁驱动 |
| ⌨️ 快捷键 | 截图（GDI 纯原生，零依赖）、显示/隐藏工具箱、一言、打开数据目录 |
| ⚙️ 设置 | 开机自启、快捷键绑定、外观主题、自定义学生端路径 |
| 🛡️ UAC 提权 | 三级降级：fodhelper → eventvwr → UAC 弹窗 |

---

## 🚀 快速开始

### 下载

从 [Releases](https://github.com/NYSkyfox/OsEasy-ToolKit/releases) 下载最新 `ToolKit_v*.exe`。

### 运行

双击运行，程序会自动请求管理员权限（UAC）。

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
