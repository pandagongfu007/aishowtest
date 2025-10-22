#!/bin/env python
# coding=utf-8

########################################################################################################################
# 通过http推送数据
# auth: zhangxuanchao(53536364@qq.com)
# date: 2021-5-7
########################################################################################################################
import httpx
import asyncio
import logging

class PushService:
  
  # 初始化
  # 参数
  #   host 服务地址
  #   port 服务端口
  def __init__(self, host, port):
    self.host = host
    self.port = port

  # 具体推送过程
  async def post(self, content):
    async with httpx.AsyncClient() as client:
      result={
        "code" : 403
      }
      try:
        resp = await client.post('http://%s:%d/heart'%(self.host, self.port), json=content )
        result = resp.json()
      except Exception as e:
        logging.error(e)
      return result

  # 给平台推送数据
  def toCloud(self, content):
    res = asyncio.run(self.post(content))
    return(res)
