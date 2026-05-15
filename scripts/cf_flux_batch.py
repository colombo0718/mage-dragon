"""
Cloudflare Workers AI Flux Schnell 批次生成 — MD 24 張 motion comic
免費額度 10K Neurons/天、24 張 ~2400 Neurons、完全免費
輸出：mage-dragon/video-tests/motion-comic-cf/
"""
import os, sys, io, time, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# 讀 .env
ENV = {}
for line in Path("C:/Users/USER/mage-dragon/.env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip()

CF_TOKEN = ENV["CLOUDFLARE_API_TOKEN"]
CF_ACCOUNT = ENV["CLOUDFLARE_ACCOUNT_ID"]
MODEL = "@cf/black-forest-labs/flux-1-schnell"
URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/run/{MODEL}"

OUT_DIR = Path("C:/Users/USER/mage-dragon/video-tests/motion-comic-cf")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Part 0 錨點（Flux 用 T5 編碼器、可以塞長 prompt）
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

SHOTS = [
    ("01-beat1-establish",     "Extreme wide shot. Vast smoldering battlefield foreground, the DRAGON's silhouette looming distant against the crimson sky, half-hidden in smoke. Ash drifts."),
    ("02-beat1-emerge",        "Medium-wide. The DRAGON's massive armored body emerges from smoke. Lava cracks pulse. Wings half-folded. Low angle."),
    ("03-beat1-eye",           "Extreme macro close-up on the DRAGON's burning red eye, glowing hot, reflected ember light, molten scales around it."),
    ("04-beat1-rear-up",       "Medium shot. The DRAGON rears up on hind legs, wings unfurling, chest with brightest lava cracks, mouth opening. Low heroic angle."),
    ("05-beat1-roar",          "Close-medium. The DRAGON's maw fully open mid-roar, teeth gleaming, heat distortion air, embers erupting from throat. Low three-quarter."),
    ("06-beat1-wings-spread",  "Wide shot. The DRAGON with wings fully spread blocking the sky, shockwave ripples rolling outward visibly. Dramatic silhouette against red sky."),
    ("07-beat2-standoff",      "Wide shot. BLUE WIZARD left and CRIMSON WIZARD right, 20 meters apart, facing the dragon. Blue raises staff aggressively, crimson palm forward defensively. Ground level."),
    ("08-beat2-cast-lightning","Medium close-up. BLUE WIZARD raising staff with both hands, sapphire-blue lightning crackling at staff tip, lighting his determined face. Side angle dynamic."),
    ("09-beat2-lightning-hit", "Close-up on DRAGON's flank. Blue lightning bolt striking armored scales, sparks scattering, scales absorbing with minimal damage."),
    ("10-beat2-solo-shield",   "Medium shot. CRIMSON WIZARD summoning translucent emerald-green magical shield in front of HIMSELF ONLY, not covering teammate. Anxious face."),
    ("11-beat2-firestream",    "Wide cinematic. The DRAGON unleashing orange-white firestream sweeping across both wizards. Crimson's shield small and insufficient. Fire engulfing foreground."),
    ("12-beat2-blown-back",    "Low angle. Both wizards thrown backward by firestream, robes smoldering, knees buckling, staffs barely held. Pained faces. Embers raining."),
    ("13-beat3-kneeling",      "Close-up. BLUE WIZARD on knees in burning debris, head bowed, blood from cheek cut, beard singed, staff planted beside him. Shallow DoF."),
    ("14-beat3-turn-head",     "Profile close-up. BLUE WIZARD's head slowly turning toward teammate. Embers floating in slow motion foreground. Lit from behind by fire glow."),
    ("15-beat3-meet-eyes",     "Close-up. CRIMSON WIZARD kneeling, panting heavily, sweat on forehead, looking up to meet teammate's gaze. Recognition on face."),
    ("16-beat3-eye-lock",      "Two-shot extreme close-up. Both wizards' eyes locked across the frame, blurred floating embers between. Time frozen. Wordless pact. Profile."),
    ("17-beat3-nod-grip",      "Detail shot. BLUE WIZARD's slight nod mid-motion, CRIMSON WIZARD's gloved knuckles whitening on staff grip. Quiet resolve. Intimate."),
    ("18-beat4-rise-unison",   "Wide shot. Both wizards rising simultaneously from kneeling, robes billowing, staffs lifted in synchronized motion. Twin auras gathering. Low heroic angle."),
    ("19-beat4-staff-slam",    "Medium shot. Both staffs slamming the ground in perfect unison, dust and embers erupting, shockwave radiating from each impact. Grim resolve."),
    ("20-beat4-twin-shields",  "Split close-up two-shot. BLUE WIZARD's sapphire shield bursting forward in crystalline patterns, CRIMSON WIZARD's emerald shield mirroring on other side. Symmetric."),
    ("21-beat4-dome-fused",    "Wide shot. Two shields expand and fuse into one colossal sapphire-emerald light dome encompassing both wizards. Lightning arcs on its surface. Awe-inspiring low angle."),
    ("22-beat4-fire-on-dome",  "Close-up on dome's surface. DRAGON's orange-white firestream crashing against the shield dome, surface bowing inward, light intensifying, about to release."),
    ("23-beat4-reflected-lance","Wide cinematic. Reflected energy launching backward from dome as concentrated lance of white-hot light streaking toward dragon. Diagonal trajectory across frame."),
    ("24-beat4-dragon-fall",   "Wide shot. The DRAGON struck in chest by the lance, roaring in agony, scales shattering and falling away, collapsing backward. Wizards small in victorious foreground."),
]


def gen_one(idx, name, shot_desc):
    out_path = OUT_DIR / f"{name}.jpg"
    if out_path.exists():
        return (name, True, "已存在、跳過", 0)

    full_prompt = f"{PART_0}\n\n{shot_desc}"
    payload = json.dumps({
        "prompt": full_prompt,
        "steps": 8,  # Flux Schnell 4-8 步即可
    }).encode("utf-8")

    req = urllib.request.Request(
        URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {CF_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST"
    )

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            content_type = r.headers.get("Content-Type", "")
            data = r.read()
            elapsed = time.time() - start

            if "json" in content_type:
                # 可能 base64-encoded image 在 JSON 內
                resp = json.loads(data)
                if "result" in resp and "image" in resp["result"]:
                    import base64
                    img_bytes = base64.b64decode(resp["result"]["image"])
                    out_path.write_bytes(img_bytes)
                    return (name, True, f"{elapsed:.1f}s, {len(img_bytes)/1024:.0f}KB", elapsed)
                return (name, False, f"JSON 無 image: {str(resp)[:200]}", elapsed)
            else:
                # 直接 binary
                out_path.write_bytes(data)
                return (name, True, f"{elapsed:.1f}s, {len(data)/1024:.0f}KB", elapsed)

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        return (name, False, f"HTTP {e.code}: {body}", time.time()-start)
    except Exception as e:
        return (name, False, f"{type(e).__name__}: {str(e)[:200]}", time.time()-start)


def main():
    print("=" * 60)
    print(f"  Cloudflare Workers AI Flux Schnell 批次 ({len(SHOTS)} 張)")
    print(f"  Account: {CF_ACCOUNT[:8]}...  Model: {MODEL}")
    print(f"  Output: {OUT_DIR}")
    print("=" * 60)

    # 序列跑（避免 rate limit）
    results = []
    for idx, (name, shot) in enumerate(SHOTS, 1):
        print(f"\n[{idx:2d}/{len(SHOTS)}] {name}")
        r = gen_one(idx, name, shot)
        results.append(r)
        symbol = "✅" if r[1] else "❌"
        print(f"      {symbol} {r[2]}")

    # 總結
    ok = sum(1 for r in results if r[1])
    fail = sum(1 for r in results if not r[1])
    total_t = sum(r[3] for r in results)
    print("\n" + "=" * 60)
    print(f"  ✅ 成功 {ok}/{len(SHOTS)}   ❌ 失敗 {fail}")
    print(f"  總耗時 {total_t:.0f}s ({total_t/60:.1f} 分鐘)")
    print(f"  輸出資料夾：{OUT_DIR}")
    if fail > 0:
        print(f"\n失敗清單：")
        for r in results:
            if not r[1]:
                print(f"  ❌ {r[0]}：{r[2]}")


if __name__ == "__main__":
    main()
