# pcie_shell.py
import os, sys, shlex
from prompt_toolkit import PromptSession
from rich import print
from drv_chr import CHR44X02, CHR34XXX, MOCK

def parse_int(s): 
    if s.lower().startswith("0x"): return int(s,16)
    return int(s)

def main():
    mock_cli = ("--mock" in sys.argv)
    if mock_cli:
        os.environ["PCIE_MOCK"] = "1"

    di = None
    ser = None

    help_text = """
[bold cyan]命令：[/]
  help
  exit / quit

[bold magenta]串口卡 CHR34XXX：[/]
  ser open <devId>
  ser close
  ser rs <ch> 232|422|485
  ser comm <ch> <baud> <data 5-8> <parity n|o|e|m|s> <stop 1|15|2>
  ser tx <ch> <hex...>
  ser rx <ch> <n>

[bold yellow]离散量 CHR44X02：[/]
  di open <cardId>
  di reset
  di close
  di get <ch>
  di poll
  do set <ch> <0|1>
  do all <hexMask>
  trig mode <0|1|2>
  trig line <0..7>
  trig in cfg <line> <edge>
  trig in wait <timeout_ms>
"""

    print(f"[green]PCIe Shell (Python) — MOCK={MOCK or mock_cli}[/]\n输入 help 查看命令。\n")
    sess = PromptSession("PS pcie> ")

    while True:
        try:
            line = sess.prompt()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        line = line.strip()
        if not line: 
            continue
        if line in ("exit","quit"): 
            break
        if line == "help":
            print(help_text); 
            continue

        try:
            tok = shlex.split(line)
            if not tok: 
                continue

            # --- 串口 ---
            if tok[0] == "ser":
                if tok[1] == "open":
                    dev = int(tok[2])
                    ser = CHR34XXX(); ser.open(dev)
                    print(f"[ok] ser open {dev}")
                elif tok[1] == "close":
                    if ser: ser.close(); ser=None
                    print("[ok] ser close")
                else:
                    if not ser: 
                        print("[red]err:[/] ser not open"); 
                        continue
                    if tok[1] == "rs":
                        ch = int(tok[2]); mode = {"232":0,"422":1,"485":2}[tok[3]]
                        ser.set_rs(ch, mode, True)
                        print(f"[ok] ch{ch} RS{tok[3]}")
                    elif tok[1] == "comm":
                        ch=int(tok[2]); baud=int(tok[3]); data=int(tok[4])
                        parity = {"n":0,"o":1,"e":2,"m":3,"s":4}[tok[5].lower()]
                        stop   = { "1":0, "15":1, "2":2 }[tok[6]]
                        ser.set_comm(ch, baud, data, parity, stop)
                        print(f"[ok] ch{ch} {baud} {data}{tok[5]}{tok[6]}")
                    elif tok[1] == "tx":
                        ch=int(tok[2]); arr=[int(x,16) for x in tok[3:]]
                        w=ser.write_hex(ch, arr); print(f"[ok] tx {w}B")
                    elif tok[1] == "rx":
                        ch=int(tok[2]); n=int(tok[3]); b=ser.read_n(ch,n)
                        print("[rx]", " ".join(f"{x:02X}" for x in b))
                    else:
                        print("[red]err:[/] ser cmds: open|close|rs|comm|tx|rx")

            # --- 离散量 ---
            elif tok[0] in ("di","do","trig","demo"):
                if tok[0] == "di" and tok[1] == "open":
                    card = int(tok[2]); di = CHR44X02(); di.open(card)
                    print(f"[ok] device opened: {card}")
                else:
                    if not di:
                        print("[red]err:[/] device not open"); 
                        continue

                    if tok[0]=="di":
                        if tok[1]=="reset":
                            di.reset(); print("[ok]")
                        elif tok[1]=="close":
                            di.close(); di=None; print("[ok] device closed")
                        elif tok[1]=="get":
                            ch=int(tok[2]); print(f"DI[{ch:02d}]={di.di_get(ch)}")
                        elif tok[1]=="poll":
                            vals = [di.di_get(i) for i in range(24)]
                            print(" ".join(f"ch[{i:02d}]={v}" for i,v in enumerate(vals)))
                        else:
                            print("[red]err:[/] di cmds: open|reset|close|get|poll")

                    elif tok[0]=="do":
                        if tok[1]=="set":
                            ch=int(tok[2]); v=int(tok[3]); di.do_set(ch,v); print(f"[ok] DO[{ch:02d}]={v}")
                        elif tok[1]=="all":
                            mask = parse_int(tok[2]) & 0xFFFFFF
                            for i in range(24): di.do_set(i, 1 if (mask>>i)&1 else 0)
                            print(f"[ok] mask=0x{mask:06X}")
                        else:
                            print("[red]err:[/] do cmds: set|all")

                    elif tok[0]=="trig":
                        if tok[1]=="mode":
                            di.set_workmode(int(tok[2])); print(f"[ok] workmode={int(tok[2])}")
                        elif tok[1]=="line":
                            di.set_trigline(int(tok[2])); print(f"[ok] trigline={int(tok[2])}")
                        elif tok[1]=="in" and tok[2]=="cfg":
                            di.trig_cfg(int(tok[3]), int(tok[4])); print("[ok] trig cfg")
                        elif tok[1]=="in" and tok[2]=="wait":
                            dw,st = di.trig_wait(int(tok[3])); print(f"[wait] event={dw} status={st}")
                        else:
                            print("[red]err:[/] trig cmds: mode|line|in cfg|in wait")
            else:
                print("[red]err:[/] 未知命令，输入 help")
        except Exception as e:
            print(f"[red]err:[/] {e}")

    # 退出清理
    try:
        if ser: ser.close()
    except: pass
    try:
        if di: di.close()
    except: pass

if __name__ == "__main__":
    main()

