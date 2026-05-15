"""
T2V API 平行測試 - MD Beat 1 龍咆嘯
測試提供者：
  1. Google Veo 3（Gemini API）⭐ 旗艦
  2. HuggingFace Inference API（開源模型）
輸出：mage-dragon/video-tests/<provider>-<model>.mp4
"""
import os, sys, io, time, json, re
from pathlib import Path
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# ─── 讀 .env ───────────────────────────────────────────────────
ENV_PATH = Path("C:/Users/USER/mage-dragon/.env")
ENV = {}
for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"): continue
    if "=" in line:
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip()

GEMINI_KEY = ENV.get("GEMINI_API_KEY", "")
HF_TOKEN = ENV.get("HF_TOKEN", "")

OUT_DIR = Path("C:/Users/USER/mage-dragon/video-tests")
OUT_DIR.mkdir(exist_ok=True)

# ─── 共用 prompt ───────────────────────────────────────────────
PART_0 = """[CHARACTERS]
TWO WIZARDS: BLUE WIZARD in hooded deep blue robe with silver trim, grey beard, gnarled wooden staff with crackling sapphire-blue lightning. CRIMSON WIZARD in hooded scarlet robe with gold trim, dark wooden staff summoning emerald-green circular runes.
DRAGON: colossal black-scaled armored dragon, molten lava cracks across body, spike crown, massive bat wings, smoldering red eyes, breathes orange-white fire.
[WORLD] Night battlefield, smoldering ruins, ash falling, embers swirling, stormy crimson sky, scattered fires.
[STYLE] Dark fantasy painterly photoreal cinematic, dramatic rim lighting, volumetric smoke, deep blacks + crimson + ember orange + electric blue + emerald."""

BEAT_1 = "SCENE: The DRAGON rears up and unleashes a thunderous roar. Wings spread wide, blocking the crimson sky. Shockwave of heat and ash rolls outward. Sparks swirl violently. CAMERA: low-angle pull-back, slow dolly out. ASPECT: 16:9 widescreen cinematic. DURATION: 5 seconds."

FULL_PROMPT = PART_0 + "\n\n" + BEAT_1

# ─── Provider 1: Veo 3（Gemini API）──────────────────────────
def test_veo3():
    print("\n[1/N] 🎬 Google Veo 3 via Gemini API")
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_KEY)

        model_name = "veo-3.1-fast-generate-preview"  # 最新 + 較快
        print(f"    送出 Veo 3 生成請求（model={model_name}）…")
        operation = client.models.generate_videos(
            model=model_name,
            prompt=FULL_PROMPT,
            config=types.GenerateVideosConfig(
                aspect_ratio="16:9",
                number_of_videos=1,
            )
        )

        print(f"    Operation: {operation.name}")
        print("    輪詢狀態（每 10 秒）…")
        start = time.time()
        while not operation.done:
            time.sleep(10)
            operation = client.operations.get(operation)
            print(f"    經過 {int(time.time()-start)}s、done={operation.done}")
            if time.time() - start > 600:  # 10 分鐘 timeout
                print("    ⚠️ 超時、放棄")
                return None

        # 下載
        gen_videos = operation.response.generated_videos if operation.response else None
        if not gen_videos:
            print(f"    ❌ 無生成結果: {operation}")
            return None

        out_path = OUT_DIR / "veo3-beat1.mp4"
        client.files.download(file=gen_videos[0].video)
        gen_videos[0].video.save(str(out_path))
        print(f"    ✅ 存到 {out_path}（{out_path.stat().st_size/1024:.0f} KB）")
        return str(out_path)

    except Exception as e:
        print(f"    ❌ Veo 3 失敗: {type(e).__name__}: {e}")
        return None


# ─── Provider 2-N: HuggingFace Inference API ─────────────────────
def test_hf(model_id, short_name):
    print(f"\n[HF] 🤗 {short_name} ({model_id})")
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        print(f"    送出 HF 請求…")
        r = requests.post(url, headers=headers, json={"inputs": BEAT_1}, timeout=600)
        print(f"    HTTP {r.status_code}, Content-Type: {r.headers.get('content-type')}")

        if r.status_code != 200:
            try:
                err = r.json()
                print(f"    ❌ 錯誤: {err}")
            except:
                print(f"    ❌ 錯誤: {r.text[:300]}")
            return None

        ct = r.headers.get("content-type", "")
        if "video" in ct or "octet" in ct:
            out = OUT_DIR / f"hf-{short_name}-beat1.mp4"
            out.write_bytes(r.content)
            print(f"    ✅ 存到 {out}（{len(r.content)/1024:.0f} KB）")
            return str(out)
        else:
            # JSON / 圖片 fallback
            print(f"    ⚠️ 非影片回應: {r.text[:300]}")
            return None

    except Exception as e:
        print(f"    ❌ {short_name} 失敗: {type(e).__name__}: {e}")
        return None


# ─── Main ──────────────────────────────────────────────────────
def main():
    print("="*60)
    print("  T2V API 平行測試 - MD Beat 1（龍咆嘯）")
    print("="*60)
    print(f"  輸出資料夾: {OUT_DIR}")
    print(f"  Gemini key: {'✓' if GEMINI_KEY else '✗'}")
    print(f"  HF token  : {'✓' if HF_TOKEN else '✗'}")

    results = {}

    # Veo 3
    if GEMINI_KEY:
        results["veo3"] = test_veo3()

    # HF Inference API 2026 後免費 serverless 對 video 模型基本沒了
    # 略過、focus on Veo

    # 總結
    print("\n" + "="*60)
    print("  總結")
    print("="*60)
    for name, path in results.items():
        status = f"✅ {path}" if path else "❌ 失敗"
        print(f"  {name:25} {status}")
    print(f"\n📁 全部輸出在: {OUT_DIR}")


if __name__ == "__main__":
    main()
