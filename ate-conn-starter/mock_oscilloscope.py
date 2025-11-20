#!/usr/bin/env python3
"""
模拟示波器服务程序

通过TCP Socket接受连接并响应SCPI标准指令。
所有功能整合在单一Python文件中，便于部署和使用。
"""

import socket
import threading
import argparse
import random
import re
import math
from typing import Dict, List, Optional, Tuple


class MockOscilloscopeState:
    """模拟示波器的配置状态"""
    
    def __init__(self):
        """初始化默认配置状态"""
        self.channels: Dict[str, 'ChannelConfig'] = {}
        self.lock = threading.Lock()
        
        # 初始化4个通道
        for i in range(1, 5):
            channel_key = f"CH{i}"
            self.channels[channel_key] = ChannelConfig(channel_num=i)


class ChannelConfig:
    """单个通道的配置信息"""
    
    def __init__(self, channel_num: int):
        """初始化通道配置"""
        self.channel_num: int = channel_num
        self.coupling: str = "DC"


class ErrorQueue:
    """SCPI标准错误队列"""
    
    def __init__(self, max_size: int = 10):
        """初始化错误队列"""
        self.errors: List[Tuple[int, str]] = []
        self.max_size: int = max_size
        self.lock = threading.Lock()
    
    def add_error(self, error_code: int, error_message: str) -> None:
        """添加错误到队列"""
        with self.lock:
            self.errors.append((error_code, error_message))
            if len(self.errors) > self.max_size:
                self.errors.pop(0)
    
    def get_error(self) -> Tuple[int, str]:
        """获取并移除队列中的第一个错误"""
        with self.lock:
            if self.errors:
                return self.errors.pop(0)
            return (0, "No error")
    
    def clear(self) -> None:
        """清空错误队列"""
        with self.lock:
            self.errors.clear()


class MockOscilloscopeServer:
    """模拟示波器TCP服务器"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 10013, 
                 verbose: bool = False):
        """初始化服务器"""
        self.host = host
        self.port = port
        self.verbose = verbose
        self.state = MockOscilloscopeState()
        self.error_queue = ErrorQueue()
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.client_threads: List[threading.Thread] = []
    
    def start(self) -> None:
        """启动服务器"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.running = True
        if self.verbose:
            print(f"Mock oscilloscope server started on {self.host}:{self.port}")
    
    def accept_connections(self) -> None:
        """接受客户端连接"""
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                if self.verbose:
                    print(f"Client connected from {address}")
                handler = ClientHandler(client_socket, address, self.state, 
                                       self.error_queue, self.verbose)
                thread = threading.Thread(target=handler.run, daemon=True)
                thread.start()
                self.client_threads.append(thread)
            except OSError:
                # Socket closed
                break
    
    def stop(self) -> None:
        """停止服务器"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.verbose:
            print("Mock oscilloscope server stopped")


class ClientHandler:
    """客户端连接处理器"""
    
    def __init__(self, client_socket: socket.socket, address: Tuple[str, int],
                 state: MockOscilloscopeState, error_queue: ErrorQueue,
                 verbose: bool = False):
        """初始化客户端处理器"""
        self.client_socket = client_socket
        self.address = address
        self.state = state
        self.error_queue = error_queue
        self.verbose = verbose
    
    def run(self) -> None:
        """处理客户端连接"""
        try:
            while True:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                command = data.decode('utf-8').strip()
                if self.verbose:
                    print(f"Received command from {self.address}: {command}")
                self.process_command(command)
        except Exception as e:
            if self.verbose:
                print(f"Error handling client {self.address}: {e}")
        finally:
            self.client_socket.close()
            if self.verbose:
                print(f"Client {self.address} disconnected")
    
    def parse_command(self, command: str) -> Tuple[str, Optional[str]]:
        """解析SCPI指令"""
        command = command.upper().strip()
        if '?' in command:
            # 查询指令 - 保留?作为标识
            parts = command.split('?', 1)
            cmd = parts[0].strip() + '?'
            # 检查?后面是否有参数（如 MEAS:VOLT:DC? CH1）
            if len(parts) > 1 and parts[1].strip():
                value = parts[1].strip()
                return (cmd, value)
            return (cmd, None)
        else:
            # 设置指令
            if ' ' in command:
                parts = command.split(' ', 1)
                cmd = parts[0].strip()
                value = parts[1].strip()
                return (cmd, value)
            return (command, None)
    
    def process_command(self, command: str) -> None:
        """处理SCPI指令"""
        # 支持命令链（分号分隔）
        commands = command.split(';')
        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue
            cmd_parts, value = self.parse_command(cmd)
            
            # 调试信息
            if self.verbose:
                print(f"DEBUG: Original cmd='{cmd}', cmd_parts='{cmd_parts}', value={value}")
            
            # 路由到相应的处理函数
            # System commands
            if cmd_parts == '*IDN?':
                self.handle_idn()
            # Channel coupling commands
            elif cmd_parts.startswith('CH') and ':COUPLING?' in cmd_parts:
                channel_str = cmd_parts.replace(':COUPLING?', '')
                self.handle_channel_coupling_query(channel_str)
            elif cmd_parts.startswith('CH') and ':COUPLING' in cmd_parts and value:
                channel_str = cmd_parts.replace(':COUPLING', '')
                self.handle_channel_coupling_set(channel_str, value)
            # Measurement commands - CH<num>:MEAS:VOLT:PP?
            elif cmd_parts.startswith('CH') and ':MEAS:VOLT:PP?' in cmd_parts:
                channel_str = cmd_parts.replace(':MEAS:VOLT:PP?', '')
                self.handle_meas_volt_pp(channel_str)
            # Waveform commands - CH<num>:WAV:DATA?
            elif cmd_parts.startswith('CH') and ':WAV:DATA?' in cmd_parts:
                channel_str = cmd_parts.replace(':WAV:DATA?', '')
                self.handle_wav_data(channel_str)
            else:
                if self.verbose:
                    print(f"DEBUG: Command not matched - cmd_parts='{cmd_parts}', startswith_CH={cmd_parts.startswith('CH')}, contains_WAV_DATA={'WAV:DATA?' in cmd_parts}")
                self.handle_invalid_command(cmd)
    
    def handle_idn(self) -> None:
        """处理*IDN?指令"""
        response = "namisoft,VirtuScope,a0001,1.0.0"
        self.send_response(response)
    
    def handle_invalid_command(self, command: str) -> None:
        """处理无效指令"""
        self.error_queue.add_error(-113, "Undefined header")
        response = "-113,\"Undefined header\""
        self.send_response(response)
    
    def validate_channel_number(self, channel_num: int) -> bool:
        """验证通道号"""
        return 1 <= channel_num <= 4
    
    def validate_coupling(self, coupling: str) -> bool:
        """验证耦合方式"""
        return coupling.upper() in ["DC", "AC", "GND"]
    
    def handle_channel_coupling_set(self, channel_str: str, value: str) -> None:
        """处理CH<num>:COUPLING设置指令"""
        match = re.match(r'CH(\d+)', channel_str.upper())
        if not match:
            self.error_queue.add_error(-102, "Syntax error")
            self.send_response("-102,\"Syntax error\"")
            return
        channel_num = int(match.group(1))
        if not self.validate_channel_number(channel_num):
            self.error_queue.add_error(-222, "Data out of range")
            self.send_response("-222,\"Data out of range\"")
            return
        coupling_value = value.upper().strip()
        if not self.validate_coupling(coupling_value):
            self.error_queue.add_error(-224, "Illegal parameter value")
            self.send_response("-224,\"Illegal parameter value\"")
            return
        channel_key = f"CH{channel_num}"
        with self.state.lock:
            if channel_key in self.state.channels:
                self.state.channels[channel_key].coupling = coupling_value
        self.send_response("OK")
    
    def handle_channel_coupling_query(self, channel_str: str) -> None:
        """处理CH<num>:COUPLING?查询指令"""
        match = re.match(r'CH(\d+)', channel_str.upper())
        if not match:
            self.error_queue.add_error(-102, "Syntax error")
            self.send_response("-102,\"Syntax error\"")
            return
        channel_num = int(match.group(1))
        if not self.validate_channel_number(channel_num):
            self.error_queue.add_error(-222, "Data out of range")
            self.send_response("-222,\"Data out of range\"")
            return
        channel_key = f"CH{channel_num}"
        with self.state.lock:
            if channel_key in self.state.channels:
                self.send_response(self.state.channels[channel_key].coupling)
            else:
                self.error_queue.add_error(-100, "Command error")
                self.send_response("-100,\"Command error\"")
    
    def generate_voltage_pp(self, channel_num: int) -> float:
        """生成峰峰值电压测量值"""
        # 生成0到10V范围内的随机值
        return random.uniform(0, 10.0)
    
    def generate_waveform_data(self, channel_num: int) -> str:
        """生成波形数据（100个点）"""
        # 生成100个数据点，使用正弦波
        points = []
        for i in range(100):
            value = 2.0 * math.sin(2 * math.pi * i / 100.0) + random.uniform(-0.1, 0.1)
            points.append(f"{value:.6f}")
        return ",".join(points)
    
    def handle_meas_volt_pp(self, channel_str: str) -> None:
        """处理MEAS:VOLT:PP?查询指令"""
        match = re.match(r'CH(\d+)', channel_str.upper())
        if not match:
            self.error_queue.add_error(-102, "Syntax error")
            self.send_response("-102,\"Syntax error\"")
            return
        channel_num = int(match.group(1))
        if not self.validate_channel_number(channel_num):
            self.error_queue.add_error(-222, "Data out of range")
            self.send_response("-222,\"Data out of range\"")
            return
        voltage = self.generate_voltage_pp(channel_num)
        self.send_response(f"{voltage:.3f}V")
    
    def handle_wav_data(self, channel_str: str) -> None:
        """处理WAV:DATA?查询指令"""
        match = re.match(r'CH(\d+)', channel_str.upper())
        if not match:
            self.error_queue.add_error(-102, "Syntax error")
            self.send_response("-102,\"Syntax error\"")
            return
        channel_num = int(match.group(1))
        if not self.validate_channel_number(channel_num):
            self.error_queue.add_error(-222, "Data out of range")
            self.send_response("-222,\"Data out of range\"")
            return
        waveform = self.generate_waveform_data(channel_num)
        self.send_response(waveform)
    
    def send_response(self, response: str) -> None:
        """发送响应"""
        try:
            self.client_socket.sendall((response + '\n').encode('utf-8'))
        except Exception as e:
            if self.verbose:
                print(f"Error sending response: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Mock Oscilloscope Server')
    parser.add_argument('--host', default='127.0.0.1', help='Listen host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=10013, help='Listen port (default: 10013)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    server = MockOscilloscopeServer(
        host=args.host,
        port=args.port,
        verbose=args.verbose
    )
    
    try:
        server.start()
        server.accept_connections()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.stop()


if __name__ == '__main__':
    main()

