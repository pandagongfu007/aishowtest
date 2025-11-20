"""
响应格式定义模块

定义ReplySpec数据类和ReplyType枚举，用于解析仪器指令响应。
"""

import re
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Union


class ReplyType(IntEnum):
    """响应数据类型枚举"""
    NUMERIC = 0          # 数值型数据
    STRING = 1           # 字符串型数据
    WAVEFORM = 2         # 波形数据
    COMMA_SEPARATED = 5  # 逗号分隔的多组数据


@dataclass
class ReplySpec:
    """仪器指令预期响应格式定义"""
    
    key: str                              # 参数代码（必填）
    code: str = ""                        # 编码
    label: str = ""                       # 参数名称
    kind: str = ""                        # 数据类型描述
    type: int = ReplyType.STRING          # 数据类型（使用ReplyType枚举）
    unit: str = ""                        # 单位
    use: int = 0                          # 是否使用
    decimals: float = 0.0                 # 保留小数位数
    scale: float = 1.0                    # 缩放系数
    var: str = ""                         # 全局变量
    regexps: List[str] = field(default_factory=list)  # 正则表达式列表
    position: int = 0                     # 位置
    sim_data: Dict[str, Any] = field(default_factory=dict)  # 模拟数据
    unit_data: List[Any] = field(default_factory=list)      # 单位列表
    
    def parse(self, content: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        根据类型解析响应内容
        
        Args:
            content: 原始响应内容字符串
            
        Returns:
            解析后的数据字典或字典列表
            - NUMERIC/WAVEFORM/STRING: 返回单个字典
            - COMMA_SEPARATED: 返回字典列表
        """
        content = content.strip()
        
        # 根据类型选择解析方法
        if self.type == ReplyType.NUMERIC:
            return self._parse_numeric(content)
        elif self.type == ReplyType.STRING:
            return self._parse_string(content)
        elif self.type == ReplyType.WAVEFORM:
            return self._parse_waveform(content)
        elif self.type == ReplyType.COMMA_SEPARATED:
            return self._parse_comma_separated(content)
        else:
            # 默认按字符串处理
            return self._parse_string(content)
    
    def _parse_numeric(self, content: str) -> Dict[str, Any]:
        """解析数值型数据"""
        # 如果有正则表达式，先提取匹配的值
        if self.regexps:
            for pattern in self.regexps:
                match = re.search(pattern, content)
                if match:
                    content = match.group(0)
                    break
        
        try:
            # 转换为浮点数
            value = float(content)
            # 应用缩放系数
            value = value * self.scale
            # 格式化小数位数
            value_str = f"{value:.{int(self.decimals)}f}"
        except (ValueError, TypeError):
            # 如果无法解析，返回原始值
            value_str = content
        
        return {
            'key': self.key,
            'type': self.type,
            'label': self.label,
            'kind': self.kind,
            'unit': self.unit,
            'value': value_str
        }
    
    def _parse_string(self, content: str) -> Dict[str, Any]:
        """解析字符串型数据"""
        return {
            'key': self.key,
            'type': self.type,
            'label': self.label,
            'kind': self.kind,
            'unit': self.unit,
            'value': content
        }
    
    def _parse_waveform(self, content: str) -> Dict[str, Any]:
        """解析波形数据（不进行缩放处理）"""
        return {
            'key': self.key,
            'type': self.type,
            'label': self.label,
            'kind': self.kind,
            'unit': self.unit,
            'value': content
        }
    
    def _parse_comma_separated(self, content: str) -> List[Dict[str, Any]]:
        """解析逗号分隔的多组数据"""
        parts = [p.strip() for p in content.split(',')]
        results = []
        
        for part in parts:
            try:
                # 尝试解析为数值
                value = float(part)
                # 应用缩放系数
                value = value * self.scale
                # 格式化小数位数
                value_str = f"{value:.{int(self.decimals)}f}"
            except (ValueError, TypeError):
                # 如果无法解析，使用原始值
                value_str = part
            
            results.append({
                'key': self.key,
                'type': ReplyType.NUMERIC,  # 每个元素都是数值型
                'label': self.label,
                'kind': self.kind,
                'unit': self.unit,
                'value': value_str
            })
        
        return results
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReplySpec':
        """
        从字典创建ReplySpec对象
        
        Args:
            data: 包含ReplySpec字段的字典
            
        Returns:
            ReplySpec对象
        """
        # 提取字段，使用默认值填充缺失字段
        return cls(
            key=data.get('key', ''),
            code=data.get('code', ''),
            label=data.get('label', ''),
            kind=data.get('kind', ''),
            type=data.get('type', ReplyType.STRING),
            unit=data.get('unit', ''),
            use=data.get('use', 0),
            decimals=data.get('decimals', 0.0),
            scale=data.get('scale', 1.0),
            var=data.get('var', ''),
            regexps=data.get('regexps', []),
            position=data.get('position', 0),
            sim_data=data.get('sim_data', {}),
            unit_data=data.get('unit_data', [])
        )

