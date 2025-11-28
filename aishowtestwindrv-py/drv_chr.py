# drv_chr.py
# 统一封装 CHR34XXX（串口卡）与 CHR44X02（离散量卡）最小集接口 + 版本查询
# - 自动从 ./Lib 或系统 PATH 加载 x64 DLL
# - 设置环境变量 PCIE_MOCK=1 或未找到 DLL 时进入模拟模式

from __future__ import annotations
import os, ctypes, sys, pathlib, platform
from typing import Optional

# ---- 环境与类型别名 ----
IS_64 = platform.architecture()[0] == "64bit"
MOCK  = os.environ.get("PCIE_MOCK", "0") == "1"

DWORD  = ctypes.c_uint32
BYTE   = ctypes.c_uint8
HANDLE = ctypes.c_void_p
BOOL   = ctypes.c_int

# ---- 工具：查找并加载 DLL ----
def _find_dll(name: str) -> Optional[str]:
    # 优先 ./Lib
    here = pathlib.Path(__file__).resolve().parent
    cand = here / "Lib" / name
    if cand.exists():
        return str(cand)
    # 兼容大小写或另一路径
    for p in [here, here / "Lib", here.parent, pathlib.Path(os.getcwd())]:
        f = p / name
        if f.exists():
            return str(f)
    return None

def _load_dll(name: str) -> Optional[ctypes.CDLL]:
    path = _find_dll(name)
    if not path:
        return None
    try:
        return ctypes.WinDLL(path)
    except Exception:
        return None

def _dw_to_verstr(dw: int) -> str:
    a = (dw >> 24) & 0xFF
    b = (dw >> 16) & 0xFF
    c = (dw >> 8)  & 0xFF
    d = (dw >> 0)  & 0xFF
    return f"{a}.{b}.{c}.{d}"

def _bind_opt(dll, name, argtypes=None, restype=ctypes.c_uint32):
    """绑定可选导出；不存在时返回 None"""
    if dll is None:
        return None
    try:
        fn = getattr(dll, name)
        if argtypes is not None:
            fn.argtypes = argtypes
        fn.restype = restype
        return fn
    except Exception:
        return None


# ======================================================================
#                           CHR44X02（离散卡）
# ======================================================================
class CHR44X02:
    _dll_name = "CHR44X02.dll"

    def __init__(self):
        global MOCK
        self._dll = _load_dll(self._dll_name)
        if self._dll is None:
            MOCK = True
        self.hdev: HANDLE = None
        self._bind()

    # 绑定最小集接口
    def _bind(self):
        d = self._dll
        self._OpenDev   = _bind_opt(d, "CHR44X02_OpenDev",   [ctypes.POINTER(HANDLE), BYTE], ctypes.c_int)
        self._CloseDev  = _bind_opt(d, "CHR44X02_CloseDev",  [HANDLE], ctypes.c_int)
        self._ResetDev  = _bind_opt(d, "CHR44X02_ResetDev",  [HANDLE], ctypes.c_int)

        self._GetDI     = _bind_opt(d, "CHR44X02_IO_GetInputStatus", [HANDLE, BYTE, ctypes.POINTER(BYTE)], ctypes.c_int)
        self._SetDO     = _bind_opt(d, "CHR44X02_IO_SetOutputStatus",[HANDLE, BYTE, BYTE], ctypes.c_int)

        self._SetWork   = _bind_opt(d, "CHR44X02_SetWorkMode",[HANDLE, BYTE], ctypes.c_int)
        self._SetTrigLn = _bind_opt(d, "CHR44X02_SetTrigLine",[HANDLE, BYTE], ctypes.c_int)

        self._TrigCfg   = _bind_opt(d, "CHR44X02_TrigIn_Config",      [HANDLE, BYTE, BYTE], ctypes.c_int)
        self._TrigEvt   = _bind_opt(d, "CHR44X02_TrigIn_CreateEvent", [HANDLE, ctypes.POINTER(HANDLE)], ctypes.c_int)
        self._TrigWait  = _bind_opt(d, "CHR44X02_TrigIn_WaitEvent",   [HANDLE, HANDLE, DWORD], DWORD)
        self._TrigGet   = _bind_opt(d, "CHR44X02_TrigIn_GetStatus",   [HANDLE, ctypes.POINTER(BYTE)], ctypes.c_int)
        self._TrigClose = _bind_opt(d, "CHR44X02_TrigIn_CloseEvent",  [HANDLE, HANDLE], ctypes.c_int)

        # 版本接口（可选）
        self._GetDLLVer = _bind_opt(d, "CHR44X02_GetDLLVersion",  [], DWORD)
        self._GetDRVVer = _bind_opt(d, "CHR44X02_GetDriverVersion",[], DWORD)
        self._GetFWVer  = _bind_opt(d, "CHR44X02_GetFirmwareVersion", [HANDLE, ctypes.POINTER(DWORD)], ctypes.c_int)

    # ---- 生命周期 ----
    def open(self, card_id: int) -> int:
        if MOCK:
            self.hdev = HANDLE(1)
            return 0
        if not self._OpenDev:
            return -1
        h = HANDLE()
        rc = self._OpenDev(ctypes.byref(h), BYTE(card_id))
        if rc == 0:
            self.hdev = h
        return rc

    def reset(self) -> int:
        if not self.hdev: return 0
        if MOCK: return 0
        return 0 if not self._ResetDev else self._ResetDev(self.hdev)

    def close(self) -> int:
        if not self.hdev: return 0
        if MOCK:
            self.hdev = None
            return 0
        rc = 0
        if self._ResetDev: rc = self._ResetDev(self.hdev)
        if self._CloseDev: rc = self._CloseDev(self.hdev)
        self.hdev = None
        return rc

    # ---- IO ----
    def di_get(self, ch: int) -> int:
        if MOCK: return 1 if (ch % 2) else 0
        if not self._GetDI or not self.hdev: return -1
        v = BYTE(0)
        rc = self._GetDI(self.hdev, BYTE(ch), ctypes.byref(v))
        return v.value if rc == 0 else -1

    def do_set(self, ch: int, val: int) -> int:
        if MOCK: return 0
        if not self._SetDO or not self.hdev: return -1
        return self._SetDO(self.hdev, BYTE(ch), BYTE(val))

    # ---- 模式 & 触发 ----
    def set_workmode(self, m: int) -> int:
        if MOCK: return 0
        if not self._SetWork or not self.hdev: return -1
        return self._SetWork(self.hdev, BYTE(m))

    def set_trig_line(self, ln: int) -> int:
        if MOCK: return 0
        if not self._SetTrigLn or not self.hdev: return -1
        return self._SetTrigLn(self.hdev, BYTE(ln))

    def trig_cfg(self, ln: int, edge: int) -> int:
        if MOCK: return 0
        if not self._TrigCfg or not self.hdev: return -1
        return self._TrigCfg(self.hdev, BYTE(ln), BYTE(edge))

    def trig_create(self) -> Optional[HANDLE]:
        if MOCK: return HANDLE(2)
        if not self._TrigEvt or not self.hdev: return None
        h = HANDLE()
        rc = self._TrigEvt(self.hdev, ctypes.byref(h))
        return h if rc == 0 else None

    def trig_wait(self, hev: HANDLE, timeout_ms: int) -> int:
        if MOCK: return 0  # signaled
        if not self._TrigWait or not self.hdev: return -1
        return int(self._TrigWait(self.hdev, hev, DWORD(timeout_ms)))

    def trig_status(self) -> int:
        if MOCK: return 1
        if not self._TrigGet or not self.hdev: return -1
        v = BYTE(0)
        rc = self._TrigGet(self.hdev, ctypes.byref(v))
        return v.value if rc == 0 else -1

    def trig_close(self, hev: HANDLE) -> int:
        if MOCK: return 0
        if not self._TrigClose or not self.hdev: return -1
        return self._TrigClose(self.hdev, hev)

    # ---- 版本 ----
    def versions(self) -> dict:
        if MOCK:
            return {"dll":"1.0.0.0","driver":"1.0.0.0","firmware":"1.0.0.0"}
        out = {"dll":None,"driver":None,"firmware":None}
        try:
            if self._GetDLLVer: out["dll"] = _dw_to_verstr(int(self._GetDLLVer()))
        except: pass
        try:
            if self._GetDRVVer: out["driver"] = _dw_to_verstr(int(self._GetDRVVer()))
        except: pass
        try:
            if self._GetFWVer and self.hdev:
                dw = DWORD(0)
                rc = self._GetFWVer(self.hdev, ctypes.byref(dw))
                if rc == 0:
                    out["firmware"] = _dw_to_verstr(int(dw.value))
        except: pass
        return out


# ======================================================================
#                           CHR34XXX（串口卡）
# ======================================================================
class CHR34XXX:
    _dll_name = "CHR34XXX.dll"

    def __init__(self):
        global MOCK
        self._dll = _load_dll(self._dll_name)
        if self._dll is None:
            MOCK = True
        self.dev_id: Optional[int] = None
        self._bind()

    def _bind(self):
        d = self._dll
        # 生命周期
        self._Start = _bind_opt(d, "CHR34XXX_StartDevice", [ctypes.c_int], BOOL)
        self._Stop  = _bind_opt(d, "CHR34XXX_StopDevice",  [ctypes.c_int], BOOL)
        # 设置
        self._SetRs = _bind_opt(d, "CHR34XXX_Ch_SetRsMode", [ctypes.c_int, BYTE, BYTE, BOOL], BOOL)
        # DCB 结构（按手册）
        class CHRUART_DCB_ST(ctypes.Structure):
            _fields_ = [
                ("BaudRate", DWORD),
                ("ByteSize", BYTE),
                ("Parity",   BYTE),
                ("StopBits", BYTE),
            ]
        self.CHRE_DCB = CHRUART_DCB_ST
        self._SetComm = _bind_opt(d, "CHR34XXX_Ch_SetCommState",
                                  [ctypes.c_int, BYTE, ctypes.POINTER(CHRUART_DCB_ST)], BOOL)
        # IO
        self._Write = _bind_opt(d, "CHR34XXX_Ch_WriteFile",
                                [ctypes.c_int, BYTE, DWORD, ctypes.c_void_p, ctypes.POINTER(DWORD)], BOOL)
        self._Read  = _bind_opt(d, "CHR34XXX_Ch_ReadFile",
                                [ctypes.c_int, BYTE, DWORD, ctypes.c_void_p, ctypes.POINTER(DWORD)], BOOL)

        # 版本
        self._GetDLLVer = _bind_opt(d, "CHR34XXX_GetDLLVersion",  [], DWORD)
        self._GetDRVVer = _bind_opt(d, "CHR34XXX_GetDriverVersion",[], DWORD)
        self._GetFWVer  = _bind_opt(d, "CHR34XXX_GetFirmwareVersion",
                                    [ctypes.c_int, ctypes.POINTER(DWORD)], ctypes.c_int)

    # ---- 生命周期 ----
    def start(self, dev_id: int) -> bool:
        if MOCK:
            self.dev_id = int(dev_id)
            return True
        if not self._Start: return False
        ok = bool(self._Start(int(dev_id)))
        if ok: self.dev_id = int(dev_id)
        return ok

    def stop(self) -> bool:
        if self.dev_id is None: return True
        if MOCK:
            self.dev_id = None
            return True
        if not self._Stop: return False
        ok = bool(self._Stop(int(self.dev_id)))
        self.dev_id = None
        return ok

    # ---- 参数 ----
    # mode: 0=232,1=422,2=485; term=True/False
    def set_rs_mode(self, ch: int, mode: int, term: bool=True) -> bool:
        if MOCK: return True
        if not self._SetRs or self.dev_id is None: return False
        return bool(self._SetRs(int(self.dev_id), BYTE(ch), BYTE(mode), BOOL(1 if term else 0)))

    # DCB: baud, byteSize, parity(0n/1o/2e/3m/4s), stopBits(0:1,1:1.5,2:2)
    def set_comm(self, ch: int, baud: int, byte_size: int=8, parity: int=0, stop_bits: int=0) -> bool:
        if MOCK: return True
        if not self._SetComm or self.dev_id is None: return False
        dcb = self.CHRE_DCB(DWORD(baud), BYTE(byte_size), BYTE(parity), BYTE(stop_bits))
        return bool(self._SetComm(int(self.dev_id), BYTE(ch), ctypes.byref(dcb)))

    # ---- IO ----
    def write(self, ch: int, data: bytes) -> int:
        if MOCK: return len(data)
        if not self._Write or self.dev_id is None: return -1
        n = DWORD(0)
        ok = self._Write(int(self.dev_id), BYTE(ch), DWORD(len(data)),
                         ctypes.c_char_p(data), ctypes.byref(n))
        return int(n.value) if ok else -1

    def read(self, ch: int, nbytes: int) -> bytes:
        if MOCK:  # 模拟：回显长度
            return bytes([0x30 + (i % 10) for i in range(max(0, nbytes))])
        if not self._Read or self.dev_id is None: return b""
        buf = (ctypes.c_ubyte * nbytes)()
        n   = DWORD(0)
        ok  = self._Read(int(self.dev_id), BYTE(ch), DWORD(nbytes),
                         ctypes.cast(buf, ctypes.c_void_p), ctypes.byref(n))
        return bytes(buf[: int(n.value)]) if ok else b""

    # ---- 版本 ----
    def versions(self) -> dict:
        if MOCK:
            return {"dll":"1.0.0.0","driver":"1.0.0.0","firmware":"1.0.0.0"}
        out = {"dll":None,"driver":None,"firmware":None}
        try:
            if self._GetDLLVer: out["dll"] = _dw_to_verstr(int(self._GetDLLVer()))
        except: pass
        try:
            if self._GetDRVVer: out["driver"] = _dw_to_verstr(int(self._GetDRVVer()))
        except: pass
        try:
            if self._GetFWVer and (self.dev_id is not None):
                dw = DWORD(0)
                rc = self._GetFWVer(int(self.dev_id), ctypes.byref(dw))
                if rc == 0:
                    out["firmware"] = _dw_to_verstr(int(dw.value))
        except: pass
        return out

