# 拦截远程关机 / 重启 —— patch 点逆向文档

## 目标

学生端 `Student.exe`（PE32，i386，ImageBase `0x400000`）。
拦截教师端下发的**远程重启 / 远程关机**指令，使其在学生机失效。

## 逆向结论

远程重启与远程关机**共用同一个函数** `FUN_004a9660`：

```
FUN_004a9660:
    if (param == 0)   ExitWindowsEx(6, 0);   // 0x6 = REBOOT|FORCE
    else              ExitWindowsEx(0xd, 0); // 0xd = SHUTDOWN|FORCE|POWEROFF
```

该函数先 `AdjustTokenPrivileges` 启用 `SeShutdownPrivilege`，再调用 `ExitWindowsEx`。

**关键排除**：
- `StudentLogic.dll` 完全不参与关机 / 重启逻辑。
- `Student.exe` 二进制内**无** `shutdown.exe` 字符串。
- 因此"劫持 / 拦截 shutdown.exe"对远程关机**无效**（红鲱鱼，早期误判）。

真正入口在 `Student.exe` 的 `FUN_004a9660`，重启与关机都走这里——**一个点封两个动作**。

## Patch 点

| 项 | 值 |
|---|---|
| 符号 | `FUN_004a9660` |
| VA | `0x4A9660` |
| RVA | `0x0A9660` |
| 原 3 字节 | `55 8b ec`（`push ebp; mov ebp, esp`，MSVC SEH 序言） |
| 补丁 3 字节 | `31 c0 c3`（`xor eax, eax; ret`，函数进入即返回） |

原理：把函数入口改为立即返回，重启 / 关机指令全部失效，随时可还原。

## 已知合法样本

| MD5 | 说明 |
|---|---|
| `326a77edb4b5d03eaeeb7dafa2d9e08e` | Student.exe 原版 |
| `aa2e24bc4912e8f57a3dd2b3df6cb6e1` | Student_duo_open.exe 双开版（布局相同，RVA 一致） |

## 两种运行方式

- **文件版**：直接改磁盘上的 `Student.exe`（持久；需先结束学生端进程，再启动新文件）。备份 `<文件>.noshutdown.bak`，可还原。
- **内存版**：改运行中 `Student.exe` 进程内存。运行时枚举主模块基址（抗 ASLR），写 `base + RVA`。进程重启后自动恢复，磁盘文件不动。仅 **Windows + 管理员**。

## 落位

`src/modules/noshutdown.py`（PE+VA 定位 + 内存版，与 `duo_open` 同类，独立维护；
不纳入 `src/patches/` 注册表，因后者只收固定文件偏移的纯引擎目标）。
GUI 页面 `src/gui/pages/page_noshutdown.py`。
