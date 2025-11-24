# -*- coding: utf-8 -*-
# 连接器核心模块：管理所有仪器连接，提供资源池和指令处理功能。
  
import threading
from typing import Dict, List, Optional, Tuple, Any

from inst import Instrument
from reply_spec import ReplySpec
from log import Log

# 离散卡 CHR44X02 的 Python 仿真驱动
from drv_sim_aishow import handle_write as drv_write, handle_read as drv_read

logger = Log()


class Connector:
  """连接器类（单例），管理所有仪器连接"""

  _instance: Optional["Connector"] = None
  _lock = threading.Lock()

  def __new__(cls) -> "Connector":
      if cls._instance is None:
          with cls._lock:
              if cls._instance is None:
                  obj = super().__new__(cls)
                  obj.insts: Dict[str, Instrument] = {}
                  obj.lock = threading.Lock()
                  obj.current_code: str = ""   # 当前指令编码，由 server.py 设置
                  cls._instance = obj
      return cls._instance

  # ------------------------------------------------------------------
  # 设备发现 / 资源池管理
  # ------------------------------------------------------------------
  def find(self) -> None:
      """
      发现和检测仪器，更新资源池。

      这里先用硬编码：只配置一块 CHR44X02 离散卡，
      SN = 154001_DO，用来做 TEST_CTRL / TEST_STATUS 验证。
      """

      instrument_configs = [
          # 1) 官方示波器 Demo：mock_oscilloscope.py 对应的两台示波器
          {
              "sn": "a0001",
              "model": "VirtuScope",
              "mfr": "namisoft",
              "host": "127.0.0.1",
              "port": 10013,
          },
          {
              "sn": "a0002",
              "model": "VirtuScope",
              "mfr": "namisoft",
              "host": "127.0.0.1",
              "port": 10014,
          },
  
          # 2) 你的 DUT：显示设备 154001，对应本地 CHR44X02 离散卡
          {
              "sn": "154001",        # 在 ATE 里就用 154001 当成 SN/设备号
              "model": "154001",   # 关键：走 drv_sim_aishow 分支
              "mfr": "fanmai",
              "host": "local",       # 本地 PCIe，不走 socket
              "port": 0,
          },
      ]
  
      threads = []
      for cfg in instrument_configs:
          t = threading.Thread(
              target=self._check_and_add_instrument,
              args=(
                  cfg["sn"],
                  cfg["host"],
                  cfg["port"],
                  cfg.get("model", ""),
                  cfg.get("mfr", ""),
              ),
          )
          t.start()
          threads.append(t)
  
      for t in threads:
          t.join()
  
      logger.info(
          f"Device discovery completed. Found {len(self.insts)} online instruments."
      )


  def _check_and_add_instrument(
      self, sn: str, host: str, port: int, model: str = "", mfr: str = ""
  ) -> None:
      """检查并添加仪器到资源池（含重复 SN 检测 / 重连逻辑）"""
      try:
          with self.lock:
              if sn in self.insts:
                  inst = self.insts[sn]
                  # 同 SN 不同 host/port，当配置冲突处理
                  if inst.host != host or inst.port != port:
                      logger.warning(
                          f"Duplicate SN {sn} with different host/port, "
                          f"existing={inst.host}:{inst.port}, new={host}:{port}"
                      )
                      return
                  # 同一设备，且在线，直接跳过
                  if inst.is_online:
                      logger.debug(f"Instrument {sn} already online, skip add.")
                      return
                  # 同一设备，离线则尝试重连
                  logger.info(f"Instrument {sn} offline, try reconnect...")
                  try:
                      new_inst = Instrument(sn, host, port, model, mfr)
                      if new_inst.is_online:
                          try:
                              inst.close()
                          except Exception:
                              pass
                          self.insts[sn] = new_inst
                          logger.info(f"Instrument {sn} reconnected ok.")
                      else:
                          logger.warning(f"Instrument {sn} reconnect failed.")
                  except Exception as e:
                      logger.warning(f"Reconnecting instrument {sn} failed: {e}")
                  return

          # 新设备
          inst = Instrument(sn, host, port, model, mfr)

          # 对于本地 PCIe 板卡，可以直接认为在线
          if host == "local" and port == 0:
              inst.is_online = True

          if inst.is_online:
              with self.lock:
                  if sn in self.insts:
                      try:
                          inst.close()
                      except Exception:
                          pass
                      logger.debug(
                          f"Instrument {sn} already added by another thread."
                      )
                  else:
                      self.insts[sn] = inst
                      logger.info(f"Instrument {sn} added to resource pool.")
          else:
              logger.warning(
                  f"Instrument {sn} is offline (host={host}, port={port}), not added."
              )
      except Exception as e:
          logger.warning(f"Failed to add instrument {sn}: {e}")

  def get_inst(self, sn: str) -> Optional[Instrument]:
      """根据 SN 获取仪器实例"""
      with self.lock:
          return self.insts.get(sn)

  # ------------------------------------------------------------------
  # 写指令
  # ------------------------------------------------------------------
  def write(
      self, sn: str, instruction: str, params: List[Dict[str, str]]
  ) -> Tuple[bool, str]:
      """
      执行写操作

      sn: 仪器 SN（比如 154001_DO）
      instruction: 指令模板（可能带 {{param}}）
      params: [{"key": "...", "value": "..."}]
      """
      inst = self.get_inst(sn)
      if not inst:
          return False, f"仪器不存在: {sn}"

      if not inst.is_online:
          logger.warning(f"Instrument {sn} is offline during write.")
          return False, f"仪器掉线，当前 sn: {sn}"

      # 本地离散卡：走 Python 仿真，不用 socket
      if inst.model == "154001":
          param_dict = {p["key"]: p["value"] for p in params}
          ok, msg = drv_write(code=self.current_code, params=param_dict)
          return ok, msg

      # 其他设备：按模板替换，通过 socket 写
      processed = self._replace_params(instruction, params)
      result = inst.write(processed)  # 约定返回 (success, message)

      if not result[0] and not inst.is_online:
          logger.warning(f"Instrument {sn} went offline after write.")
      return result

  # ------------------------------------------------------------------
  # 读指令
  # ------------------------------------------------------------------
  def read(
      self,
      sn: str,
      instruction: str,
      params: List[Dict[str, str]],
      replys: List[Any],
      code: str,
  ) -> Tuple[List[Dict], int, str]:
      """
      执行读操作

      返回: (datas, http_code, message)
      """
      inst = self.get_inst(sn)
      if not inst:
          return [], 404, f"仪器不存在: {sn}"

      if not inst.is_online:
          logger.warning(f"Instrument {sn} is offline during read.")
          return [], 400, f"仪器掉线，当前 sn: {sn}"

      # 先把 replys 转成 ReplySpec 列表
      reply_specs: List[ReplySpec] = []
      for r in replys:
          if isinstance(r, dict):
              reply_specs.append(ReplySpec.from_dict(r))
          elif isinstance(r, ReplySpec):
              reply_specs.append(r)
          else:
              logger.warning(f"Invalid reply format: {type(r)}")

      try:
          # 本地离散卡：直接走仿真
          if inst.model == "154001":
              param_dict = {p["key"]: p["value"] for p in params}
              ok, content = drv_read(code=self.current_code, params=param_dict)
              if not ok:
                  return [], 500, content
              datas = self.parse_data(content, reply_specs)
              return datas, 200, "success"

          # 其他设备：参数替换后，通过 socket 读
          processed = self._replace_params(instruction, params)
          content = inst.read(processed)  # 约定返回字符串
          datas = self.parse_data(content, reply_specs)
          return datas, 200, "success"

      except TimeoutError as e:
          return [], 400, str(e)
      except ConnectionError as e:
          inst.is_online = False
          logger.warning(f"Instrument {sn} connection error: {e}")
          return [], 400, str(e)
      except Exception as e:
          logger.error(f"Read operation failed: {e}")
          return [], 500, f"读取操作失败: {e}"

  # ------------------------------------------------------------------
  # 工具方法
  # ------------------------------------------------------------------
  def parse_data(self, content: str, replys: List[ReplySpec]) -> List[Dict[str, Any]]:
      """
      用 ReplySpec 列表解析响应字符串 content
      """
      datas: List[Dict[str, Any]] = []

      for reply in replys:
          try:
              result = reply.parse(content)
              if isinstance(result, list):
                  datas.extend(result)
              else:
                  datas.append(result)
          except Exception as e:
              logger.error(f"Failed to parse reply {reply.key}: {e}")
              datas.append(
                  {
                      "key": reply.key,
                      "type": reply.type,
                      "label": reply.label,
                      "kind": reply.kind,
                      "unit": reply.unit,
                      "value": content,
                  }
              )

      return datas

  def _replace_params(self, template: str, params: List[Dict[str, str]]) -> str:
      """
      把模板里的 {{key}} 替换成 params 里的 value
      """
      import re

      result = template
      param_dict = {p["key"]: p["value"] for p in params}

      pattern = r"\{\{(\w+)\}\}"

      def repl(match: "re.Match") -> str:
          key = match.group(1)
          if key in param_dict:
              return param_dict[key]
          logger.warning(f"Parameter {key} not found in params list")
          return match.group(0)

      return re.sub(pattern, repl, result)

