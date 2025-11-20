"""
仪器管理模块

封装单个仪器的Socket通信，提供线程安全的读写操作接口。
"""

import socket
import time
from multiprocessing import Lock
from typing import Tuple, Optional

from const import CONNECTION_TIMEOUT, INSTRUCTION_TIMEOUT
from log import Log

logger = Log()


class Instrument:
    """仪器对象，封装单个仪器的所有操作和状态"""
    
    def __init__(self, sn: str, host: str, port: int, model: str = "", mfr: str = "") -> None:
        """
        初始化仪器对象，建立Socket连接
        
        Args:
            sn: 仪器序列号
            host: 仪器IP地址
            port: 仪器端口
            model: 仪器型号
            mfr: 制造商
        """
        self.sn = sn
        self.host = host
        self.port = port
        self.model = model
        self.mfr = mfr
        self.socket: Optional[socket.socket] = None
        self.lock = Lock()
        self.active = time.time()
        self.is_online = False
        self.first = True
        self.err_num = 0
        
        # 建立连接
        self._connect()
    
    def _connect(self) -> None:
        """建立Socket连接"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(CONNECTION_TIMEOUT)
            self.socket.connect((self.host, self.port))
            self.is_online = True
            self.first = False
            self.err_num = 0
            logger.info(f"Instrument {self.sn} connected to {self.host}:{self.port}")
        except Exception as e:
            self.is_online = False
            self.err_num += 1
            logger.error(f"Failed to connect instrument {self.sn}: {str(e)}")
            if self.socket:
                try:
                    self.socket.close()
                except Exception:
                    pass
                self.socket = None
    
    def write(self, instruction: str) -> Tuple[bool, str]:
        """
        写入指令到仪器
        
        Args:
            instruction: 指令字符串
            
        Returns:
            (success, message) 元组
        """
        if not self.is_online or not self.socket:
            return False, f"仪器掉线，检查线缆是否插好,网络是否通畅针对当前sn:{self.sn}的仪器"
        
        with self.lock:
            try:
                # 设置超时
                self.socket.settimeout(INSTRUCTION_TIMEOUT)
                
                # 发送指令（添加换行符）
                instruction_bytes = (instruction + '\n').encode('utf-8')
                self.socket.sendall(instruction_bytes)
                
                # 更新活跃时间
                self.active = time.time()
                
                # 只写入，不读取响应
                return True, "success"
            
            except socket.timeout:
                self.err_num += 1
                error_msg = f"指令执行超时: {instruction}"
                logger.error(f"Instrument {self.sn} {error_msg}")
                return False, error_msg
            
            except Exception as e:
                self.err_num += 1
                self.is_online = False
                error_msg = f"写入指令失败: {str(e)}"
                logger.error(f"Instrument {self.sn} {error_msg}")
                return False, error_msg
    
    def read(self, instruction: str) -> str:
        """
        从仪器读取响应
        
        Args:
            instruction: 查询指令字符串
            
        Returns:
            响应内容字符串
        """
        if not self.is_online or not self.socket:
            raise ConnectionError(f"仪器掉线，检查线缆是否插好,网络是否通畅针对当前sn:{self.sn}的仪器")
        
        with self.lock:
            try:
                # 设置超时
                self.socket.settimeout(INSTRUCTION_TIMEOUT)
                
                # 发送查询指令
                instruction_bytes = (instruction + '\n').encode('utf-8')
                logger.debug(f"Instrument {self.sn} sending instruction: '{instruction}' (bytes: {instruction_bytes})")
                self.socket.sendall(instruction_bytes)
                
                # 读取响应
                response = self.socket.recv(4096).decode('utf-8').strip()
                
                # 更新活跃时间
                self.active = time.time()
                
                logger.debug(f"Instrument {self.sn} read response: {response}")
                return response
            
            except socket.timeout:
                self.err_num += 1
                raise TimeoutError(f"读取指令超时: {instruction}")
            
            except Exception as e:
                self.err_num += 1
                self.is_online = False
                raise ConnectionError(f"读取指令失败: {str(e)}")
    
    def close(self) -> None:
        """关闭Socket连接"""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
            self.is_online = False
            logger.info(f"Instrument {self.sn} connection closed")

