import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "file:///C:/Users/USER/mage-dragon/dual-view.html"
ENV = Path("C:/Users/USER/mage-dragon/.env")
TOTAL_GAMES = 10

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
        "() => !document.getElementById('input-bar').classList.contains('idle')"
        " && !document.getElementById('player-send').disabled"
        " && window.gs?.phase === 'choosing'",
        timeout=timeout)

def wait_resolve(frame, timeout=40000):
    frame.wait_for_function(
        "() => { const s = document.getElementById('dragon-skill')?.textContent;"
        "return s && s !== '❓' && s !== '✅'; }",
        timeout=timeout)

def get_state(frame):
    return frame.evaluate("""() => ({
        aHp:   document.getElementById('mageA-hp')?.textContent,
        bHp:   document.getElementById('mageB-hp')?.textContent,
        dHp:   document.getElementById('dragon-hp')?.textContent,
        phase: window.gs?.phase,
    })""")

def last_sys(frame):
    return frame.evaluate(
        "() => [...document.querySelectorAll('.system-msg .msg-text')].at(-1)?.textContent ?? ''")

def parse_hp(text):
    try:
        return int(''.join(c for c in (text or '') if c.isdigit()))
    except: return 99

def choose(last_msg, a_hp_text, b_hp_text):
    a_hp = parse_hp(a_hp_text)
    b_hp = parse_hp(b_hp_text)
    if "第 1 回合" in last_msg or "第 2 回合" in last_msg:
        return "2", "🛡️ 護盾"
    if a_hp <= 2 or b_hp <= 2:
        return "3", "💚 補血"
    return "1", "⚡ 閃電"

def guest_submitted(guest):
    """Guest 已出招（送出按鈕被 disable，或 mageB-skill = ✅）"""
    return guest.evaluate(
        "() => document.getElementById('player-send').disabled"
        " || document.getElementById('mageB-skill').textContent === '✅'")

def check_game_over(frame):
    """用按鈕文字偵測 game_over，比讀 gs.phase 更可靠"""
    return frame.evaluate(
        "() => document.getElementById('player-send').textContent.includes('再來')")

def wait_guest_turn(guest, expected_turn, timeout=8000):
    """等 guest 收到 turn_start（gs.turn 追上 host），避免 race condition"""
    try:
        guest.wait_for_function(
            f"() => window.gs?.turn === {expected_turn}",
            timeout=timeout)
    except Exception:
        pass  # bForced/dead 或 game_over 時 gs.turn 可能不會更新，不擋

def setup_p2p(page, key):
    """首次建立 P2P 連線，回傳 (host, guest) frames"""
    page.goto(URL)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(800)

    host  = page.frame(name="host")
    guest = page.frame(name="guest")

    if key:
        host.click("details:has(summary:text('智能模型'))")
        host.wait_for_timeout(200)
        host.fill("#global-api-key", key)
        host.click("#save-ai-config")
        host.wait_for_timeout(200)
        p(f"✅ API key 已設定（{key[:8]}…）")

    host.click("details:has(summary:text('連線對戰'))")
    host.wait_for_timeout(300)
    host.click("#generate-invite")
    p("⏳ 等待 PeerJS 信令伺服器…")
    wait_status(host, "等待隊友", timeout=25000)
    code = host.input_value("#invite-code-out")
    p(f"✅ 邀請碼：{code}")

    guest.click(".tab-btn[data-target='dashboard']")
    guest.wait_for_timeout(200)
    guest.click("details:has(summary:text('連線對戰'))")
    guest.wait_for_timeout(300)
    guest.fill("#invite-code-in", code)
    guest.click("#join-game")
    p("⏳ Guest 連線中…")

    wait_status(host,  "✅", timeout=20000)
    wait_status(guest, "✅", timeout=20000)
    p("✅ P2P 連線建立！")
    host.wait_for_timeout(400)

    guest.click(".tab-btn[data-target='battle']")
    guest.wait_for_timeout(200)

    return host, guest

def run_game(host, guest, game_num):
    """執行單局，回傳 'win' / 'lose' / 'error'"""
    p(f"\n{'='*50}")
    p(f"  第 {game_num} 局")
    p(f"{'='*50}")

    # 點「戰鬥開始 / 再來一局」
    host.click("#player-send")
    host.wait_for_timeout(500)

    for turn in range(1, 31):
        p(f"─── 回合 {turn} ───")

        if check_game_over(host):
            s_end = get_state(host)
            result = "win" if parse_hp(s_end["dHp"]) <= 0 else "lose"
            p(f"🏁 {'🎉 勝利！' if result == 'win' else '💀 落敗'}")
            return result

        try:
            wait_input_active(host, timeout=20000)
        except Exception:
            p("  ⏱ 等輸入欄逾時")
            return "error"

        s = get_state(host)
        p(f"  A:{s['aHp']}  B:{s['bHp']}  龍:{s['dHp']}")

        msg = last_sys(host)
        h_choice, h_reason = choose(msg, s["aHp"], s["bHp"])
        g_choice, g_reason = choose(msg, s["aHp"], s["bHp"])

        # Host 出招
        a_forced = host.evaluate("() => { const a=window.gs?.mageA?.action; return a>=1&&a<=3; }")
        if a_forced:
            p("  Host ⏩")
        else:
            host.fill("#player-input", h_choice)
            host.click("#player-send")
            p(f"  Host → {h_choice} {h_reason}")

        # 等 guest 收到 turn_start（P2P 有延遲，不等會誤判 guest 已出招）
        wait_guest_turn(guest, turn)

        # Guest 出招
        if guest_submitted(guest):
            p("  Guest ⏩")
        else:
            guest.fill("#player-input", g_choice)
            guest.click("#player-send")
            p(f"  Guest → {g_choice} {g_reason}")

        # 等結算
        try:
            wait_resolve(host,  timeout=40000)
            wait_resolve(guest, timeout=40000)
        except Exception:
            p("  ⏱ 結算逾時")
            return "error"

        host.wait_for_timeout(200)
        s2 = get_state(host)
        p(f"  → A:{s2['aHp']} B:{s2['bHp']} 龍:{s2['dHp']}  {last_sys(host)}")

        if check_game_over(host):
            result = "win" if parse_hp(s2["dHp"]) <= 0 else "lose"
            p(f"🏁 {'🎉 勝利！' if result == 'win' else '💀 落敗'}")
            return result

    return "error"

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=False, slow_mo=300,
        args=["--start-maximized"])
    page = browser.new_page(no_viewport=True)
    page.on("pageerror", lambda e: p(f"[error] {e}"))

    key = groq_key()
    host, guest = setup_p2p(page, key)

    stats = {"win": 0, "lose": 0, "error": 0}
    p(f"\n🎮 開始壓力測試，共 {TOTAL_GAMES} 局\n")

    for game_num in range(1, TOTAL_GAMES + 1):
        try:
            result = run_game(host, guest, game_num)
        except Exception as e:
            p(f"  ❌ 例外：{e}")
            result = "error"
        stats[result] += 1
        page.wait_for_timeout(500)

    p(f"\n{'='*50}")
    p(f"  測試完成：{TOTAL_GAMES} 局")
    p(f"  🎉 勝利：{stats['win']}　💀 落敗：{stats['lose']}　❌ 錯誤：{stats['error']}")
    p(f"  勝率：{stats['win'] / TOTAL_GAMES * 100:.0f}%")
    p(f"{'='*50}")

    page.wait_for_timeout(5000)
    browser.close()
