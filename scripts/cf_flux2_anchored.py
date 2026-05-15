"""
Cloudflare Workers AI Flux 2 Klein 批次（含 reference_images 風格錨點）
模型：@cf/black-forest-labs/flux-2-klein-4b（支援 multi-reference）
參考圖：cover.jpg（MD 概念圖、鎖風格 + 角色 + 龍）
輸出：mage-dragon/video-tests/motion-comic-cf-anchored/
價格：~$0.035/張、24 張 ~$0.84（partner model、不在免費 Neurons 額度內）
"""
import os, sys, io, time, json, base64
from pathlib import Path
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

ENV = {}
for line in Path("C:/Users/USER/mage-dragon/.env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip()

CF_TOKEN = ENV["CLOUDFLARE_API_TOKEN"]
CF_ACCOUNT = ENV["CLOUDFLARE_ACCOUNT_ID"]
MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/run/{MODEL}"

REFERENCE_IMG = Path("C:/Users/USER/mage-dragon/cover.jpg")
OUT_DIR = Path("C:/Users/USER/mage-dragon/video-tests/motion-comic-cf-anchored")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Part 0 + Shot 同前
PART_0 = (
    "Match the visual style, character designs, and color palette of the reference image. "
    "Same BLUE WIZARD (deep blue robe, silver trim, lightning staff), "
    "same CRIMSON WIZARD (scarlet robe, gold trim, emerald magic), "
    "same DRAGON (black armored, lava cracks, bat wings, fire breath). "
    "Dark fantasy painterly photoreal cinematic style. "
    "Night battlefield, embers, stormy crimson sky."
)

SHOTS = [
    ("01-beat1-establish",     "Extreme wide shot. Smoldering battlefield foreground, DRAGON silhouette distant against crimson sky in smoke. Ash drifts."),
    ("02-beat1-emerge",        "Medium-wide. DRAGON massive armored body emerges from smoke. Lava cracks pulse. Low angle."),
    ("03-beat1-eye",           "Extreme macro close-up on DRAGON's burning red eye, molten scales around it."),
    ("04-beat1-rear-up",       "Medium. DRAGON rears on hind legs, wings unfurling, chest lava cracks brightest, mouth opening. Heroic low angle."),
    ("05-beat1-roar",          "Close-medium. DRAGON's maw open mid-roar, heat distortion, embers erupting from throat."),
    ("06-beat1-wings-spread",  "Wide. DRAGON wings fully spread blocking sky, shockwave ripples. Silhouette against red sky."),
    ("07-beat2-standoff",      "Wide. BLUE WIZARD left and CRIMSON WIZARD right, 20m apart, facing dragon. Blue staff raised, crimson palm forward."),
    ("08-beat2-cast-lightning","Medium close-up. BLUE WIZARD raising staff, sapphire-blue lightning crackling at tip, illuminating his face."),
    ("09-beat2-lightning-hit", "Close-up on DRAGON's flank. Blue lightning bolt striking armored scales, sparks scattering, minimal damage."),
    ("10-beat2-solo-shield",   "Medium. CRIMSON WIZARD summoning emerald-green shield ONLY in front of HIMSELF, not covering teammate."),
    ("11-beat2-firestream",    "Wide cinematic. DRAGON unleashing orange-white firestream across both wizards. Crimson's shield insufficient."),
    ("12-beat2-blown-back",    "Low angle. Both wizards thrown backward by firestream, robes smoldering, knees buckling. Pained faces."),
    ("13-beat3-kneeling",      "Close-up. BLUE WIZARD on knees in burning debris, head bowed, blood from cheek, staff planted beside."),
    ("14-beat3-turn-head",     "Profile close-up. BLUE WIZARD's head slowly turning toward teammate. Embers floating. Lit from behind."),
    ("15-beat3-meet-eyes",     "Close-up. CRIMSON WIZARD kneeling, panting, sweat on forehead, looking up to meet teammate's gaze."),
    ("16-beat3-eye-lock",      "Two-shot extreme close-up. Both wizards' eyes locked, blurred embers between. Time frozen. Wordless pact."),
    ("17-beat3-nod-grip",      "Detail. BLUE WIZARD's slight nod mid-motion, CRIMSON WIZARD's gloved knuckles whitening on staff grip."),
    ("18-beat4-rise-unison",   "Wide. Both wizards rising simultaneously from kneeling, robes billowing, staffs lifted in sync. Twin auras."),
    ("19-beat4-staff-slam",    "Medium. Both staffs slamming the ground in unison, dust and embers erupting, shockwave from each."),
    ("20-beat4-twin-shields",  "Split close-up. BLUE WIZARD's sapphire shield bursting forward, CRIMSON WIZARD's emerald shield mirroring."),
    ("21-beat4-dome-fused",    "Wide. Two shields expand and fuse into one colossal sapphire-emerald light dome around both wizards."),
    ("22-beat4-fire-on-dome",  "Close-up on dome's surface. DRAGON's firestream crashing against shield dome, bowing inward, light intensifying."),
    ("23-beat4-reflected-lance","Wide cinematic. Reflected energy launching backward from dome as lance of white-hot light toward dragon."),
    ("24-beat4-dragon-fall",   "Wide. DRAGON struck by lance, roaring in agony, scales shattering, collapsing backward. Wizards victorious in foreground."),
]


def gen_one(idx, name, shot_desc):
    out_path = OUT_DIR / f"{name}.jpg"
    if out_path.exists():
        return (name, True, "已存在、跳過", 0)

    full_prompt = f"{PART_0}\n\n{shot_desc}"
    headers = {"Authorization": f"Bearer {CF_TOKEN}"}

    # multipart form：prompt + reference_images（file）+ 參數
    with open(REFERENCE_IMG, "rb") as f:
        files = {
            "reference_images": ("ref.jpg", f, "image/jpeg"),
        }
        data = {
            "prompt": full_prompt,
            "steps": "8",
            "width": "1024",
            "height": "576",
        }
        t0 = time.time()
        try:
            r = requests.post(URL, headers=headers, files=files, data=data, timeout=180)
            elapsed = time.time() - t0
            if r.status_code != 200:
                return (name, False, f"HTTP {r.status_code}: {r.text[:200]}", elapsed)
            resp = r.json()
            if "result" in resp and "image" in resp["result"]:
                img_b64 = resp["result"]["image"]
                img_bytes = base64.b64decode(img_b64)
                out_path.write_bytes(img_bytes)
                return (name, True, f"{elapsed:.1f}s, {len(img_bytes)/1024:.0f}KB", elapsed)
            return (name, False, f"無 image 欄位: {str(resp)[:200]}", elapsed)
        except Exception as e:
            return (name, False, f"{type(e).__name__}: {str(e)[:200]}", time.time()-t0)


def main():
    print("=" * 60)
    print(f"  Flux 2 Klein 4B + reference_images 鎖風格")
    print(f"  參考圖: {REFERENCE_IMG.name}")
    print(f"  Output: {OUT_DIR}")
    print(f"  預估成本: ~$0.84 (24 × $0.035)")
    print("=" * 60)

    # 先跑 1 張驗證
    print(f"\n--- 試跑 Shot 01、確認可行 + 看品質 ---")
    r = gen_one(1, SHOTS[0][0], SHOTS[0][1])
    print(f"  {'✅' if r[1] else '❌'} {r[2]}")
    if not r[1]:
        print("\n試跑失敗、中止。")
        return

    print(f"\n--- 試跑成功、繼續剩下 23 張 ---")
    results = [r]
    for idx, (name, shot) in enumerate(SHOTS[1:], 2):
        print(f"[{idx:2d}/24] {name}")
        r = gen_one(idx, name, shot)
        results.append(r)
        print(f"      {'✅' if r[1] else '❌'} {r[2]}")

    ok = sum(1 for r in results if r[1])
    fail = sum(1 for r in results if not r[1])
    total_t = sum(r[3] for r in results)
    print("\n" + "=" * 60)
    print(f"  ✅ 成功 {ok}/24  ❌ 失敗 {fail}")
    print(f"  耗時 {total_t:.0f}s  輸出: {OUT_DIR}")


if __name__ == "__main__":
    main()
