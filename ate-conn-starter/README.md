# ate-conn-starter

## 项目介绍

本项目是ATECLOUD连接器的示例项目

### 核心特性

- **统一通信接口**：通过TCP Socket实现网络通信
- **自动发现**：自动发现和识别连接的仪器设备
- **统一指令处理**：支持参数化指令模板，支持写操作和读操作
- **实时状态同步**：通过心跳机制保持状态一致
- **高并发支持**：基于Sanic异步框架，支持高并发请求处理

## 软件架构

系统采用分层架构设计：

```
┌─────────────────────────────────────────────┐
│            应用层 (Application)             │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  │
│  │ main.py │  │server.py │  │heartbeat │  │
│  └─────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│            业务层 (Business)                │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  │
│  │ conn.py │  │ inst.py  │  │push.py   │  │
│  └─────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│            基础层 (Foundation)              │
│  ┌─────────┐  ┌──────────┐  │
│  │ log.py   │  │const.py  │  │
│  └─────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│            驱动层 (Driver)                  │
│  ┌─────────┐                                │
│  │ Socket  │                                │
│  └─────────┘                                │
└─────────────────────────────────────────────┘
```

### 技术栈

- **Web框架**：Sanic 25.3.0+（高性能异步Web框架）
- **仪器通信**：TCP Socket（Python标准库）
- **HTTP客户端**：httpx（用于Edge平台通信）
- **Python版本**：Python 3.7+

## 环境要求


### Python环境

- Python 3.7 或更高版本
- pip 包管理器

## 安装教程

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖包括：
- `Sanic>=25.3.0` - Web框架
- `websockets>=9.1,<11.0` - WebSocket支持
- `httpx>=0.24.0` - HTTP客户端

### 2. 配置检查

检查 `const.py` 中的关键配置：

```python
# HTTP服务端口（默认：27081）
PORT = 27081

# Edge平台地址（默认：127.0.0.1:5000）
EDGE_HOST = "127.0.0.1"
EDGE_PORT = 5000

# 超时配置
CONNECTION_TIMEOUT = 10  # 设备连接超时（秒）
INSTRUCTION_TIMEOUT = 10  # 指令执行超时（秒）
```

### 3. 配置仪器列表

编辑 `conn.py` 中的 `find()` 方法，配置仪器信息：

```python
instrument_configs = [
    {'sn': 'a0001', 'model': 'VirtuScope', 'mfr': 'namisoft', 'host': '127.0.0.1', 'port': 10013},
    {'sn': 'a0002', 'model': 'VirtuScope', 'mfr': 'namisoft', 'host': '127.0.0.1', 'port': 10014},
]
```

## 启动程序

### 启动主服务

运行主程序启动HTTP服务器：

```bash
python main.py
```


启动成功后，服务将：
1. 自动发现并连接配置的仪器设备
2. 启动HTTP服务器监听在 `0.0.0.0:27081`（默认端口）
3. 启动心跳线程，定期向Edge平台推送状态

### 停止服务

使用 `Ctrl+C` 优雅停止服务，系统会自动：
- 停止心跳线程
- 关闭所有仪器连接
- 清理资源

## 运行模拟器

项目提供了模拟示波器服务程序（`mock_oscilloscope.py`），用于测试和开发。

### 启动模拟器

基本用法：

```bash
python mock_oscilloscope.py
```

默认配置：
- 监听地址：`127.0.0.1`
- 监听端口：`10013`

### 自定义配置

```bash
# 指定监听地址和端口
python mock_oscilloscope.py --host 0.0.0.0 --port 10013

# 启用详细日志
python mock_oscilloscope.py --verbose

# 完整示例
python mock_oscilloscope.py --host 127.0.0.1 --port 10013 --verbose
```

### 模拟器支持的指令

模拟器支持以下SCPI标准指令：

- `*IDN?` - 查询设备标识
- `CH<num>:COUPLING <value>` - 设置通道耦合方式（DC/AC/GND）
- `CH<num>:COUPLING?` - 查询通道耦合方式
- `CH<num>:MEAS:VOLT:PP?` - 查询峰峰值电压
- `CH<num>:WAV:DATA?` - 查询波形数据



### 运行多个模拟器实例

可以启动多个模拟器实例模拟多台设备：

```bash
# 终端1：启动第一个模拟器（端口10013）
python mock_oscilloscope.py --port 10013

# 终端2：启动第二个模拟器（端口10014）
python mock_oscilloscope.py --port 10014
```

然后在 `conn.py` 中配置多个仪器：

```python
instrument_configs = [
    {'sn': 'a0001', 'host': '127.0.0.1', 'port': 10013},
    {'sn': 'a0002', 'host': '127.0.0.1', 'port': 10014},
]
```

## 使用说明

### API接口

系统提供RESTful API接口，用于执行仪器指令。

#### 接口地址

```
POST /test/<tid>/inst/<sn>
```

- `tid`: 测试ID
- `sn`: 仪器序列号

#### 请求格式

**写操作（type=2）**：

```json
{
  "type": 2,
  "code": "SET_COUPLING",
  "template": "CH{{channel}}:COUPLING {{coupling}}",
  "params": [
    {"key": "channel", "value": "1"},
    {"key": "coupling", "value": "DC"}
  ],
  "replys": []
}
```

**读操作（type=3）**：

```json
{
  "type": 3,
  "code": "QUERY_VOLTAGE",
  "template": "CH{{channel}}:MEAS:VOLT:PP?",
  "params": [
    {"key": "channel", "value": "1"}
  ],
  "replys": [
    {
      "key": "voltage",
      "type": "FLOAT",
      "label": "峰峰值电压",
      "kind": "VALUE",
      "unit": "V"
    }
  ]
}
```

#### 响应格式

**写操作成功**：

```json
{
  "code": 200,
  "message": "success"
}
```

**读操作成功**：

```json
{
  "code": 200,
  "message": "success",
  "datas": [
    {
      "key": "voltage",
      "type": "FLOAT",
      "label": "峰峰值电压",
      "kind": "VALUE",
      "unit": "V",
      "value": "5.234"
    }
  ]
}
```

**错误响应**：

```json
{
  "code": 400,
  "message": "错误信息"
}
```
