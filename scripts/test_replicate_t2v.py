"""
Replicate 平行 T2V 測試 — MD Beat 1
測試模型混搭：cheap + medium + premium
輸出：mage-dragon/video-tests/replicate-<model>.mp4
"""
import os, sys, io, time, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# 讀 .env
ENV = {}
for line in Path("C:/Users/USER/mage-dragon/.env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip()

os.environ["REPLICATE_API_TOKEN"] = ENV["REPLICATE_API_TOKEN"]
import replicate

OUT_DIR = Path("C:/Users/USER/mage-dragon/video-tests")
OUT_DIR.mkdir(exist_ok=True)

# ─── Beat 1 prompt ────────────────────────────────────────────
PROMPT = (
    "Cinematic dark fantasy. A colossal black-scaled armored dragon "
    "with molten lava cracks rears up on a burning battlefield, "
    "spreads massive bat wings wide, and unleashes a thunderous roar. "
    "Sparks and ash swirl in the air. Stormy crimson sky. "
    "Low-angle camera pulling back. Dramatic rim lighting, "
    "photoreal painterly style, 16:9 widescreen."
)

# ─── 模型清單（混合價位）──────────────────────────────────────
# 註：價格估算、實際以 Replicate billing 為準
MODELS = [
    {
        "id": "lightricks/ltx-video",
        "short": "ltx-video",
        "est_cost": "$0.04",
        "input": {
            "prompt": PROMPT,
            "length": 121,           # ~5 秒 @ 24fps
            "cfg": 3.0,
            "steps": 30,
        }
    },
    {
        "id": "minimax/video-01",
        "short": "minimax-hailuo",
        "est_cost": "$0.50",
        "input": {
            "prompt": PROMPT,
            "prompt_optimizer": True,
        }
    },
    {
        "id": "tencent/hunyuan-video",
        "short": "hunyuan-video",
        "est_cost": "$0.30",
        "input": {
            "prompt": PROMPT,
            "video_length": "5s",
            "aspect_ratio": "16:9",
            "infer_steps": 30,
        }
    },
]

# ─── 跑單一模型 ───────────────────────────────────────────────
def run_model(m):
    short = m["short"]
    print(f"\n[{short}] 🚀 啟動（est. {m['est_cost']}）…")
    start = time.time()
    try:
        output = replicate.run(m["id"], input=m["input"])
        elapsed = time.time() - start
        print(f"[{short}] ✓ 完成、{elapsed:.0f}s、output type: {type(output).__name__}")

        # output 可能是 URL（str）、URLs（list）、或 FileOutput 物件
        url = None
        if isinstance(output, str):
            url = output
        elif isinstance(output, list) and output:
            url = output[0] if isinstance(output[0], str) else str(output[0])
        elif hasattr(output, 'url'):
            url = output.url
        else:
            url = str(output)

        print(f"[{short}] URL: {url}")
        out_path = OUT_DIR / f"replicate-{short}.mp4"

        # 下載
        if url.startswith("http"):
            print(f"[{short}] 下載中…")
            urllib.request.urlretrieve(url, str(out_path))
        else:
            # 可能是 FileOutput、可呼叫 .read()
            with open(out_path, "wb") as f:
                f.write(output.read() if hasattr(output, 'read') else url.encode())

        size_mb = out_path.stat().st_size / 1024 / 1024
        print(f"[{short}] ✅ 存到 {out_path} ({size_mb:.1f} MB)")
        return (short, str(out_path), elapsed, size_mb)

    except Exception as e:
        print(f"[{short}] ❌ {type(e).__name__}: {str(e)[:300]}")
        return (short, None, time.time() - start, 0)


# ─── Main ─────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Replicate 平行 T2V 測試 — MD Beat 1（龍咆嘯）")
    print("=" * 60)
    print(f"  模型數：{len(MODELS)}")
    print(f"  輸出資料夾：{OUT_DIR}")

    results = []
    with ThreadPoolExecutor(max_workers=len(MODELS)) as exe:
        futures = {exe.submit(run_model, m): m for m in MODELS}
        for f in as_completed(futures):
            results.append(f.result())

    print("\n" + "=" * 60)
    print("  總結")
    print("=" * 60)
    for short, path, elapsed, size in sorted(results):
        status = f"✅ {size:5.1f} MB, {elapsed:5.0f}s, {path}" if path else f"❌ 失敗 ({elapsed:.0f}s)"
        print(f"  {short:20} {status}")
    print(f"\n📁 全部 mp4 在: {OUT_DIR}")
    print(f"💰 預計成本: ~$0.84（trial $1 內）")


if __name__ == "__main__":
    main()
