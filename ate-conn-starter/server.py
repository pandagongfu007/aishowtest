"""
HTTP服务模块

基于Sanic框架提供RESTful API接口，处理设备控制指令请求。
"""

from sanic import Sanic, Request, json
from sanic.exceptions import SanicException
from typing import Dict, Any

from const import PORT, OpType
from log import Log

# 创建Sanic应用实例
app = Sanic("edge_control")

# 日志实例
logger = Log()


def init_app_context(connector: Any) -> None:
    """
    初始化应用上下文，注入Connector实例
    
    Args:
        connector: Connector实例，用于处理设备操作
    """
    app.ctx.connector = connector


@app.exception(SanicException)
async def handle_exception(request: Request, exception: SanicException):
    """统一异常处理"""
    logger.error(f"请求错误: {exception.message}")
    response = {
        'code': exception.status_code,
        'message': exception.message
    }
    logger.info(f"返回内容 - {response}")
    return json(response, status=exception.status_code)


@app.exception(Exception)
async def handle_general_exception(request: Request, exception: Exception):
    """通用异常处理"""
    logger.error(f"服务器内部错误: {str(exception)}")
    response = {
        'code': 500,
        'message': '服务器内部错误'
    }
    logger.info(f"返回内容 - {response}")
    return json(response, status=500)


@app.post("/test/<tid>/inst/<sn>")
async def execute_instruction(request: Request, tid: str, sn: str):
    """
    执行仪器指令端点
    
    Args:
        request: Sanic请求对象
        tid: 测试ID
        sn: 仪器序列号
        
    Returns:
        JSON响应，包含执行结果或错误信息
    """
    try:
        # 获取请求体
        data: Dict[str, Any] = request.json
        
        # 验证请求数据
        if not data:
            response = {
                'code': 400,
                'message': '请求体不能为空'
            }
            logger.warning("请求体为空")
            logger.info(f"返回内容 - {response}")
            return json(response, status=400)
        
        # T081: 输入验证 - 验证必需字段
        required_fields = ['type', 'code', 'template', 'params', 'replys']
        for field in required_fields:
            if field not in data:
                response = {
                    'code': 400,
                    'message': f'缺少必需字段: {field}'
                }
                logger.warning(f"缺少必需字段 - {field}")
                logger.info(f"返回内容 - {response}")
                return json(response, status=400)
        
        # T081: 输入验证 - 验证字段类型和格式
        # 验证 type 字段
        if not isinstance(data['type'], int) or data['type'] not in [OpType.WRITE, OpType.READ]:
            response = {
                'code': 400,
                'message': f'type字段必须是整数{OpType.WRITE}（写操作）或{OpType.READ}（读操作）'
            }
            logger.warning(f"type字段验证失败 - type={data.get('type')}")
            logger.info(f"返回内容 - {response}")
            return json(response, status=400)
        
        # 验证 code 字段
        if not isinstance(data['code'], str) or not data['code'].strip():
            response = {
                'code': 400,
                'message': 'code字段必须是非空字符串'
            }
            logger.warning("code字段验证失败")
            logger.info(f"返回内容 - {response}")
            return json(response, status=400)
        
        # 验证 template 字段
        if not isinstance(data['template'], str) or not data['template'].strip():
            response = {
                'code': 400,
                'message': 'template字段必须是非空字符串'
            }
            logger.warning("template字段验证失败")
            logger.info(f"返回内容 - {response}")
            return json(response, status=400)
        
        # 验证 params 字段
        if not isinstance(data['params'], list):
            response = {
                'code': 400,
                'message': 'params字段必须是数组'
            }
            logger.warning("params字段验证失败")
            logger.info(f"返回内容 - {response}")
            return json(response, status=400)
        
        # 验证 params 数组中的元素格式
        for i, param in enumerate(data['params']):
            if not isinstance(param, dict):
                response = {
                    'code': 400,
                    'message': f'params[{i}]必须是对象'
                }
                logger.warning(f"params[{i}]验证失败 - 不是对象")
                logger.info(f"返回内容 - {response}")
                return json(response, status=400)
            if 'key' not in param or 'value' not in param:
                response = {
                    'code': 400,
                    'message': f'params[{i}]必须包含key和value字段'
                }
                logger.warning(f"params[{i}]验证失败 - 缺少key或value字段")
                logger.info(f"返回内容 - {response}")
                return json(response, status=400)
            if not isinstance(param['key'], str) or not isinstance(param['value'], str):
                response = {
                    'code': 400,
                    'message': f'params[{i}]的key和value必须是字符串'
                }
                logger.warning(f"params[{i}]验证失败 - key或value不是字符串")
                logger.info(f"返回内容 - {response}")
                return json(response, status=400)
        
        # 验证 replys 字段
        if not isinstance(data['replys'], list):
            response = {
                'code': 400,
                'message': 'replys字段必须是数组'
            }
            logger.warning("replys字段验证失败")
            logger.info(f"返回内容 - {response}")
            return json(response, status=400)
        
        # 读操作必须提供replys
        if data['type'] == OpType.READ and len(data['replys']) == 0:
            response = {
                'code': 400,
                'message': '读操作必须提供至少一个replys元素'
            }
            logger.warning("读操作缺少replys元素")
            logger.info(f"返回内容 - {response}")
            return json(response, status=400)
        
        # 获取Connector实例
        connector = getattr(app.ctx, 'connector', None)
        if not connector:
            logger.error("Connector未在应用上下文中初始化")
            response = {
                'code': 500,
                'message': '系统未初始化'
            }
            logger.info(f"返回内容 - {response}")
            return json(response, status=500)
        
        # 记录接收到的指令
        logger.info(f"收到指令请求 - tid={tid}, sn={sn}, type={data.get('type')}")
        logger.info(f"指令内容 - code={data.get('code')}, template={data.get('template')}, params={data.get('params')}, replys={data.get('replys')}")
        
        # 根据操作类型执行相应操作
        op_type = data['type']
        instruction = data['template']
        params = data['params']
        replys = data['replys']
        
        if op_type == OpType.WRITE:  # 写操作
            success, message = connector.write(sn, instruction, params)
            if success:
                response = {
                    'code': 200,
                    'message': 'success'
                }
                logger.info(f"写操作成功 - sn={sn}")
                logger.info(f"返回内容 - {response}")
                return json(response)
            else:
                response = {
                    'code': 400,
                    'message': message
                }
                logger.warning(f"写操作失败 - sn={sn}, message={message}")
                logger.info(f"返回内容 - {response}")
                return json(response, status=400)
        
        elif op_type == OpType.READ:  # 读操作
            if not replys:
                response = {
                    'code': 400,
                    'message': '读操作必须提供replys字段'
                }
                logger.info(f"返回内容 - {response}")
                return json(response, status=400)
            
            datas, code, message = connector.read(sn, instruction, params, replys, data.get('code', ''))
            if code == 200:
                response = {
                    'code': 200,
                    'message': 'success',
                    'datas': datas
                }
                logger.info(f"读操作成功 - sn={sn}, data_count={len(datas)}")
                logger.info(f"返回内容 - {response}")
                return json(response)
            else:
                response = {
                    'code': code,
                    'message': message
                }
                logger.warning(f"读操作失败 - sn={sn}, code={code}, message={message}")
                logger.info(f"返回内容 - {response}")
                return json(response, status=code)
        
        else:
            response = {
                'code': 400,
                'message': f'不支持的操作类型: {op_type}'
            }
            logger.warning(f"不支持的操作类型 - op_type={op_type}")
            logger.info(f"返回内容 - {response}")
            return json(response, status=400)
    
    except Exception as e:
        logger.error(f"执行指令时发生错误: {str(e)}")
        response = {
            'code': 500,
            'message': f'服务器内部错误: {str(e)}'
        }
        logger.info(f"返回内容 - {response}")
        return json(response, status=500)


def run_server(host: str = "0.0.0.0", port: int = PORT) -> None:
    """
    启动HTTP服务器
    
    Args:
        host: 监听地址
        port: 监听端口
    """
    logger.info(f"Starting HTTP server on {host}:{port}")
    app.run(host=host, port=port, debug=False)

