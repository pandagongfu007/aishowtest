#!/bin/env python
# coding=utf-8

########################################################################################################################
# 连接器主程序
# auth: zhangxuanchao(53536364@qq.com)
# date: 2021-5-12
# 启动http服务，用于接收工步引擎调度指令
# 启动心跳线程
########################################################################################################################

import server
from heartbeat import HeartbeatThread
from push import PushService
import logging


# 配置日志
logging.basicConfig(level=logging.DEBUG)

# 启动心跳线程，定期上报服务信息
pushService = PushService("127.0.0.1", 5000)
HeartbeatThread().init(pushService).start()

# 启动http服务，准备接收工步引擎调度指令
server.app.run(host='0.0.0.0', port=27101, debug=False, workers=1)
