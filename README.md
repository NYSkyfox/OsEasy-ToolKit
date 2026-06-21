# OsEasy-ToolKit

基于 Python Tkinter 重构的「噢易」工具箱，用于噢易多媒体教学系统学生端的解锁与管理。
之所以使用 Python Tkinter 重构，是因为学校机房的网速慢到极点，原版即使 38mb 的工具箱也要下载很久（非GitHub，用的是第三方不限速网盘）。便于是基于 [ZiHaoSaMa66](https://github.com/ZiHaoSaMa66) 的 [OsEasy-ToolBox](https://github.com/ZiHaoSaMa66/OsEasy-ToolBox) 重构。

## 特点

- ✅ **解耦架构** - 配置、服务、页面完全分离
- ✅ **tkinter + ttk GUI** - 体积极小的 GUI 框架
- ✅ **配置信息统一管理** - 所有版本信息集中在 `config.py`
- ✅ **模块化服务** - 学生端、MMPC、解锁、广播、DLL 各服务独立
- ✅ **页面组件化** - 6 个功能页面各自独立

## 项目结构

```
OsEasy-ToolKit/
├── main.py                  # 入口
├── app.py                   # 主应用类
├── config.py                # 全局配置
├── build.py                 # 打包脚本
├── requirements.txt         # 依赖
├── Fake_SCR.py              # 假 ScreenRender 程序
├── pages/                   # GUI 页面
│   ├── __init__.py
│   ├── base_page.py         # 页面基类
│   ├── process_page.py      # 进程管理
│   ├── unlock_page.py       # 解锁管理
│   ├── broadcast_page.py    # 广播管理
│   ├── command_page.py      # 广播命令
│   ├── dll_page.py          # DLL 工具
│   └── about_page.py        # 关于
├── services/                # 业务逻辑
│   ├── __init__.py
│   ├── student.py           # 学生端服务
│   ├── mmpc.py              # MMPC 服务
│   ├── unlock.py            # 解锁服务
│   ├── broadcast.py         # 广播服务
│   ├── dll_utils.py         # DLL 调用
│   ├── network.py           # 网络服务
│   └── usb.py               # USB 服务
└── utils/                   # 通用工具
    ├── __init__.py
    ├── admin.py               # 管理员权限
    ├── process.py             # 进程操作
    └── helpers.py             # 辅助函数
```

## 使用

### 安装依赖

```bash
pip install -r requirements.txt
```

### 开发运行

```bash
python main.py
```

### 打包发布

```bash
# 正式版本（无控制台）
python build.py

# 调试版本（带控制台）
python build.py --debug

# 仅清理
python build.py --clean
```

## 功能说明

### 进程管理
- 挂起/恢复学生端进程
- 切换 MMPC 根服务
- 重启学生端
- 粘滞键后门注册/移除

### 解锁管理
- 删除键盘锁/控屏/黑屏安静
- 解锁网络限制
- 解锁 USB 限制
- 备份/恢复关键文件

### 广播管理
- 替换 ScreenRender 拦截命令
- 窗口化/全屏广播
- 杀死广播进程
- 快捷键支持

### 广播命令
- 手动输入/编辑命令
- 从教师机 IP 生成
- 从日志文件提取
- 导入/导出命令

### DLL 工具
- USB 管控启动/停止/状态查询
- 网络管控开启/关闭

## 信息

信息定义在 `config.py` 中，例如：

```python
VERSION = "1.0.0"
APP_NAME = "OsEasy-ToolKit"
FULL_TITLE = f"{APP_NAME} v{VERSION}"
```

## 注意事项

- 需要以管理员权限运行
- 适用于噢易 V10.8+学生端
- 使用前请确保已备份重要文件
- 若在学校因使用工具箱被物理制裁，一切责任与作者无关

## 开源

基于 [OsEasy-ToolBox](https://github.com/ZiHaoSaMa66/OsEasy-ToolBox) 重构 · [GitHub 仓库](https://github.com/NYSkyfox/OsEasy-ToolKit)

## 许可

MIT License