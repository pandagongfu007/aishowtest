"""
程序入口模块

系统初始化和启动逻辑。
"""

import signal
import sys
from typing import Optional

from conn import Connector
from server import app, init_app_context, run_server
from heartbeat import HeartbeatThread
from log import Log
from const import PORT          # ★ 新增这一行


logger = Log()


class Main:
    """主程序类，负责系统初始化和启动"""
    
    def __init__(self):
        """初始化各个服务组件"""
        self.connector: Optional[Connector] = None
        self.heartbeat_thread: Optional[HeartbeatThread] = None
        self.running = False
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理函数，用于优雅关闭"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def initialize(self) -> None:
        """初始化系统组件"""
        logger.info("Initializing edge control module...")
        
        # 创建连接器实例（单例）
        self.connector = Connector()
        
        # 初始化设备发现
        logger.info("Discovering devices...")
        self.connector.find()
        
        # 将Connector注入到Sanic应用上下文
        init_app_context(self.connector)
        
        # 启动心跳线程（T060）
        logger.info("Starting heartbeat thread...")
        self.heartbeat_thread = HeartbeatThread(self.connector)
        self.heartbeat_thread.start()
        
        logger.info("System initialization completed")
    
    def run(self) -> None:
        """启动HTTP服务器"""
        if not self.connector:
            logger.error("System not initialized")
            return
        
        self.running = True
        logger.info("Starting edge control module...")
        
        try:
            # 启动HTTP服务器（阻塞）
            run_server("0.0.0.0", PORT, self.connector) 
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """优雅关闭所有服务"""
        if not self.running:
            return
        
        logger.info("Stopping edge control module...")
        self.running = False
        
        # 停止心跳线程
        if self.heartbeat_thread:
            logger.info("Stopping heartbeat thread...")
            self.heartbeat_thread.stop()
            self.heartbeat_thread.join(timeout=5)
            logger.info("Heartbeat thread stopped")
        
        # 关闭所有仪器连接
        if self.connector:
            with self.connector.lock:
                for sn, inst in self.connector.insts.items():
                    try:
                        inst.close()
                        logger.info(f"Closed connection to instrument {sn}")
                    except Exception as e:
                        logger.error(f"Error closing instrument {sn}: {str(e)}")
        
        logger.info("Edge control module stopped")


def main():
    """主函数入口"""
    main_app = Main()
    main_app.initialize()
    main_app.run()


if __name__ == "__main__":
    main()

