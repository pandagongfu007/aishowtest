"""
连接器核心模块

管理所有仪器连接，提供设备资源池和指令处理功能。
"""

import threading
from typing import Dict, List, Optional, Tuple, Any

from inst import Instrument
from reply_spec import ReplySpec, ReplyType
from log import Log

logger = Log()


class Connector:
    """连接器类（单例模式），管理所有仪器连接"""
    
    _instance: Optional['Connector'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'Connector':
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.insts: Dict[str, Instrument] = {}
                    cls._instance.lock = threading.Lock()
        return cls._instance
    
    def find(self) -> None:
        """
        发现和检测仪器，更新资源池
        
        硬编码的仪器列表，并发检测每个仪器连接状态。
        """
        # 硬编码的仪器配置列表
        # TODO: 在实际使用中，这里应该从配置文件或数据库读取
        instrument_configs = [
            # 示例配置，实际使用时需要替换为真实设备信息
            {'sn': 'a0001', 'model': 'VirtuScope', 'mfr': 'namisoft', 'host': '127.0.0.1', 'port': 10013},
            {'sn': 'a0002', 'model': 'VirtuScope', 'mfr': 'namisoft', 'host': '127.0.0.1', 'port': 10014},
        ]
        
        # 并发检测每个仪器
        threads = []
        for config in instrument_configs:
            thread = threading.Thread(
                target=self._check_and_add_instrument,
                args=(config['sn'], config['host'], config['port'], 
                      config.get('model', ''), config.get('mfr', ''))
            )
            thread.start()
            threads.append(thread)
        
        # 等待所有检测完成
        for thread in threads:
            thread.join()
        
        logger.info(f"Device discovery completed. Found {len(self.insts)} online instruments.")
    
    def _check_and_add_instrument(self, sn: str, host: str, port: int, model: str = "", mfr: str = "") -> None:
        """检查并添加仪器到资源池 (T082: 重复SN检测)"""
        try:
            with self.lock:
                # T082: 检测重复SN（在创建Instrument之前检查，避免资源浪费）
                if sn in self.insts:
                    existing_inst = self.insts[sn]
                    # 检查是否是不同的设备（不同的host或port）
                    if existing_inst.host != host or existing_inst.port != port:
                        logger.warning(f"Duplicate SN detected: {sn} already exists with different host/port. "
                                     f"Existing: {existing_inst.host}:{existing_inst.port}, "
                                     f"New: {host}:{port}. Skipping new device.")
                        return
                    # 如果是相同设备，检查是否需要重连
                    if not existing_inst.is_online:
                        logger.info(f"Instrument {sn} was offline, attempting reconnection...")
                        # T080: 尝试重连（通过创建新的Instrument实例）
                        try:
                            new_inst = Instrument(sn, host, port, model, mfr)
                            if new_inst.is_online:
                                # 关闭旧连接
                                try:
                                    existing_inst.close()
                                except Exception:
                                    pass
                                self.insts[sn] = new_inst
                                logger.info(f"Instrument {sn} reconnected successfully")
                            else:
                                logger.warning(f"Instrument {sn} reconnection failed, still offline")
                        except Exception as e:
                            logger.warning(f"Failed to reconnect instrument {sn}: {str(e)}")
                    else:
                        logger.debug(f"Instrument {sn} already online, skipping")
                    return
            
            # 新设备，创建连接
            inst = Instrument(sn, host, port, model, mfr)
            if inst.is_online:
                with self.lock:
                    # 再次检查（防止并发添加）
                    if sn in self.insts:
                        # 如果已存在，关闭新创建的连接，使用已存在的
                        try:
                            inst.close()
                        except Exception:
                            pass
                        logger.debug(f"Instrument {sn} already added by another thread")
                    else:
                        self.insts[sn] = inst
                        logger.info(f"Instrument {sn} added to resource pool")
            else:
                logger.warning(f"Instrument {sn} is offline, not added to resource pool")
        except Exception as e:
            logger.warning(f"Failed to add instrument {sn}: {str(e)}")
    
    def check_instrument(self, sn: str, host: str, port: int) -> bool:
        """
        检测指定仪器连接状态
        
        Args:
            sn: 仪器序列号
            host: 仪器IP地址
            port: 仪器端口
            
        Returns:
            连接是否成功
        """
        try:
            inst = Instrument(sn, host, port)
            return inst.is_online
        except Exception:
            return False
    
    def get_inst(self, sn: str) -> Optional[Instrument]:
        """
        获取指定序列号的仪器对象
        
        Args:
            sn: 仪器序列号
            
        Returns:
            Instrument对象，如果不存在返回None
        """
        with self.lock:
            inst = self.insts.get(sn)
            # 如果设备存在但已离线，检查是否需要移除
            if inst and not inst.is_online:
                # 检查设备离线状态（T039: 设备离线检测机制）
                # 这里可以添加更复杂的离线检测逻辑
                # 当前实现中，is_online 状态由 Instrument 自己维护
                pass
            return inst
    
    def remove_offline_instruments(self) -> None:
        """
        移除离线设备（T040: 自动移除离线设备）
        
        检查资源池中的所有设备，移除离线设备。
        """
        with self.lock:
            offline_sns = []
            for sn, inst in self.insts.items():
                if not inst.is_online:
                    offline_sns.append(sn)
            
            for sn in offline_sns:
                inst = self.insts.pop(sn, None)
                if inst:
                    try:
                        inst.close()
                        logger.info(f"Removed offline instrument {sn} from resource pool")
                    except Exception as e:
                        logger.warning(f"Error closing offline instrument {sn}: {str(e)}")
    
    def write(self, sn: str, instruction: str, params: List[Dict[str, str]]) -> Tuple[bool, str]:
        """
        执行写操作 (T071: 支持参数替换)
        
        Args:
            sn: 仪器序列号
            instruction: 指令模板（可能包含参数占位符）
            params: 参数列表
            
        Returns:
            (success, message) 元组
        """
        # 获取仪器对象
        inst = self.get_inst(sn)
        if not inst:
            return False, f"仪器不存在: {sn}"
        
        if not inst.is_online:
            # T039: 检测到设备离线，更新状态
            logger.warning(f"Instrument {sn} is offline during write operation")
            # T040: 可以选择自动移除离线设备（可选，根据需求决定）
            # self.remove_offline_instruments()
            return False, f"仪器掉线，检查线缆是否插好,网络是否通畅针对当前sn:{sn}的仪器"
        
        # T067: 参数替换
        processed_instruction = self._replace_params(instruction, params)
        
        # 执行写入操作
        result = inst.write(processed_instruction)
        
        # T039: 如果写入失败且设备离线，更新状态
        if not result[0]:
            if not inst.is_online:
                logger.warning(f"Instrument {sn} went offline after write operation")
        
        return result
    
    def read(self, sn: str, instruction: str, params: List[Dict[str, str]], 
             replys: List[Any], code: str) -> Tuple[List[Dict], int, str]:
        """
        执行读操作 (T072: 支持参数替换)
        
        Args:
            sn: 仪器序列号
            instruction: 指令模板（可能包含参数占位符）
            params: 参数列表
            replys: 响应定义列表（可以是字典或ReplySpec对象）
            code: 指令代码
            
        Returns:
            (datas, code, message) 元组
        """
        # 获取仪器对象
        inst = self.get_inst(sn)
        if not inst:
            return [], 404, f"仪器不存在: {sn}"
        
        if not inst.is_online:
            # T039: 检测到设备离线，更新状态
            logger.warning(f"Instrument {sn} is offline during read operation")
            return [], 400, f"仪器掉线，检查线缆是否插好,网络是否通畅针对当前sn:{sn}的仪器"
        
        try:
            # T067: 参数替换
            processed_instruction = self._replace_params(instruction, params)
            logger.debug(f"Processed instruction for {sn}: '{processed_instruction}'")
            
            # 执行读取操作
            content = inst.read(processed_instruction)
            
            # 转换replys为ReplySpec对象列表
            reply_specs = []
            for reply in replys:
                if isinstance(reply, dict):
                    reply_specs.append(ReplySpec.from_dict(reply))
                elif isinstance(reply, ReplySpec):
                    reply_specs.append(reply)
                else:
                    logger.warning(f"Invalid reply format: {type(reply)}")
                    continue
            
            # 解析响应数据
            datas = self.parse_data(content, reply_specs)
            
            return datas, 200, "success"
        
        except TimeoutError as e:
            # T039: 读取超时，检查设备状态
            if inst and not inst.is_online:
                logger.warning(f"Instrument {sn} went offline after timeout")
            return [], 400, str(e)
        except ConnectionError as e:
            # T039: 连接错误，设备可能离线
            if inst:
                inst.is_online = False
                logger.warning(f"Instrument {sn} connection error: {str(e)}")
            return [], 400, str(e)
        except Exception as e:
            logger.error(f"Read operation failed: {str(e)}")
            # T039: 其他异常，检查设备状态
            if inst and not inst.is_online:
                logger.warning(f"Instrument {sn} went offline after read error")
            return [], 500, f"读取操作失败: {str(e)}"
    
    def parse_data(self, content: str, replys: List[ReplySpec]) -> List[Dict[str, Any]]:
        """
        解析响应数据
        
        Args:
            content: 原始响应内容
            replys: ReplySpec对象列表
            
        Returns:
            解析后的数据字典列表
        """
        datas = []
        
        for reply in replys:
            try:
                result = reply.parse(content)
                
                # 如果结果是列表（COMMA_SEPARATED类型），展开
                if isinstance(result, list):
                    datas.extend(result)
                else:
                    datas.append(result)
            
            except Exception as e:
                logger.error(f"Failed to parse reply {reply.key}: {str(e)}")
                # 添加错误数据项
                datas.append({
                    'key': reply.key,
                    'type': reply.type,
                    'label': reply.label,
                    'kind': reply.kind,
                    'unit': reply.unit,
                    'value': content  # 使用原始内容
                })
        
        return datas
    
    def _replace_params(self, template: str, params: List[Dict[str, str]]) -> str:
        """
        替换指令模板中的参数占位符 (T067)
        
        Args:
            template: 指令模板，包含{{key}}占位符
            params: 参数列表，每个元素包含key和value
            
        Returns:
            替换后的指令字符串
        """
        result = template
        param_dict = {p['key']: p['value'] for p in params}
        
        # 替换所有{{key}}占位符
        import re
        pattern = r'\{\{(\w+)\}\}'
        
        def replace_func(match):
            key = match.group(1)
            if key in param_dict:
                return param_dict[key]
            else:
                # 如果参数不存在，保留占位符并记录警告
                logger.warning(f"Parameter {key} not found in params list")
                return match.group(0)  # 保留原始占位符
        
        result = re.sub(pattern, replace_func, result)
        
        return result

