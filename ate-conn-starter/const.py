"""
常量定义模块

定义系统配置常量、服务信息、超时时间等。
"""

from enum import IntEnum


class OpType(IntEnum):
    """操作类型枚举"""
    WRITE = 2  # 写操作
    READ = 3   # 读操作

# HTTP服务配置
PORT = 27081

# 心跳配置
HEARTBEAT_INTERVAL = 15  # 心跳间隔（秒）

# 启动配置
VERIFY_TIME = 10  # 验证时间间隔（秒）

# 服务信息
SERVICE_NAME = "ate-conn-ns"
SERVICE_VERSION = "6.0.1"
SERVICE_KIND = "conn"

# Edge平台配置
EDGE_HOST = "127.0.0.1"
EDGE_PORT = 5000

# 超时配置
CONNECTION_TIMEOUT = 10  # 设备连接超时（秒）
INSTRUCTION_TIMEOUT = 10  # 指令执行超时（秒）

