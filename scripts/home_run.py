"""在 home 上：先裝相依、再啟動 T2V script（背景跑）"""
import subprocess, sys, os, time
from pathlib import Path

OUT = Path(r"C:\Users\88697\Documents\video-tests")
OUT.mkdir(exist_ok=True)

def run(cmd, check=True):
    print(f"$ {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    print(r.stdout[-500:] if r.stdout else "")
    if r.stderr: print("STDERR:", r.stderr[-300:])
    return r.returncode == 0

print("=" * 60)
print("  Diffusers T2V 安裝 + 啟動")
print("=" * 60)

print("\n[1/3] 安裝相依")
run(f"{sys.executable} -m pip install --quiet diffusers transformers accelerate imageio imageio-ffmpeg sentencepiece")

print("\n[2/3] 版本確認")
run(f'{sys.executable} -c "import torch, diffusers; print(\'torch\', torch.__version__); print(\'diffusers\', diffusers.__version__); print(\'CUDA:\', torch.cuda.is_available()); print(\'GPU:\', torch.cuda.get_device_name(0) if torch.cuda.is_available() else \'none\')"')

print("\n[3/3] 背景啟動 T2V script、log → video-tests/run.log")
log_path = OUT / "run.log"
# Windows 背景跑：用 Popen + DETACHED_PROCESS
proc = subprocess.Popen(
    [sys.executable, r"C:\Users\88697\Documents\home_diffusers_t2v.py"],
    stdout=open(log_path, "w", encoding="utf-8"),
    stderr=subprocess.STDOUT,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000008,  # DETACHED
)
print(f"PID: {proc.pid}")
print(f"Log: {log_path}")
print("\n--- 5 秒後檢查初步狀態 ---")
time.sleep(5)
if log_path.exists():
    txt = log_path.read_text(encoding="utf-8", errors="replace")
    print(txt[:500])
