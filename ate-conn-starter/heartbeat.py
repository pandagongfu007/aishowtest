"""
心跳服务模块

定期向Edge平台发送心跳消息，上报服务状态和已连接设备列表。
"""

import threading
import time
import socket
from typing import Optional, Dict, Any, List
from log import Log
from const import (
    HEARTBEAT_INTERVAL,
    SERVICE_NAME,
    SERVICE_VERSION,
    SERVICE_KIND,
    PORT,
    EDGE_HOST,
    EDGE_PORT
)
from conn import Connector
from push import PushService

logger = Log()


class HeartbeatThread(threading.Thread):
    """心跳线程类，定期发送心跳消息"""
    
    def __init__(self, connector: Optional[Connector] = None):
        """
        初始化心跳线程
        
        Args:
            connector: Connector实例，用于获取设备列表
        """
        super().__init__(daemon=True, name="HeartbeatThread")
        self.connector = connector or Connector()
        self.push_service = PushService()
        self.running = False
        self._stop_event = threading.Event()
    
    def run(self) -> None:
        """心跳主循环"""
        self.running = True
        logger.info("Heartbeat thread started")
        
        while self.running and not self._stop_event.is_set():
            try:
                # 组装心跳消息
                heartbeat_message = self._assemble_heartbeat_message()
                
                # 发送心跳
                success = self.push_service.push(heartbeat_message)
                
                if success:
                    logger.debug("Heartbeat sent successfully")
                else:
                    logger.warning("Failed to send heartbeat, will retry in next interval")
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {str(e)}")
            
            # 等待下一个心跳间隔
            self._stop_event.wait(HEARTBEAT_INTERVAL)
        
        logger.info("Heartbeat thread stopped")
    
    def _assemble_heartbeat_message(self) -> Dict[str, Any]:
        """
        组装心跳消息
        
        Returns:
            心跳消息字典
        """
        # 获取设备列表
        insts_list = self._collect_device_list()
        
        # 获取本机IP地址
        host = self._get_local_ip()
        
        # 组装消息
        message = {
            "svc": SERVICE_NAME,
            "ver": SERVICE_VERSION,
            "hb": HEARTBEAT_INTERVAL,
            "kind": SERVICE_KIND,
            "host": host,
            "port": PORT,
            "insts": insts_list,
            "ress": [],
            "psrs": []
        }
        
        return message
    
    def _collect_device_list(self) -> List[Dict[str, str]]:
        """
        从Connector收集设备列表
        
        Returns:
            设备信息列表
        """
        insts_list = []
        
        if self.connector:
            with self.connector.lock:
                for sn, inst in self.connector.insts.items():
                    if inst.is_online:
                        insts_list.append({
                            "sn": sn,
                            "host": inst.host,
                            "port": inst.port,
                            "model": inst.model,
                            "mfr": inst.mfr,
                            "res": f"{inst.host}::{inst.port}",
                            "status": 1,
                            "cfg": {}
                        })
        
        return insts_list
    
    def _get_local_ip(self) -> str:
        """
        获取本机IP地址
        
        Returns:
            IP地址字符串
        """
        try:
            # 连接到外部地址以获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((EDGE_HOST, EDGE_PORT))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            # 如果获取失败，返回默认值
            return "127.0.0.1"
    
    def stop(self) -> None:
        """停止心跳线程"""
        self.running = False
        self._stop_event.set()
        logger.info("Heartbeat thread stop requested")

