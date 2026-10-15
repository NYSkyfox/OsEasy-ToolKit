# src/patches/dog_license.py
# 教师端「加密狗 / 点数限制」解除 —— 纯 patch 点配置（无执行逻辑）
#
# 执行逻辑在 src/core/dog_patch.DogPatchExecutor。
# 4 个方案是同一个功能域（解除教师端授权限制）的配套路径：
#   方案1 max_connect   [MainLogic.dll] 解除学生机连接数上限（治本·推荐）
#   方案2 fake_dog      [Teacher.exe]   恒判有狗（改对版·双 patch，需配合方案1）
#   方案3 nodog_dialog  [Teacher.exe]   消除"未找到加密狗"启动弹窗（辅助）
#   方案4 config_limit  [skin/core.conf]改 /Limit/ 并重签 /MD5/（辅助验证）
#
# 定位范式：anchor（唯一锚点+双态）/ multi（一文件多锚点）/ va / config（文本重签）。
# 定位均已在服务器真实样本上字节级核实（详见 Patch_Docs/10 ~ 12）。

from src.core.dog_patch import DogSolution

DOG_SOLUTIONS = [
    DogSolution(
        key="max_connect",
        name="解除学生机连接数上限",
        tag="[治本·推荐]",
        target="MainLogic.dll",
        loc_type="anchor",
        anchor=bytes.fromhex("3b91b00000000f8da6000000"),  # cmp max,cur; jge 拒绝
        anchor_off=6,                                       # jge 在锚点内的偏移
        orig=bytes.fromhex("0f8da6000000"),                 # jge +0xa6
        new=bytes.fromhex("909090909090"),                  # 6 x NOP
        md5="022b8f1be58b9c02a0d4f0022d038f0f",
        size=1684480,
        desc="NOP 掉 MainLogic.dll 中『当前连接数 ≥ 授权点数则拒绝』的判定"
             "（NodeManager m_nCurConnectsOnline 判定）。直接命中『无狗最多 5 台』的根因，"
             "学生机可连任意多台，且独立于加密狗逻辑。",
    ),
    DogSolution(
        key="fake_dog",
        name="恒判有狗（改对版·双patch）",
        tag="[Teacher.exe]",
        target="Teacher.exe",
        loc_type="multi",
        md5="7b999b972ea50b540c44800be1e4e465",
        size=3732480,
        desc="【改对版】不再整体替换 FUN_00419280——那是带副作用的授权初始化函数，"
             "整体 mov eax,2;ret 会跳过授权写入→『未激活/无授权教师机点数』进不去主界面。"
             "改为两处精准 patch，保留全部授权副作用：\n"
             "  ① FUN_00419280 内 je→jmp：让『无授权串』也执行授权写入路径(FUN_0041cd90)；\n"
             "  ② FUN_0041cd90 尾部恒返回 6(调用方校验最多的『有效』状态码)。\n"
             "解除『无授权教师机点数 / 未激活』拦截。需配合方案1。",
        patches=[
            # 2a: FUN_00419280 授权分支 je+0x2a -> jmp+0x2a（仅改 1 字节 74->eb，位移不变）
            dict(label="2a: 0x4192e9 je→jmp",
                 anchor=bytes.fromhex("e8ecb101000fb6d085d2742a"),  # call empty; movzbl; test
                 anchor_off=10,                                       # je 在锚点第 10 字节
                 orig=bytes.fromhex("74"),
                 new=bytes.fromhex("eb")),
            # 2b: FUN_0041cd90 尾部 15 字节 -> mov eax,6; jmp 尾声; 8×NOP
            dict(label="2b: 0x41cdab 恒返回6",
                 anchor=bytes.fromhex("0fb6d085d27505e8991c00008b45fc"),
                 anchor_off=0,
                 orig=bytes.fromhex("0fb6d085d27505e8991c00008b45fc"),
                 new=bytes.fromhex("b806000000eb089090909090909090")),
        ],
    ),
    DogSolution(
        key="nodog_dialog",
        name="消除\"未找到加密狗\"启动弹窗",
        tag="[Teacher.exe]",
        target="Teacher.exe",
        loc_type="va",
        imagebase=0x400000,
        va=0x55a900,                                          # FUN_0055a900 狗状态->弹窗分发
        orig=bytes.fromhex("558bec"),
        new=bytes.fromhex("31c0c3"),                          # xor eax,eax; ret
        md5="7b999b972ea50b540c44800be1e4e465",
        size=3732480,
        desc="NOP 掉启动时按狗状态弹窗的分发函数。仅消除弹窗表象，不解除点数限制，"
             "建议配合方案1使用。",
    ),
    DogSolution(
        key="config_limit",
        name="改 core.conf 的 /Limit/ 并重签",
        tag="[配置]",
        target="skin/core.conf",
        loc_type="config",
        desc="把 skin\\core.conf 的 /Limit/ 值改掉，并重新计算 /MD5/ 签名（算法已破解）。"
             "是否解除限制取决于 Limit 的具体语义，作为辅助验证手段。",
    ),
]

_DOG_MAP = {s.key: s for s in DOG_SOLUTIONS}


def get_dog_solution(key: str):
    return _DOG_MAP.get(key)


def dog_solution_keys() -> list:
    return list(_DOG_MAP.keys())


# 供 overview 展示的教师端目标文件（去重，保持出现顺序）
DOG_TARGET_FILES = list(dict.fromkeys(
    [s.target for s in DOG_SOLUTIONS]))