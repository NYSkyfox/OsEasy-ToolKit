# src/modules/teacher_control.py
# 教师端管控指令模拟模块 —— 在学生机上模拟教师端向学生端发送管控指令
#
# 逆向结论（Os-Easy 多媒体电子教室，MainLogic.dll / StudentLogic.dll）：
#   教师端 → 学生端的管控指令是单播 UDP 包，格式固定：
#
#       报文体 = [16 字节命令头][JSON/文本载荷]
#       命令头（小端）：
#           uint32 cmdType      命令类型号
#           uint32 flag1        0 或 1
#           uint32 flag2        0
#           uint32 payloadLen   载荷字节长度
#
#   学生端监听端口（UdpMessageControllerPort，core.conf 默认值）= 8040
#
#   cmdType 已知值：
#       11    学生呼号/点名（SendCallSignToNewStudent）
#       13/39/40/41  远程命令（RemoteCommand）
#       28    学生参数配置（StuSet）
#       79    考试文件传输结束
#       111   学生信息登记（json: ip/mac/name/stunum/shownum/pcname/autosign）
#       500   网络限制（Limit；a7==0 时触发 sub_10064770 发送）
#
#   学生端收到 type 报文后，在本地翻译成 support-use-device-control /
#   stop-device-control，发到本机 127.0.0.1:8045 给 DeviceControl，再走
#   OeNetLimit.sys（WFP 驱动）执行断网/限速。

import time
import socket
import struct
import ipaddress

from src.utils.logger import info, warn, error, debug

# 学生端接收管控指令的 UDP 端口（UdpMessageControllerPort 默认值）
DEFAULT_PORT = 8040
DEFAULT_TIMEOUT = 1.5

# 已确认的命令类型号
CMD_CALL_SIGN = 11
CMD_REMOTE_CMD = 13
CMD_STU_SET = 28
CMD_EXAM_FILE_END = 79
CMD_STU_INFO = 111
CMD_NET_LIMIT = 500


def build_packet(cmd_type: int, payload: bytes, flag1: int = 0,
                 flag2: int = 0) -> bytes:
    """构造教师端管控指令报文。

    Args:
        cmd_type: 命令类型号。
        payload:  载荷字节（可二进制，通常为 JSON。
        flag1:    flag1 字段（默认 0）。
        flag2:    flag2 字段（默认 0）。

    Returns:
        16 字节命令头 + 载荷 组成的完整报文。
    """
    header = struct.pack("<IIII", int(cmd_type) & 0xFFFFFFFF,
                         int(flag1) & 0xFFFFFFFF,
                         int(flag2) & 0xFFFFFFFF,
                         len(payload))
    return header + payload


def send_control(ip: str, cmd_type: int, payload: bytes,
                 port: int = DEFAULT_PORT, timeout: float = DEFAULT_TIMEOUT,
                 ttl: int = 2) -> str:
    """向目标学生机单播发送一条教师端管控指令。

    Args:
        ip:       目标学生机 IP。
        cmd_type: 命令类型号。
        payload:  载荷字节。
        port:     目标 UDP 端口（默认 8040）。
        timeout:  收发超时。
        ttl:      IP_MULTICAST_TTL（组播时才有意义，单播可忽略）。

    Returns:
        结果描述字符串。
    """
    ip = (ip or "").strip()
    if not ip:
        warn("教师端指令：未提供目标 IP，已跳过")
        return "未提供目标 IP"
    try:
        port = int(port or DEFAULT_PORT)
    except (TypeError, ValueError):
        error(f"教师端指令：端口无效: {port}")
        return f"端口无效: {port}"

    pkt = build_packet(cmd_type, payload)
    t0 = time.perf_counter()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.settimeout(timeout)
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        except OSError:
            pass  # 单播场景非必需
        sock.sendto(pkt, (ip, port))
        el = (time.perf_counter() - t0) * 1000
        info(f"教师端指令 cmdType={cmd_type} 已发送到 {ip}:{port}"
             f"（{len(pkt)} 字节，耗时 {el:.0f}ms）")
        return (f"教师端指令 cmdType={cmd_type} 已发送到 {ip}:{port}"
                f"（{len(pkt)} 字节）")
    except OSError as exc:
        el = (time.perf_counter() - t0) * 1000
        warn(f"发送到 {ip}:{port} 失败: {exc}（耗时 {el:.0f}ms）")
        return f"发送到 {ip}:{port} 失败: {exc}"
    finally:
        try:
            sock.close()
        except Exception:
            pass


def send_multi(ips, cmd_type: int, payload: bytes,
               port: int = DEFAULT_PORT, timeout: float = DEFAULT_TIMEOUT) -> str:
    """对多个 IP 批量发送管控指令。"""
    ips = list(ips)
    ok, fail = 0, 0
    for ip in ips:
        r = send_control(ip, cmd_type, payload, port, timeout)
        if "已发送" in r:
            ok += 1
        else:
            fail += 1
    info(f"批量发送管控指令完成：成功 {ok} 台，失败 {fail} 台")
    return f"批量发送管控指令：成功 {ok} 台，失败 {fail} 台"


def expand_cidr(cidr: str):
    """展开网段字符串为 IP 列表；非合法网段则原样返回。"""
    try:
        net = ipaddress.ip_network(cidr.strip(), strict=False)
        hosts = [str(h) for h in net.hosts()]
        return hosts
    except ValueError:
        return [cidr.strip()]


def net_limit_payload(network_on: bool, internet_on: bool = False) -> bytes:
    """构造网络限制（cmdType=500）的载荷。

    注意：type=500 载荷的确切结构尚未 100% 还原（见 new.md）。
    此处按已还原的字段语义提供一个占位构造，后续逆向完成后替换。
    """
    # 占位：字段语义待最终确认
    body = (f"network={1 if network_on else 0};"
            f"internet={1 if internet_on else 0};")
    return body.encode("utf-8")
