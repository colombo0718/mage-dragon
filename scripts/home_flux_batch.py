"""
Home Flux Schnell T2I 批次生成 — MD 24 張 motion comic 關鍵幀
模型：black-forest-labs/FLUX.1-schnell (FP8 量化)
首次下載：~6 GB
輸出：C:/Users/88697/Documents/video-tests/motion-comic/<NN>.jpg
"""
import sys, io, os, time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

OUT_DIR = Path(r"C:\Users\88697\Documents\video-tests\motion-comic-flux")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Part 0 錨點（每張都帶） ──────────────────────────────────
PART_0 = (
    "Dark fantasy painterly photoreal cinematic style, high contrast, "
    "strong rim lighting, volumetric smoke, cinematic depth of field. "
    "Setting: night battlefield with smoldering ruins, broken banners, "
    "ash falling, embers, stormy crimson sky, scattered fires. "
    "Characters: BLUE WIZARD (tall, hooded deep blue robe, silver trim, "
    "grey beard, gnarled staff with sapphire-blue lightning), "
    "CRIMSON WIZARD (shorter, hooded scarlet robe, gold trim, dark staff, "
    "emerald-green magical runes), "
    "DRAGON (colossal black-scaled armored, molten lava cracks, "
    "spike crown, massive bat wings, red eyes, orange-white fire breath). "
    "Palette: deep blacks, crimson, ember orange, electric blue, emerald. "
    "No anime, no cartoon."
)

# ─── 24 個 Shot 描述 ─────────────────────────────────────────
SHOTS = [
    # ── Beat 1 龍 ──
    ("01-beat1-establish",     "Extreme wide shot. Vast smoldering battlefield foreground, the DRAGON's silhouette looming distant against the crimson sky, half-hidden in smoke. Ash drifts."),
    ("02-beat1-emerge",        "Medium-wide. The DRAGON's massive armored body emerges from smoke. Lava cracks pulse. Wings half-folded. Low angle."),
    ("03-beat1-eye",           "Extreme macro close-up on the DRAGON's burning red eye, glowing hot, reflected ember light, molten scales around it."),
    ("04-beat1-rear-up",       "Medium shot. The DRAGON rears up on hind legs, wings unfurling, chest with brightest lava cracks, mouth opening. Low heroic angle."),
    ("05-beat1-roar",          "Close-medium. The DRAGON's maw fully open mid-roar, teeth gleaming, heat distortion air, embers erupting from throat. Low three-quarter."),
    ("06-beat1-wings-spread",  "Wide shot. The DRAGON with wings fully spread blocking the sky, shockwave ripples rolling outward visibly. Dramatic silhouette against red sky."),
    # ── Beat 2 失敗 ──
    ("07-beat2-standoff",      "Wide shot. BLUE WIZARD left and CRIMSON WIZARD right, 20 meters apart, facing the dragon. Blue raises staff aggressively, crimson palm forward defensively. Ground level."),
    ("08-beat2-cast-lightning","Medium close-up. BLUE WIZARD raising staff with both hands, sapphire-blue lightning crackling at staff tip, lighting his determined face. Side angle dynamic."),
    ("09-beat2-lightning-hit", "Close-up on DRAGON's flank. Blue lightning bolt striking armored scales, sparks scattering, scales absorbing with minimal damage."),
    ("10-beat2-solo-shield",   "Medium shot. CRIMSON WIZARD summoning translucent emerald-green magical shield in front of HIMSELF ONLY, not covering teammate. Anxious face."),
    ("11-beat2-firestream",    "Wide cinematic. The DRAGON unleashing orange-white firestream sweeping across both wizards. Crimson's shield small and insufficient. Fire engulfing foreground."),
    ("12-beat2-blown-back",    "Low angle. Both wizards thrown backward by firestream, robes smoldering, knees buckling, staffs barely held. Pained faces. Embers raining."),
    # ── Beat 3 默契 ──
    ("13-beat3-kneeling",      "Close-up. BLUE WIZARD on knees in burning debris, head bowed, blood from cheek cut, beard singed, staff planted beside him. Shallow DoF."),
    ("14-beat3-turn-head",     "Profile close-up. BLUE WIZARD's head slowly turning toward teammate. Embers floating in slow motion foreground. Lit from behind by fire glow."),
    ("15-beat3-meet-eyes",     "Close-up. CRIMSON WIZARD kneeling, panting heavily, sweat on forehead, looking up to meet teammate's gaze. Recognition on face."),
    ("16-beat3-eye-lock",      "Two-shot extreme close-up. Both wizards' eyes locked across the frame, blurred floating embers between. Time frozen. Wordless pact. Profile."),
    ("17-beat3-nod-grip",      "Detail shot. BLUE WIZARD's slight nod mid-motion, CRIMSON WIZARD's gloved knuckles whitening on staff grip. Quiet resolve. Intimate."),
    # ── Beat 4 反殺 ──
    ("18-beat4-rise-unison",   "Wide shot. Both wizards rising simultaneously from kneeling, robes billowing, staffs lifted in synchronized motion. Twin auras gathering. Low heroic angle."),
    ("19-beat4-staff-slam",    "Medium shot. Both staffs slamming the ground in perfect unison, dust and embers erupting, shockwave radiating from each impact. Grim resolve."),
    ("20-beat4-twin-shields",  "Split close-up two-shot. BLUE WIZARD's sapphire shield bursting forward in crystalline patterns, CRIMSON WIZARD's emerald shield mirroring on other side. Symmetric."),
    ("21-beat4-dome-fused",    "Wide shot. Two shields expand and fuse into one colossal sapphire-emerald light dome encompassing both wizards. Lightning arcs on its surface. Awe-inspiring low angle."),
    ("22-beat4-fire-on-dome",  "Close-up on dome's surface. DRAGON's orange-white firestream crashing against the shield dome, surface bowing inward, light intensifying, about to release."),
    ("23-beat4-reflected-lance","Wide cinematic. Reflected energy launching backward from dome as concentrated lance of white-hot light streaking toward dragon. Diagonal trajectory across frame."),
    ("24-beat4-dragon-fall",   "Wide shot. The DRAGON struck in chest by the lance, roaring in agony, scales shattering and falling away, collapsing backward. Wizards small in victorious foreground."),
]

# ─── 載入模型 ────────────────────────────────────────────────
print("=" * 60)
print(f"  Flux Schnell 批次生成 — MD {len(SHOTS)} 張關鍵幀")
print("=" * 60)

# HF 登入（Flux Schnell 是 gated repo）— token 從 .env 讀
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    raise RuntimeError("缺 HF_TOKEN 環境變數（放 .env）")
os.environ["HUGGING_FACE_HUB_TOKEN"] = HF_TOKEN
from huggingface_hub import login
login(token=HF_TOKEN, add_to_git_credential=False)
print("[auth] HF 已登入")

import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

from diffusers import FluxPipeline
print("\n[1/2] 載入 Flux Schnell（首次下載 ~24 GB、cache 後快）…")
start = time.time()

pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-schnell",
    torch_dtype=torch.bfloat16,
)
print(f"    模型載入完成、{time.time()-start:.1f}s")

print("[2/2] 啟用 CPU offload（6GB VRAM 必須）…")
pipe.enable_model_cpu_offload()
pipe.vae.enable_slicing()
pipe.vae.enable_tiling()

print(f"\n=== 開始批次生成、目標 {OUT_DIR} ===\n")

generated = 0
failed = []
for idx, (name, shot_desc) in enumerate(SHOTS, 1):
    out_path = OUT_DIR / f"{name}.jpg"
    if out_path.exists():
        print(f"[{idx:2d}/{len(SHOTS)}] {name} 已存在、跳過")
        generated += 1
        continue

    full_prompt = f"{PART_0}\n\n{shot_desc}"
    print(f"[{idx:2d}/{len(SHOTS)}] {name}")
    print(f"      生成中…", flush=True)
    t0 = time.time()
    try:
        image = pipe(
            prompt=full_prompt,
            guidance_scale=0.0,          # Flux Schnell 用 0（distilled fast model）
            num_inference_steps=4,        # Schnell 4 步出圖
            max_sequence_length=256,      # T5 編碼器吃長 prompt
            generator=torch.Generator("cpu").manual_seed(42 + idx),
            height=576,                   # 16:9、6GB 較省 VRAM
            width=1024,
        ).images[0]
        image.save(out_path, "JPEG", quality=92)
        elapsed = time.time() - t0
        size_kb = out_path.stat().st_size / 1024
        print(f"      ✅ {elapsed:.1f}s、{size_kb:.0f} KB")
        generated += 1
    except Exception as e:
        print(f"      ❌ {type(e).__name__}: {str(e)[:200]}")
        failed.append(name)

print(f"\n=== 完成 ===")
print(f"成功：{generated}/{len(SHOTS)}")
if failed:
    print(f"失敗：{failed}")
print(f"輸出：{OUT_DIR}")
