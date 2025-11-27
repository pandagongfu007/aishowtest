# drv_chr.py
from __future__ import annotations
import os, sys, ctypes
from ctypes import wintypes
from typing import Optional, Tuple, List

# -------- 配置：是否启用“模拟模式” --------
# 方式一：环境变量  set PCIE_MOCK=1
# 方式二：运行时传参  pcie_shell.py --mock
MOCK = bool(int(os.environ.get("PCIE_MOCK", "0")))

# -------- Windows 基本类型 --------
BYTE   = ctypes.c_ubyte
DWORD  = ctypes.c_uint32
BOOL   = ctypes.c_int
HANDLE = wintypes.HANDLE
LPBYTE = ctypes.POINTER(BYTE)
LPDWORD= ctypes.POINTER(DWORD)

# -------- 串口 DCB 结构（按你 C++ 里用到的最小字段）--------
class CHRUART_DCB_ST(ctypes.Structure):
    _fields_ = [
        ("BaudRate", DWORD),
        ("ByteSize", BYTE),
        ("Parity",   BYTE),   # 0N 1O 2E 3M 4S
        ("StopBits", BYTE),   # 0:1 1:1.5 2:2
    ]

# ========= 动态加载 DLL =========
def _dll_path(name: str) -> Optional[str]:
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.join(here, "Lib", name)
    if os.path.exists(cand):
        return cand
    # 交给系统搜索 PATH
    return name

_chr44 = None
_chr34 = None

def _load_dlls(mock: bool = MOCK):
    global _chr44, _chr34
    if mock:
        _chr44 = _chr34 = None
        return
    try:
        _chr44 = ctypes.WinDLL(_dll_path("CHR44X02.dll"))
    except Exception as e:
        _chr44 = None
    try:
        _chr34 = ctypes.WinDLL(_dll_path("CHR34XXX.dll"))
    except Exception as e:
        _chr34 = None

_load_dlls()

# ========= 绑定 44X02 接口（离散量）=========
class DIError(RuntimeError): ...
class SERError(RuntimeError): ...

class CHR44X02:
    def __init__(self):
        self.hdev: Optional[HANDLE] = None
        self.hevt: Optional[HANDLE] = None
        if not MOCK and _chr44 is None:
            raise DIError("未找到 CHR44X02.dll（或位数不匹配）")

        if not MOCK:
            # int CHR44X02_OpenDev(HANDLE*, BYTE)
            _chr44.CHR44X02_OpenDev.argtypes  = [ctypes.POINTER(HANDLE), BYTE]
            _chr44.CHR44X02_OpenDev.restype   = ctypes.c_int

            _chr44.CHR44X02_CloseDev.argtypes = [HANDLE]
            _chr44.CHR44X02_CloseDev.restype  = ctypes.c_int

            _chr44.CHR44X02_ResetDev.argtypes = [HANDLE]
            _chr44.CHR44X02_ResetDev.restype  = ctypes.c_int

            _chr44.CHR44X02_IO_GetInputStatus.argtypes = [HANDLE, BYTE, ctypes.POINTER(BYTE)]
            _chr44.CHR44X02_IO_GetInputStatus.restype  = ctypes.c_int

            _chr44.CHR44X02_IO_SetOutputStatus.argtypes = [HANDLE, BYTE, BYTE]
            _chr44.CHR44X02_IO_SetOutputStatus.restype  = ctypes.c_int

            _chr44.CHR44X02_SetWorkMode.argtypes = [HANDLE, BYTE]
            _chr44.CHR44X02_SetWorkMode.restype  = ctypes.c_int

            _chr44.CHR44X02_SetTrigLine.argtypes = [HANDLE, BYTE]
            _chr44.CHR44X02_SetTrigLine.restype  = ctypes.c_int

            _chr44.CHR44X02_TrigIn_Config.argtypes = [HANDLE, BYTE, BYTE]
            _chr44.CHR44X02_TrigIn_Config.restype  = ctypes.c_int

            _chr44.CHR44X02_TrigIn_CreateEvent.argtypes = [HANDLE, ctypes.POINTER(HANDLE)]
            _chr44.CHR44X02_TrigIn_CreateEvent.restype  = ctypes.c_int

            _chr44.CHR44X02_TrigIn_WaitEvent.argtypes = [HANDLE, HANDLE, DWORD]
            _chr44.CHR44X02_TrigIn_WaitEvent.restype  = DWORD

            _chr44.CHR44X02_TrigIn_CloseEvent.argtypes = [HANDLE, HANDLE]
            _chr44.CHR44X02_TrigIn_CloseEvent.restype  = ctypes.c_int

            _chr44.CHR44X02_TrigIn_GetStatus.argtypes = [HANDLE, ctypes.POINTER(BYTE)]
            _chr44.CHR44X02_TrigIn_GetStatus.restype  = ctypes.c_int

        # 模拟态用本地状态
        self._mock_di = [0]*24
        self._mock_do = [0]*24
        self._workmode = 0
        self._trigline = 0

    # ---- 基本生命周期 ----
    def open(self, card_id: int):
        if MOCK:
            self.hdev = HANDLE(1)
            return
        h = HANDLE()
        rc = _chr44.CHR44X02_OpenDev(ctypes.byref(h), BYTE(card_id))
        if rc != 0 or not h:
            raise DIError(f"CHR44X02_OpenDev rc={rc}")
        self.hdev = h

    def reset(self):
        if MOCK: 
            self._mock_di = [0]*24; self._mock_do=[0]*24
            return
        self._need_open()
        rc = _chr44.CHR44X02_ResetDev(self.hdev)
        if rc != 0: raise DIError(f"Reset rc={rc}")

    def close(self):
        if self.hdev and not MOCK:
            _chr44.CHR44X02_ResetDev(self.hdev)
            if self.hevt:
                _chr44.CHR44X02_TrigIn_CloseEvent(self.hdev, self.hevt)
                self.hevt = None
            _chr44.CHR44X02_CloseDev(self.hdev)
        self.hdev = None

    def _need_open(self):
        if not self.hdev:
            raise DIError("device not open")

    # ---- DI/DO ----
    def di_get(self, ch: int) -> int:
        if MOCK: return self._mock_di[ch]
        self._need_open()
        v = BYTE()
        rc = _chr44.CHR44X02_IO_GetInputStatus(self.hdev, BYTE(ch), ctypes.byref(v))
        if rc != 0: raise DIError(f"GetInputStatus rc={rc}")
        return int(v.value)

    def do_set(self, ch: int, val: int):
        if MOCK: 
            self._mock_do[ch] = 1 if val else 0
            return
        self._need_open()
        rc = _chr44.CHR44X02_IO_SetOutputStatus(self.hdev, BYTE(ch), BYTE(val))
        if rc != 0: raise DIError(f"SetOutput rc={rc}")

    # ---- Trig ----
    def set_workmode(self, m: int):
        if MOCK: self._workmode = m; return
        self._need_open()
        rc = _chr44.CHR44X02_SetWorkMode(self.hdev, BYTE(m))
        if rc != 0: raise DIError(f"SetWorkMode rc={rc}")

    def set_trigline(self, line: int):
        if MOCK: self._trigline = line; return
        self._need_open()
        rc = _chr44.CHR44X02_SetTrigLine(self.hdev, BYTE(line))
        if rc != 0: raise DIError(f"SetTrigLine rc={rc}")

    def trig_cfg(self, line: int, edge: int):
        if MOCK: return
        self._need_open()
        rc = _chr44.CHR44X02_TrigIn_Config(self.hdev, BYTE(line), BYTE(edge))
        if rc != 0: raise DIError(f"TrigIn_Config rc={rc}")

    def trig_wait(self, timeout_ms: int) -> Tuple[int,int]:
        if MOCK:
            # 模拟：100ms 内必到一次
            return (0x00000001, 1)
        self._need_open()
        if not self.hevt:
            evt = HANDLE()
            rc = _chr44.CHR44X02_TrigIn_CreateEvent(self.hdev, ctypes.byref(evt))
            if rc != 0 or not evt: raise DIError(f"CreateEvent rc={rc}")
            self.hevt = evt
        dw = _chr44.CHR44X02_TrigIn_WaitEvent(self.hdev, self.hevt, DWORD(timeout_ms))
        st = BYTE()
        _chr44.CHR44X02_TrigIn_GetStatus(self.hdev, ctypes.byref(st))
        return (int(dw), int(st.value))

# ========= 34XXX 串口 =========
class CHR34XXX:
    def __init__(self):
        if not MOCK and _chr34 is None:
            raise SERError("未找到 CHR34XXX.dll（或位数不匹配）")
        if not MOCK:
            _chr34.CHR34XXX_StartDevice.argtypes = [ctypes.c_int]
            _chr34.CHR34XXX_StartDevice.restype  = BOOL
            _chr34.CHR34XXX_StopDevice.argtypes  = [ctypes.c_int]
            _chr34.CHR34XXX_StopDevice.restype   = BOOL

            _chr34.CHR34XXX_Ch_SetRsMode.argtypes = [ctypes.c_int, BYTE, BYTE, BOOL]
            _chr34.CHR34XXX_Ch_SetRsMode.restype  = BOOL

            _chr34.CHR34XXX_Ch_SetCommState.argtypes = [ctypes.c_int, BYTE, ctypes.POINTER(CHRUART_DCB_ST)]
            _chr34.CHR34XXX_Ch_SetCommState.restype  = BOOL

            _chr34.CHR34XXX_Ch_WriteFile.argtypes = [ctypes.c_int, BYTE, DWORD, LPBYTE, LPDWORD]
            _chr34.CHR34XXX_Ch_WriteFile.restype  = BOOL

            _chr34.CHR34XXX_Ch_ReadFile.argtypes = [ctypes.c_int, BYTE, DWORD, LPBYTE, LPDWORD]
            _chr34.CHR34XXX_Ch_ReadFile.restype  = BOOL

        self.dev_id: Optional[int] = None

    def open(self, dev_id: int):
        if MOCK: self.dev_id = dev_id; return
        ok = _chr34.CHR34XXX_StartDevice(dev_id)
        if not ok: raise SERError("StartDevice fail")
        self.dev_id = dev_id

    def close(self):
        if self.dev_id is not None and not MOCK:
            _chr34.CHR34XXX_StopDevice(self.dev_id)
        self.dev_id = None

    def set_rs(self, ch: int, mode: int, half_duplex: bool = True):
        if MOCK: return
        ok = _chr34.CHR34XXX_Ch_SetRsMode(self.dev_id, BYTE(ch), BYTE(mode), BOOL(1 if half_duplex else 0))
        if not ok: raise SERError("SetRsMode fail")

    def set_comm(self, ch: int, baud: int, data_bits: int, parity: int, stop_bits: int):
        if MOCK: return
        d = CHRUART_DCB_ST(DWORD(baud), BYTE(data_bits), BYTE(parity), BYTE(stop_bits))
        ok = _chr34.CHR34XXX_Ch_SetCommState(self.dev_id, BYTE(ch), ctypes.byref(d))
        if not ok: raise SERError("SetComm fail")

    def write_hex(self, ch: int, hex_bytes: List[int]) -> int:
        if MOCK: return len(hex_bytes)
        arr = (BYTE * len(hex_bytes))(*hex_bytes)
        w = DWORD(0)
        ok = _chr34.CHR34XXX_Ch_WriteFile(self.dev_id, BYTE(ch), DWORD(len(hex_bytes)), arr, ctypes.byref(w))
        if not ok: raise SERError("write fail")
        return int(w.value)

    def read_n(self, ch: int, n: int) -> bytes:
        if MOCK: return b"\x48\x65\x6C\x6C\x6F\x0D\x0A"  # "Hello\r\n"
        buf = (BYTE * n)()
        r = DWORD(0)
        ok = _chr34.CHR34XXX_Ch_ReadFile(self.dev_id, BYTE(ch), DWORD(n), buf, ctypes.byref(r))
        if not ok: raise SERError("read fail")
        return bytes(buf[: int(r.value)])

