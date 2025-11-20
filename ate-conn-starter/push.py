"""
消息推送模块

提供HTTP消息推送功能，用于向Edge平台发送心跳消息。
"""

import httpx
from typing import Dict, Any, Optional
from log import Log
from const import EDGE_HOST, EDGE_PORT

logger = Log()


class PushService:
    """推送服务类（单例模式），负责向Edge平台发送HTTP消息"""
    
    _instance: Optional['PushService'] = None
    _lock = None
    
    def __new__(cls) -> 'PushService':
        """单例模式实现"""
        import threading
        if cls._lock is None:
            cls._lock = threading.Lock()
        
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def push(self, message: Dict[str, Any], endpoint: str = "/heart") -> bool:
        """
        向Edge平台推送消息
        
        Args:
            message: 要推送的消息字典
            endpoint: API端点路径
            
        Returns:
            推送是否成功
        """
        url = f"http://{EDGE_HOST}:{EDGE_PORT}{endpoint}"
        
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(url, json=message)
                response.raise_for_status()
                logger.debug(f"Heartbeat sent successfully to {url}")
                return True
        except httpx.RequestError as e:
            logger.error(f"Failed to send heartbeat to {url}: {str(e)}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"Heartbeat request failed with status {e.response.status_code}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending heartbeat: {str(e)}")
            return False

