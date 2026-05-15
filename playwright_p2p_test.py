import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

URL     = "file:///C:/Users/USER/mage-dragon/index.html"
ENV     = Path("C:/Users/USER/mage-dragon/.env")
SHOT_H  = "C:/Users/USER/mage-dragon/p2p-host.png"
SHOT_G  = "C:/Users/USER/mage-dragon/p2p-guest.png"

def groq_key():
    try:
        m = re.search(r"GROQ_API_KEY=(.+)", ENV.read_text())
        return m.group(1).strip() if m else ""
    except: return ""

def wait_status(page, text, timeout=20000):
    page.wait_for_function(
        f"() => document.getElementById('invite-status')?.textContent?.includes('{text}')",
        timeout=timeout)

def wait_hint(page, keyword, timeout=20000):
    page.wait_for_function(
        f"() => [...document.querySelectorAll('.hint-msg .msg-text')]"
        f".some(el => el.textContent.includes('{keyword}'))",
        timeout=timeout)

def wait_resolve(page, timeout=25000):
    """等龍的技能圖示從 ❓/✅ 變成真實狀態"""
    page.wait_for_function(
        "() => { const s = document.getElementById('dragon-skill')?.textContent;"
        "return s && s !== '❓' && s !== '✅'; }",
        timeout=timeout)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=600,
        args=["--window-size=1000,900", "--window-position=0,0"])

    # 開兩個獨立 context，模擬兩個不同的玩家
    ctx_h = browser.new_context(viewport={"width": 980, "height": 860})
    ctx_g = browser.new_context(viewport={"width": 980, "height": 860})
    host  = ctx_h.new_page()
    guest = ctx_g.new_page()

    host.on("pageerror",  lambda e: print(f"[host error]  {e}"))
    guest.on("pageerror", lambda e: print(f"[guest error] {e}"))

    # ── 兩頁同時載入 ────────────────────────────────
    host.goto(URL)
    guest.goto(URL)
    host.wait_for_load_state("domcontentloaded")
    guest.wait_for_load_state("domcontentloaded")
    print("✅ 兩頁載入完成")

    # ── Host 設定 API key ───────────────────────────
    key = groq_key()
    if key:
        host.click("details:has(summary:text('智能模型'))")
        host.wait_for_timeout(200)
        host.fill("#global-api-key", key)
        host.click("#save-ai-config")
        host.wait_for_timeout(200)
        print(f"✅ Host API key 已設定（{key[:8]}…）")

    # ── Host 產生邀請碼 ──────────────────────────────
    host.click("details:has(summary:text('連線對戰'))")
    host.wait_for_timeout(300)
    host.click("#generate-invite")
    print("⏳ 等待 Host PeerJS 連上信令伺服器…")
    wait_status(host, "等待隊友", timeout=20000)
    code = host.input_value("#invite-code-out")
    print(f"✅ 邀請碼：{code}")

    # ── Guest 加入 ───────────────────────────────────
    guest.click("details:has(summary:text('連線對戰'))")
    guest.wait_for_timeout(300)
    guest.fill("#invite-code-in", code)
    guest.click("#join-game")
    print("⏳ Guest 連線中…")

    # 等兩邊都顯示 ✅
    wait_status(host,  "✅", timeout=20000)
    wait_status(guest, "✅", timeout=20000)
    print("✅ P2P 連線建立！")
    host.wait_for_timeout(500)

    # ── Host 開始遊戲 ────────────────────────────────
    host.click("#player-send")
    host.wait_for_timeout(600)
    print("▶️  遊戲開始")

    # ── 玩 3 回合 ────────────────────────────────────
    for turn in range(1, 4):
        print(f"\n─── 回合 {turn} ───")

        # Host 等輸入欄 active
        host.wait_for_function(
            "() => !document.getElementById('input-bar').classList.contains('idle')",
            timeout=15000)

        # Guest 等收到 turn_start 提示
        wait_hint(guest, f"回合 {turn}", timeout=15000)

        # 讀狀態
        d_skill = host.evaluate("() => document.getElementById('dragon-skill')?.textContent") or ""
        print(f"  龍狀態（❓前）: {d_skill}")

        # 策略：龍在吸氣/噴火 → 雙盾；否則雙閃電
        choice = "2" if ("👃" in d_skill or "🔥" in d_skill) else "1"
        print(f"  Host 選 {choice}，Guest 選 {choice}")

        # Host 出招（如果沒被強制）
        a_forced = host.evaluate(
            "() => { const a=window.gs?.mageA?.action; return a>=1&&a<=3; }")
        if not a_forced:
            host.fill("#player-input", choice)
            host.click("#player-send")

        # Guest 出招（如果還沒送出）
        guest_idle = guest.evaluate(
            "() => document.getElementById('input-bar').classList.contains('idle')")
        if not guest_idle:
            guest.fill("#player-input", choice)
            guest.click("#player-send")
            print("  ✅ Guest 送出招式")

        # 等兩邊結算完成
        wait_resolve(host,  timeout=25000)
        wait_resolve(guest, timeout=25000)
        host.wait_for_timeout(500)

        # 印結算訊息
        last_msg = host.evaluate(
            "() => [...document.querySelectorAll('.system-msg .msg-text')].at(-1)?.textContent ?? ''")
        print(f"  📜 {last_msg}")

        phase = host.evaluate("() => window.gs?.phase") or \
                host.evaluate("() => typeof gs !== 'undefined' ? gs.phase : 'unknown'")

        if "game_over" in str(phase):
            print("\n🏁 遊戲結束")
            break

    # ── 截圖 ─────────────────────────────────────────
    host.screenshot(path=SHOT_H)
    guest.screenshot(path=SHOT_G)
    print(f"\n📸 host  截圖：{SHOT_H}")
    print(f"📸 guest 截圖：{SHOT_G}")

    print("\n⏸  測試結束，視窗保留 8 秒供觀察…")
    host.wait_for_timeout(8000)
    browser.close()
