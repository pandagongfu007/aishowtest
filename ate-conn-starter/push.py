# push.py
import json
from typing import Dict, Any
import requests

from const import EDGE_HOST, EDGE_PORT
from log import Log

logger = Log()


class PushService:
    """
    向 Edge 平台推送消息的简单实现
    目前只用于心跳，把行为做得和 PowerShell 测试一致：
    - HTTP POST
    - URL: http://EDGE_HOST:EDGE_PORT/heart
    - JSON body
    - 关闭环境代理（proxies={}）
    """

    def __init__(self) -> None:
        self.url = f"http://{EDGE_HOST}:{EDGE_PORT}/heart"

    def push(self, message: Dict[str, Any]) -> bool:
        try:
            # 为了调试清晰，可以先打印一条日志
            logger.debug(f"Send heartbeat to {self.url}, body={json.dumps(message, ensure_ascii=False)}")

            resp = requests.post(
                self.url,
                json=message,          # 直接传 json，requests 会自动加 Content-Type
                timeout=5,             # 和你 Invoke-WebRequest 的 TimeoutSec 一样
                proxies={}             # 关键：忽略系统 HTTP_PROXY / HTTPS_PROXY，避免走不了内网
            )
            resp.raise_for_status()

            logger.debug(f"Heartbeat HTTP {resp.status_code}: {resp.text}")
            return True
        except Exception as e:
            logger.error(f"Failed to send heartbeat to {self.url}: {e}")
            return False
