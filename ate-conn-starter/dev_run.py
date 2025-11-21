# -*- coding: utf-8 -*-
"""
开发调试用启动脚本：直接启动 Sanic + Connector
绕过 main.py 和 Heartbeat，只为联调 ATE 指令。
"""

from conn import Connector
from server import app, init_app_context
from log import Log

logger = Log()

if __name__ == "__main__":
    # 1) 初始化连接器，发现设备
    connector = Connector()
    connector.find()

    # 2) 把 connector 注入到 Sanic app.ctx 中
    host = "0.0.0.0"
    port = 27081
    logger.info(f"[DEV] Starting HTTP server on {host}:{port} (dev_run)")
    # 单进程模式，避免 multiprocessing.set_start_method 冲突
    app.run(
        host=host,
        port=port,
        debug=False,
        auto_reload=False,
        single_process=True,  # 关键参数
    )

