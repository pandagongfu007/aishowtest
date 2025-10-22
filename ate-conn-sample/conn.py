#!/bin/env python
# coding=utf-8

########################################################################################################################
# 连接管理器
# auth: zhangxuanchao(53536364@qq.com)
# date: 2021-5-12
# 管理所有连接的仪器，并把读写指令发送给仪器
########################################################################################################################

import logging


class Connector(object):

  # 单例模式
  def __new__(cls, *args, **kwargs):
    if not hasattr(cls, '_instance'):
      cls._instance = super(Connector, cls).__new__(cls)
    return cls._instance

  # 初始化
  def __init__(self):
    if hasattr(self, 'initialized'):
      return
    self.instrument = {}
    self.initialized = True

  # 设置仪器参数
  def write(self, sn, instruction, params) :
    # 根据参数构建完整指令
    pass
    # 指令开发给仪器
    pass
    return True

  # 读取仪器数据
  def readData(self, sn, instruction, params, replys) :
    # 根据参数构建完整指令
    pass
    # 从仪器读取数据
    pass
    # 格式化为json
    result = []
    pass
    return result
