"""
日志管理模块

提供统一的日志输出接口，支持多级别日志记录。
"""

import logging
import sys
from typing import Optional


class Log:
    """
    日志管理类（单例模式）
    
    提供统一的日志输出接口，支持debug、info、warning、error等级别。
    """
    
    _instance: Optional['Log'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls) -> 'Log':
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_logger()
        return cls._instance
    
    def _init_logger(self) -> None:
        """初始化日志配置"""
        self._logger = logging.getLogger('edge_control')
        self._logger.setLevel(logging.DEBUG)
        
        # 避免重复添加handler
        if not self._logger.handlers:
            # 控制台输出handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            
            # 格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            self._logger.addHandler(console_handler)
    
    def debug(self, message: str) -> None:
        """记录调试日志"""
        if self._logger:
            self._logger.debug(message)
    
    def info(self, message: str) -> None:
        """记录信息日志"""
        if self._logger:
            self._logger.info(message)
    
    def warning(self, message: str) -> None:
        """记录警告日志"""
        if self._logger:
            self._logger.warning(message)
    
    def error(self, message: str) -> None:
        """记录错误日志"""
        if self._logger:
            self._logger.error(message)
    
    def get_logs(self) -> list:
        """
        获取日志内容（预留接口）
        
        Returns:
            日志内容列表
        """
        # TODO: 实现日志获取逻辑
        return []

