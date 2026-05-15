"""
Home 6GB VRAM T2V — 用 CogVideoX-2B 跑 MD Beat 1
模型：THUDM/CogVideoX-2b (2B params、可在 6GB VRAM 跑、需 CPU offload)
首次下載：~10 GB（模型 weights）、之後 cache
輸出：home C:/Users/88697/Documents/video-tests/beat1-cogvideox.mp4
"""
import sys, io, os, time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

OUT_DIR = Path(r"C:\Users\88697\Documents\video-tests")
OUT_DIR.mkdir(exist_ok=True)

# Beat 1 prompt（精簡版、CogVideoX 對長 prompt 容忍度有限）
PROMPT = (
    "Cinematic dark fantasy. A colossal black-scaled armored dragon "
    "with molten lava cracks rears up on a burning battlefield, "
    "spreads massive bat wings wide, and unleashes a thunderous roar. "
    "Sparks and ash swirl in the air. Stormy crimson sky. "
    "Low-angle camera pulling back. Dramatic rim lighting, "
    "photoreal painterly style, 16:9 widescreen."
)

print("=" * 60)
print("  CogVideoX-2B T2V Beat 1 generation")
print("=" * 60)

import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

from diffusers import CogVideoXPipeline
from diffusers.utils import export_to_video

print(f"\n[1/3] 載入 model CogVideoX-2b（首次跑會下載 ~10GB）…")
start = time.time()
pipe = CogVideoXPipeline.from_pretrained(
    "THUDM/CogVideoX-2b",
    torch_dtype=torch.float16,
)
print(f"    載入完成、{time.time()-start:.1f}s")

print(f"\n[2/3] 啟用 CPU offload（6GB VRAM 必須）…")
pipe.enable_model_cpu_offload()
pipe.enable_sequential_cpu_offload()
pipe.vae.enable_slicing()
pipe.vae.enable_tiling()

print(f"\n[3/3] 生成中…")
start = time.time()
video = pipe(
    prompt=PROMPT,
    num_videos_per_prompt=1,
    num_inference_steps=40,
    num_frames=49,           # 6 秒 @ 8 fps
    guidance_scale=6,
    generator=torch.Generator(device="cuda").manual_seed(42),
).frames[0]
print(f"    生成完成、{time.time()-start:.1f}s")

out_path = OUT_DIR / "beat1-cogvideox.mp4"
export_to_video(video, str(out_path), fps=8)
print(f"\n✅ 存到 {out_path}")
print(f"   檔案大小：{out_path.stat().st_size / 1024 / 1024:.1f} MB")
