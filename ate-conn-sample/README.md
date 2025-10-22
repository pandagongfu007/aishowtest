# atecloud-conn-sample

#### 介绍
本项目为连接器示例，基于Python实现的仪器连接器服务

#### 软件架构
* 服务注册
  服务注册采用心跳方式，有心跳线程定期给调度中心发送本服务信息，信息内容包括：       
  服务名、服务地址、服务端口、连接的仪器

```bash
# post
{
  "service" : "ate-conn-xx",
  "version" : "1.0.1",
  "heartbeat": 10,
  "kind" : "conn",
  "host" : "127.0.0.1",
  "port" : 27101,
  "instruments": [
    {
      "manufacturer": "namisoft",
      "model": "namisoft", 
      "sn": "n1234"
    }
  ]
}
```

* 接收并执行仪器指令
  通过http服务接收工步引擎发送的执行指令，执行完指令后把结果返回给调用方


#### 项目结构

```
ate-conn-sample/
├── main.py          # 主程序入口
├── server.py        # HTTP服务实现
├── conn.py          # 连接器管理器
├── heartbeat.py     # 心跳线程
├── push.py          # 数据推送服务
└── README.md        # 项目说明
```

#### 技术栈
- Python 3.x
- Sanic Web框架
- HTTPX异步HTTP客户端
- 多线程处理

#### API接口

1. 下发测试指令

   ```
   POST /test/{tid}/inst/{sn}
   ```

   参数说明：
   - `tid`: 测试任务ID
   - `sn`: 仪器序列号

   请求体示例：

   ```json
   {
     "template": "MEASUrement:MEASCH1:VALue?",
     "params": [
       {
         "key": "channel",
         "value": "CH1"
       }
     ],
     "type": 1,
     "replys": [
       {
         "kind": "电压",
         "key": "volt", 
         "use": 1.0,
         "label": "输入电压",
         "unit": "mV",
         "decimals": 1.0,
         "type": 0.0,
         "scale": 100.0,
         "regexps": ["[/]\\S+", "\\d+"]
       }
     ]
   }
   ```

   字段说明

   | 字段     | 说明                             |
   | -------- | -------------------------------- |
   | template | 下发指令模板                     |
   | params   | 下发指令中需要用到的参数         |
   | type     | 指令类型 1：读取指令 2：配置指令 |
   | replys   | 指令返回值配置                   |

   返回值字段说明

   | 字段     | 说明                                               |
   | -------- | -------------------------------------------------- |
   | key      | 返回值的代码                                       |
   | label    | 标签                                               |
   | kind     | 数据分类 如：电流/电压/长度                        |
   | type     | 数据类型 0:数值1:数组                              |
   | unit     | 单位 如：A/mA/V/mV/m/cm                            |
   | decimals | 保留精度                                           |
   | scale    | 比例因子                                           |
   | regexps  | 用于从仪器返回信息中解析出此数据的一系列正则表达式 |

   **配置指令返回内容（type=2）：**
   ```json
   {
     "code": 200,
     "message": "success"
   }
   ```

   **读取指令返回内容（type=1）：**
   ```json
   {
     "code": 200,
     "message": "success",
     "datas": [
       {
         "key": "volt",
         "label": "输入电压",
         "kind": "电压",
         "unit": "mV",
         "value": 4.5
       }
     ]
   }
   ```

#### 心跳消息

连接器定时向EDGE发送心跳消息，上报连接设备情况，格式如下：

```json
{
  "service": "ate-conn-xx",
  "version": "1.0.1", 
  "heartbeat": 10,
  "kind": "conn",
  "host": "127.0.0.1",
  "port": 27101,
  "instruments": [
    {
      "manufacturer": "namisoft",
      "model": "namisoft",
      "sn": "n1234"
    }
  ]
}
```

| 字段        | 说明                                  |
| ----------- | ------------------------------------- |
| service     | 服务名称，必须与平台中配置的名称一致  |
| version     | 版本                                  |
| heartbeat   | 发送心跳消息的时间周期，单位：秒      |
| kind        | 类型  conn: 连接器服务 oper: 算子服务 |
| host        | 服务地址                              |
| port        | 服务端口（默认27101）                 |
| instruments | 所有可识别的链接设备                  |

仪器上报信息字段说明：

| 字段         | 说明       |
| ------------ | ---------- |
| sn           | 仪器序列号 |
| model        | 仪器型号   |
| manufacturer | 生产厂家   |

#### 运行方式

1. **开发环境运行**
   ```bash
   python main.py
   ```

2. **服务配置**
   - HTTP服务端口：27101
   - 心跳间隔：10秒
   - 推送服务地址：127.0.0.1:5000

#### 依赖安装

```bash
pip install sanic httpx
```

#### 核心组件说明

- **main.py**: 程序入口，启动HTTP服务和心跳线程
- **server.py**: 基于Sanic框架的HTTP服务，处理测试指令
- **conn.py**: 连接器管理器，负责仪器连接和指令收发（单例模式）
- **heartbeat.py**: 心跳线程，定期向平台上报服务状态（单例模式）
- **push.py**: 数据推送服务，处理HTTP异步请求
