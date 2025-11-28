# pcie_shell.py
# 极简交互式 Shell，调试 CHR34XXX/CHR44X02；新增 ser ver / di ver
from __future__ import annotations
import os, sys, shlex

from drv_chr import CHR34XXX, CHR44X02, BYTE

def print_help():
    print(r"""
[串口卡 CHR34XXX]
  ser open <id>                 打开设备
  ser close                     关闭设备
  ser rs <ch> 232|422|485       设置电气模式
  ser comm <ch> <baud> <data 5-8> <parity n|o|e|m|s> <stop 1|15|2>
  ser tx <ch> <hex...>          发送十六进制字节
  ser rx <ch> <n>               读取 n 字节
  ser ver                       查询 DLL/Driver/FW 版本

[离散量卡 CHR44X02]
  di open <cardId>              打开设备
  di reset                      复位设备
  di close                      关闭设备
  di get <ch>                   读取单通道 DI (0..23)
  do set <ch> <0|1>             写单路 DO
  do all <hexMask>              批量写 24 路（bit0→ch0 ... bit23→ch23）
  trig mode <0|1|2>             工作模式：0单板/1主卡/2从卡
  trig line <0..7>              选择 PXI_TRIG 线
  trig in cfg <line> <edge>     触发输入配置
  trig in open                  创建触发事件
  trig in wait <timeout>        等待触发
  trig in close                 关闭触发事件
  di ver                        查询 DLL/Driver/FW 版本

[其它]
  help                          显示帮助
  exit                          退出
""".strip())

def to_parity(ch: str) -> int:
    p = ch.lower()[0]
    return 0 if p=='n' else 1 if p=='o' else 2 if p=='e' else 3 if p=='m' else 4

def main():
    ser = None   # CHR34XXX 实例
    di  = None   # CHR44X02  实例

    print("PCIe Shell - 输入 help 查看命令。")
    while True:
        try:
            line = input("PS> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue

        try:
            tok = shlex.split(line)
        except ValueError:
            print("[err] 解析失败")
            continue

        cmd = tok[0].lower()

        # --------- 通用 ---------
        if cmd in ("exit", "quit"):
            break
        if cmd == "help":
            print_help()
            continue

        # --------- 串口卡 ser ----------
        if cmd == "ser":
            if len(tok) < 2:
                print("[err] ser 子命令缺失")
                continue
            sub = tok[1].lower()

            if sub == "open":
                if len(tok) < 3:
                    print("[err] usage: ser open <id>")
                    continue
                dev_id = int(tok[2])
                if ser is None: ser = CHR34XXX()
                ok = ser.start(dev_id)
                print("[ok]" if ok else "[err] open fail")
                continue

            if sub == "close":
                if ser: ser.stop()
                print("[ok]")
                continue

            if sub == "ver":
                if not ser:
                    print("[err] ser not open")
                else:
                    v = ser.versions()
                    print(f"SER dll={v['dll']} driver={v['driver']} fw={v['firmware']}")
                continue

            if not ser:
                print("[err] ser not open")
                continue

            if sub == "rs":
                if len(tok) < 4:
                    print("[err] usage: ser rs <ch> 232|422|485")
                    continue
                ch = int(tok[2])
                mode = 0 if tok[3]=="232" else 1 if tok[3]=="422" else 2
                ok = ser.set_rs_mode(ch, mode, True)
                print("[ok]" if ok else "[err]")
                continue

            if sub == "comm":
                if len(tok) < 7:
                    print("[err] usage: ser comm <ch> <baud> <data 5-8> <parity n|o|e|m|s> <stop 1|15|2>")
                    continue
                ch   = int(tok[2])
                baud = int(tok[3])
                data = int(tok[4])
                par  = to_parity(tok[5])
                stop = 1 if tok[6]=="15" else 2 if tok[6]=="2" else 0
                ok   = ser.set_comm(ch, baud, data, par, stop)
                print("[ok]" if ok else "[err]")
                continue

            if sub == "tx":
                if len(tok) < 4:
                    print("[err] usage: ser tx <ch> <hex...>")
                    continue
                ch = int(tok[2])
                buf = bytearray()
                for s in tok[3:]:
                    try:
                        buf.append(int(s,16)&0xFF)
                    except ValueError:
                        print(f"[err] bad hex: {s}")
                        break
                else:
                    n = ser.write(ch, bytes(buf))
                    print(f"[ok] wrote {n}B" if n >= 0 else "[err] write fail")
                continue

            if sub == "rx":
                if len(tok) < 4:
                    print("[err] usage: ser rx <ch> <n>")
                    continue
                ch = int(tok[2]); n = int(tok[3])
                data = ser.read(ch, n)
                print(f"[rx {len(data)}B]")
                # 十六进制打印
                for i,b in enumerate(data):
                    end = "\n" if (i%16==15) else " "
                    print(f"{b:02X}", end=end)
                print()
                continue

            print("[err] 未知 ser 子命令")
            continue

        # --------- 离散卡 di/do/trig/demo ----------
        if cmd == "di":
            if len(tok) < 2:
                print("[err] di 子命令缺失")
                continue
            sub = tok[1].lower()

            if sub == "open":
                if len(tok) < 3:
                    print("[err] usage: di open <cardId>")
                    continue
                cid = int(tok[2])
                if di is None: di = CHR44X02()
                rc = di.open(cid)
                print("[ok]" if rc == 0 else f"[err] rc={rc}")
                continue

            if sub == "reset":
                print("[ok]" if (di and di.reset()==0) else "[err] device not open")
                continue

            if sub == "close":
                if di: di.close()
                print("[ok]")
                continue

            if sub == "get":
                if len(tok) < 3:
                    print("[err] usage: di get <ch>")
                    continue
                if not di:
                    print("[err] device not open")
                    continue
                ch = int(tok[2])
                v  = di.di_get(ch)
                print(f"DI[{ch:02}]={v}" if v >= 0 else "[err]")
                continue

            if sub == "poll":
                if not di:
                    print("[err] device not open")
                    continue
                out = []
                for ch in range(24):
                    out.append(str(di.di_get(ch)))
                print(" ".join(out))
                continue

            if sub == "ver":
                if not di:
                    print("[err] device not open")
                else:
                    v = di.versions()
                    print(f"DI  dll={v['dll']} driver={v['driver']} fw={v['firmware']}")
                continue

            print("[err] 未知 di 子命令")
            continue

        if cmd == "do":
            if len(tok) < 2:
                print("[err] do 子命令缺失")
                continue
            if not di:
                print("[err] device not open")
                continue
            sub = tok[1].lower()
            if sub == "set":
                if len(tok) < 4:
                    print("[err] usage: do set <ch> <0|1>")
                    continue
                ch = int(tok[2]); val = int(tok[3])
                rc = di.do_set(ch, val)
                print("[ok]" if rc == 0 else f"[err] rc={rc}")
                continue
            if sub == "all":
                if len(tok) < 3:
                    print("[err] usage: do all <hexMask>")
                    continue
                mask = int(tok[2], 16)
                for ch in range(24):
                    di.do_set(ch, 1 if ((mask >> ch) & 1) else 0)
                print("[ok]")
                continue
            print("[err] 未知 do 子命令")
            continue

        if cmd == "trig":
            if len(tok) < 2:
                print("[err] trig 子命令缺失")
                continue
            if not di:
                print("[err] device not open")
                continue
            sub = tok[1].lower()
            if sub == "mode":
                m = int(tok[2])
                rc = di.set_workmode(m)
                print("[ok]" if rc == 0 else f"[err] rc={rc}")
                continue
            if sub == "line":
                ln = int(tok[2])
                rc = di.set_trig_line(ln)
                print("[ok]" if rc == 0 else f"[err] rc={rc}")
                continue
            if sub == "in":
                if len(tok) < 3:
                    print("[err] trig in 子命令缺失")
                    continue
                s2 = tok[2].lower()
                if s2 == "cfg":
                    if len(tok) < 5:
                        print("[err] usage: trig in cfg <line> <edge>")
                        continue
                    ln = int(tok[3]); edge = int(tok[4])
                    rc = di.trig_cfg(ln, edge)
                    print("[ok]" if rc == 0 else f"[err] rc={rc}")
                    continue
                if s2 == "open":
                    hev = di.trig_create()
                    print("[ok]" if hev else "[err]")
                    # 保存到全局 for wait
                    globals()["_TRIG_HEV"] = hev
                    continue
                if s2 == "wait":
                    if len(tok) < 4:
                        print("[err] usage: trig in wait <timeout_ms>")
                        continue
                    hev = globals().get("_TRIG_HEV")
                    if not hev:
                        hev = di.trig_create()
                        globals()["_TRIG_HEV"] = hev
                    to  = int(tok[3])
                    dw  = di.trig_wait(hev, to)
                    st  = di.trig_status()
                    print(f"[wait={to}] ret={dw} status={st}")
                    continue
                if s2 == "close":
                    hev = globals().get("_TRIG_HEV")
                    if hev: di.trig_close(hev)
                    globals()["_TRIG_HEV"] = None
                    print("[ok]")
                    continue
            print("[err] 未知 trig 子命令")
            continue

        if cmd == "demo":
            print("（示例命令可按需扩展，对 DO/DI 做演示）")
            continue

        print("[err] 未知命令；输入 help 查看。")

if __name__ == "__main__":
    main()

