import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from pathlib import Path
from playwright.sync_api import sync_playwright

URL  = "file:///C:/Users/USER/mage-dragon/dual-view.html"
ENV  = Path("C:/Users/USER/mage-dragon/.env")
SHOT = "C:/Users/USER/mage-dragon/full-game.png"

def p(msg=""):
    print(msg, flush=True)

def groq_key():
    try:
        m = re.search(r"GROQ_API_KEY=(.+)", ENV.read_text())
        return m.group(1).strip() if m else ""
    except: return ""

def wait_status(frame, text, timeout=25000):
    frame.wait_for_function(
        f"() => document.getElementById('invite-status')?.textContent?.includes('{text}')",
        timeout=timeout)

def wait_input_active(frame, timeout=20000):
    frame.wait_for_function(
        "() => !document.getElementById('input-bar').classList.contains('idle')",
        timeout=timeout)

def wait_resolve(frame, timeout=40000):
    frame.wait_for_function(
        "() => { const s = document.getElementById('dragon-skill')?.textContent;"
        "return s && s !== '❓' && s !== '✅'; }",
        timeout=timeout)

def get_state(frame):
    return frame.evaluate("""() => ({
        aHp:    document.getElementById('mageA-hp')?.textContent,
        bHp:    document.getElementById('mageB-hp')?.textContent,
        dHp:    document.getElementById('dragon-hp')?.textContent,
        phase:  window.gs?.phase,
    })""")

def last_sys(frame):
    return frame.evaluate(
        "() => [...document.querySelectorAll('.system-msg .msg-text')].at(-1)?.textContent ?? ''")

def parse_hp(text):
    try:
        return int(''.join(c for c in (text or '') if c.isdigit()))
    except:
        return 99

def choose(last_msg, a_hp_text, b_hp_text):
    a_hp = parse_hp(a_hp_text)
    b_hp = parse_hp(b_hp_text)
    if "第 1 回合" in last_msg:
        return "2", "🛡️ 護盾（龍吸氣第1回合，預備擋火）"
    if a_hp <= 2 or b_hp <= 2:
        return "3", "💚 補血（HP 危險）"
    return "1", "⚡ 閃電（雙人同步）"

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=False, slow_mo=400,
        args=["--start-maximized"])
    page = browser.new_page(no_viewport=True)

    page.on("pageerror", lambda e: p(f"[error] {e}"))
    page.goto(URL)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(800)
    p("✅ 頁面載入完成")

    host  = page.frame(name="host")
    guest = page.frame(name="guest")

    # Host 設定 API key
    key = groq_key()
    if key:
        host.click("details:has(summary:text('智能模型'))")
        host.wait_for_timeout(200)
        host.fill("#global-api-key", key)
        host.click("#save-ai-config")
        host.wait_for_timeout(200)
        p(f"✅ API key 已設定（{key[:8]}…）")

    # Host 產生邀請碼
    host.click("details:has(summary:text('連線對戰'))")
    host.wait_for_timeout(300)
    host.click("#generate-invite")
    p("⏳ 等待 PeerJS 信令伺服器…")
    wait_status(host, "等待隊友", timeout=25000)
    code = host.input_value("#invite-code-out")
    p(f"✅ 邀請碼：{code}")

    # Guest 切到儀表 tab → 加入連線
    guest.click(".tab-btn[data-target='dashboard']")
    guest.wait_for_timeout(200)
    guest.click("details:has(summary:text('連線對戰'))")
    guest.wait_for_timeout(300)
    guest.fill("#invite-code-in", code)
    guest.click("#join-game")
    p("⏳ Guest 連線中…")

    wait_status(host,  "✅", timeout=20000)
    wait_status(guest, "✅", timeout=20000)
    p("✅ P2P 連線建立！\n")
    host.wait_for_timeout(500)

    # Guest 切到對戰 tab
    guest.click(".tab-btn[data-target='battle']")
    guest.wait_for_timeout(200)

    # 開始遊戲
    host.click("#player-send")
    host.wait_for_timeout(600)
    p("▶️  遊戲開始！\n")

    for turn in range(1, 31):
        p(f"─── 回合 {turn} ───")

        if get_state(host)["phase"] == "game_over":
            p("🏁 已 game_over，停止")
            break

        try:
            wait_input_active(host, timeout=20000)
        except Exception:
            p("  ⏱ 等輸入欄逾時，跳出")
            break

        s = get_state(host)
        p(f"  A:{s['aHp']}  B:{s['bHp']}  龍:{s['dHp']}")

        msg = last_sys(host)
        h_choice, h_reason = choose(msg, s["aHp"], s["bHp"])
        g_choice, g_reason = choose(msg, s["aHp"], s["bHp"])

        # Host 出招
        a_forced = host.evaluate("() => { const a=window.gs?.mageA?.action; return a>=1&&a<=3; }")
        if a_forced:
            p(f"  Host ⏩ 強制施放")
        else:
            host.fill("#player-input", h_choice)
            host.click("#player-send")
            p(f"  Host 送出 {h_choice}（{h_reason}）")

        # Guest 出招
        guest_idle = guest.evaluate(
            "() => document.getElementById('input-bar').classList.contains('idle')")
        if guest_idle:
            p(f"  Guest ⏩ 強制施放")
        else:
            guest.fill("#player-input", g_choice)
            guest.click("#player-send")
            p(f"  Guest 送出 {g_choice}（{g_reason}）")

        # 等結算
        try:
            wait_resolve(host,  timeout=40000)
            wait_resolve(guest, timeout=40000)
        except Exception:
            p("  ⏱ 結算逾時，跳出")
            break

        host.wait_for_timeout(400)
        s2 = get_state(host)
        p(f"  結算 → A:{s2['aHp']} B:{s2['bHp']} 龍:{s2['dHp']}")
        p(f"  📜 {last_sys(host)}")
        p("")

        if s2["phase"] == "game_over":
            p("🏁 遊戲結束！")
            break

    page.screenshot(path=SHOT)
    p(f"📸 截圖 → {SHOT}")
    p("\n⏸  視窗保留 15 秒…")
    page.wait_for_timeout(15000)
    browser.close()
