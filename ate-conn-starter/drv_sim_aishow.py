# drv_sim_aishow.py
"""
aishowtestwindrv 驱动仿真桥接

先用纯 Python 模拟，后面再替换成 ctypes 调用 C++ DLL 即可。
"""

from typing import Tuple, Dict, Any

# 简单在内存里维护一些模拟寄存器
_sim_regs: Dict[str, int] = {
    "discrete_ctrl": 0,     # 离散控制字
    "status_word": 0x0001,  # 状态字示例
}


def write_discrete_ctrl(value: int) -> Tuple[bool, str]:
    """模拟写离散控制字（对应 TEST_CTRL 写命令）"""
    _sim_regs["discrete_ctrl"] = value & 0xFFFF
    # 你可以顺便更新一下 status_word, 比如 bit0=power_ok
    if value & 0x1:
        _sim_regs["status_word"] |= 0x0001  # power_ok = 1
    else:
        _sim_regs["status_word"] &= ~0x0001
    return True, f"discrete_ctrl={_sim_regs['discrete_ctrl']}"


def read_status_word() -> Tuple[bool, str]:
    """模拟读状态字（对应 TEST_STATUS 读命令）"""
    val = _sim_regs["status_word"]
    # 返回一个“设备响应字符串”，让 reply_spec 去解析
    # 比如 ATE 里配置的 reply 正则是提取数字，就简单返回 "1234"
    return True, str(val)


def handle_write(code: str, params: Dict[str, str]) -> Tuple[bool, str]:
    """
    统一入口：写类指令
    code: 指令编码（比如 test_device_ctrl）
    params: {"discrete_ctrl": "123"}
    """
    if code == "test_device_ctrl":
        v = int(params.get("discrete_ctrl", "0"))
        return write_discrete_ctrl(v)

    # 其它写命令在这里继续扩展
    return False, f"unsupported write code: {code}"


def handle_read(code: str, params: Dict[str, str]) -> Tuple[bool, str]:
    """
    统一入口：读类指令
    返回 (success, content_string)
    """
    if code == "test_status":
        return read_status_word()

    # 其它读命令在这里继续扩展
    return False, f"unsupported read code: {code}"

