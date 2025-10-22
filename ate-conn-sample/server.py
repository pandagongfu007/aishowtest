#!/bin/env python
# coding=utf-8

########################################################################################################################
# http服务
# auth: zhangxuanchao(53536364@qq.com)
# date: 2021-5-13
# 用于接受
########################################################################################################################

from sanic import Sanic
from sanic.response import json
import logging
from conn import Connector

app = Sanic(__name__)


# 接收到要给仪器发送的指令
# url: 
# post /{{id}}
# body
# {
#   "template":"xxxxx",
#   "params":{"aaa":"value1","bbb":"value2"}
#   "type": 1,
#   "replys": [
#     {"code":"aaa","label":"aaa","type":1,"regexps":["[/]\\S+","\\d+"]}
#   ]
# }
@app.route("/test/<tid>/inst/<sn>", methods=['POST'])
def action(request, tid, sn):
  logging.debug("%s start"%tid)
  # 仪器连接器
  connector = Connector()
  # 获取下发信息内容
  reqBode = request.json
  logging.debug(reqBode)
  type = reqBode['type']
  template = reqBode['template']
  params = reqBode['params']
  if type == 2:   # 配置指令
    result = connector.write(sn, template, params)
    logging.debug("%s finish"%tid)
    if result:
      return json({
        "code":200,
        "message":"success"
      })
    else:
      return json({
        "code":400,
        "message":"failure"
      })
  else:          # 读取指令
    replys = reqBode['replys']
    datas = connector.readData(sn, template, params, replys)
    logging.debug("%s finish"%tid)
    return json({
      "code": 200,
      "message": "success",
      "datas": datas
    })
