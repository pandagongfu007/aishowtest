import subprocess
from pathlib import Path

EXE_PATH = Path(r"E:\2025fanmai\code\aishowtest\aishowtestwindrv\x64\Release\aisshowtestwindrv.exe")

def run_shell(cmds):
    script = "\n".join(cmds) + "\nexit\n"
    result = subprocess.run(
        [str(EXE_PATH)],
        input=script,
        text=True,
        capture_output=True,
        timeout=5,
        encoding="utf-8",   # 如果中文有乱码可改成 gbk
    )
    print("returncode:", result.returncode)
    print("stdout:\n", result.stdout)
    print("stderr:\n", result.stderr)

if __name__ == "__main__":
    run_shell([
        "help",      # 看看能否打印帮助
        "di open 0",
        "di poll",
        "di close",
    ])

