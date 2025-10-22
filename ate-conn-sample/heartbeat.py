#!/bin/env python
# coding=utf-8

########################################################################################################################
# 心跳线程
# auth: zhangxuanchao(53536364@qq.com)
# date: 2021-5-12
# 定期把服务信息上报给edge，实现服务注册功能
########################################################################################################################
import threading
import time
import logging
from push import PushService
from conn import Connector


class HeartbeatThread(threading.Thread):

  # 单例模式
  def __new__(cls, *args, **kwargs):
    if not hasattr(cls, '_instance'):
      cls._instance = super(HeartbeatThread, cls).__new__(cls)
    return cls._instance
  
  # 初始化
  def __init__(self):
    # 避免重复初始化
    if hasattr(self, 'status'):
      return
    # 初始化线程
    threading.Thread.__init__(self)
    logging.debug("heart beat create")

  # 实际初始化 启动心跳线程前必须调用
  def init(self, pushService):
    self.status=1  # 1: 运行  0:暂停
    self.pushService = pushService
    self.connector = Connector()
    self.httpHost = "127.0.0.1"
    logging.debug("heart beat init")
    return self
  
  def run(self):
    while True:
      # 以json格式把服务的信息发送给core
      content = {
        "service" : "ate-conn-xx",
        "version" : "1.0.1",
        "heartbeat": 10,
        "kind" : "conn",
        "host" : self.httpHost,
        "port" : 27101,
        "instruments": [
          {
            "manufacturer": 'namisoft',
            "model": 'namisoft',
            "sn": 'n1234'
          }
        ] 
      }
      result = self.pushService.toCloud(content)
      logging.debug(content)
      # 等待
      time.sleep(10)
