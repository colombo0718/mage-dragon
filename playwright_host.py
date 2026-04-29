import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

ENV_PATH   = Path("C:/Users/USER/mage-dragon/.env")
HTML_URL   = "file:///C:/Users/USER/mage-dragon/index.html"
CODE_FILE  = Path("C:/Users/USER/mage-dragon/invite-code.txt")

def p(msg=""):
    print(msg, flush=True)

def read_groq_key():
    try:
        text = ENV_PATH.read_text(encoding="utf-8")
        m = re.search(r"GROQ_API_KEY=(.+)", text)
        return m.group(1).strip() if m else ""
    except Exception:
        return ""

def get_state(page):
    return page.evaluate("""() => ({
        aHp:    document.getElementById('mageA-hp')?.textContent,
        bHp:    document.getElementById('mageB-hp')?.textContent,
        dHp:    document.getElementById('dragon-hp')?.textContent,
        aSkill: document.getElementById('mageA-skill')?.textContent,
        bSkill: document.getElementById('mageB-skill')?.textContent,
        dSkill: document.getElementById('dragon-skill')?.textContent,
        phase:  gs?.phase,
    })""")

def last_system_msg(page):
    return page.evaluate("""() =>
        [...document.querySelectorAll('.system-msg .msg-text')].at(-1)?.textContent ?? ''""")

def is_mageA_forced(page):
    return page.evaluate("""() => {
        const a = gs?.mageA?.action;
        return a >= 1 && a <= 3;
    }""")

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=False, slow_mo=500,
        args=["--window-size=1100,900", "--window-position=50,50"])
    page = browser.new_page(viewport={"width": 1080, "height": 860})

    page.on("console", lambda m: print(f"  [browser] {m.text}") if "[MageB LLM]" in m.text or "[P2P" in m.text else None)
    page.on("pageerror", lambda e: print(f"  [page error] {e}"))

    page.goto(HTML_URL)
    page.wait_for_load_state("domcontentloaded")
    p("✅ 頁面載入完成")

    # ── 設定 Groq API key ──────────────────────────
    groq_key = read_groq_key()
    if groq_key:
        page.click("details:has(summary:text('智能模型'))")
        page.wait_for_timeout(300)
        page.select_option("#global-provider", "groq")
        page.fill("#global-model", "llama-3.3-70b-versatile")
        page.fill("#global-api-key", groq_key)
        page.click("#save-ai-config")
        page.wait_for_timeout(200)
        p(f"✅ Groq API key 已設定（{groq_key[:8]}…）")
    else:
        p("⚠️  找不到 GROQ_API_KEY，法師B fallback 隨機")

    # ── 選角色設定 ─────────────────────────────────
    page.click("details:has(summary:text('角色設定'))")
    page.wait_for_timeout(200)
    page.select_option("#mageB-mode", "network")   # 法師B = 連線模式（等 Codex）
    page.wait_for_timeout(200)
    p("✅ 法師B 設定為連線模式（等待 Codex 加入）")

    # ── 展開連線對戰，產生邀請碼 ────────────────────
    page.click("details:has(summary:text('連線對戰'))")
    page.wait_for_timeout(400)
    page.click("#generate-invite")
    p("⏳ 等待 PeerJS 連上信令伺服器…")

    page.wait_for_function(
        "() => document.getElementById('invite-status')?.textContent?.includes('等待')",
        timeout=25000)

    code = page.input_value("#invite-code-out")
    CODE_FILE.write_text(code, encoding='utf-8')
    p("")
    p("=" * 50)
    p(f"  邀請碼：  {code}")
    p("  把這個邀請碼貼給 Codex！")
    p("=" * 50)
    p("")

    # ── 等 Codex（Guest）連線 ────────────────────────
    p("⏳ 等待 Codex 加入連線…")
    page.wait_for_function(
        "() => document.getElementById('invite-status')?.textContent?.includes('✅')",
        timeout=600000)   # 給 10 分鐘讓你把碼貼過去
    p("✅ Codex 已連線！")
    page.wait_for_timeout(800)

    # ── 開始遊戲 ─────────────────────────────────────
    page.click("#player-send")
    page.wait_for_timeout(600)
    p("▶️  遊戲開始！\n")

    # ── 主迴圈：最多 20 回合 ─────────────────────────
    for turn in range(1, 21):
        p(f"─── 回合 {turn} ───")

        if page.evaluate("() => gs?.phase") == "game_over":
            p("🏁 遊戲已結束")
            break

        # 等輸入欄 active（法師A 可以輸入）
        try:
            page.wait_for_function(
                "() => !document.getElementById('input-bar').classList.contains('idle')",
                timeout=30000)
        except Exception:
            p("  ⏱ 等待輸入逾時，跳出")
            break

        s = get_state(page)
        p(f"  A:{s['aHp']} {s['aSkill']}  B:{s['bHp']} {s['bSkill']}  龍:{s['dHp']} {s['dSkill']}")

        # 策略：龍吸氣/蓄火 → 護盾；否則奇數回合閃電
        d_skill = s["dSkill"] or ""
        if "👃" in d_skill or "🔥" in d_skill:
            choice = "2"
            reason = "🛡️ 龍蓄力，選護盾"
        elif turn % 2 == 1:
            choice = "1"
            reason = "⚡ 選閃電"
        else:
            choice = "0"
            reason = "⭕ 無動作"

        p(f"  {reason}")

        if is_mageA_forced(page):
            p("  ⏩ 強制施放中，跳過輸入")
        else:
            page.fill("#player-input", choice)
            page.click("#player-send")
            p(f"  ✅ 法師A 送出 {choice}")

        # 等結算（dragon-skill 從 ❓/✅ 變成真實狀態）
        try:
            page.wait_for_function(
                "() => { const s = document.getElementById('dragon-skill')?.textContent;"
                "return s && s !== '❓' && s !== '✅'; }",
                timeout=90000)
        except Exception:
            p("  ⏱ 等待結算逾時，跳出")
            break

        s2 = get_state(page)
        p(f"  結算後 → A:{s2['aHp']} B:{s2['bHp']} 龍:{s2['dHp']}")
        p(f"  📜 {last_system_msg(page)}")

        if s2["phase"] == "game_over":
            p("\n🏁 遊戲結束！")
            break

        page.wait_for_timeout(600)
        p()

    p("\n⏸  保留視窗供觀察，按 Ctrl+C 結束…")
    try:
        while True:
            page.wait_for_timeout(5000)
    except KeyboardInterrupt:
        pass

    browser.close()
