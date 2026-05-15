import re, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright

ENV_PATH = Path("C:/Users/USER/mage-dragon/.env")
HTML_URL = "file:///C:/Users/USER/mage-dragon/index.html"
SCREENSHOT = "C:/Users/USER/mage-dragon/playwright-result.png"

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
        phase:  window.gs?.phase,
    })""")

def last_system_msg(page):
    return page.evaluate("""() =>
        [...document.querySelectorAll('.system-msg .msg-text')].at(-1)?.textContent ?? ''""")

def all_messages(page):
    return page.evaluate("""() =>
        [...document.querySelectorAll('.message-card .msg')].map(m => {
            const av  = m.querySelector('.msg-avatar')?.textContent.trim() ?? '';
            const txt = m.querySelector('.msg-text')?.textContent.trim() ?? '';
            return av + ' ' + txt;
        })""")

def is_mageA_forced(page):
    return page.evaluate("""() => {
        const a = window.gs?.mageA?.action;
        return a >= 1 && a <= 3;
    }""")

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page(viewport={"width": 1280, "height": 800})

    # 印 LLM console 訊息
    def on_console(msg):
        if "[MageB LLM]" in msg.text:
            print(f"\033[36m[browser]\033[0m {msg.text}")
    page.on("console", on_console)
    page.on("pageerror", lambda e: print(f"\033[31m[page error]\033[0m {e}"))

    page.goto(HTML_URL)
    page.wait_for_load_state("domcontentloaded")
    print("✅ 頁面載入完成")

    # ── 設定 AI ──────────────────────────────────
    groq_key = read_groq_key()
    page.click("details:has(summary:text('智能模型'))")
    page.wait_for_timeout(300)

    if groq_key:
        page.select_option("#global-provider", "groq")
        page.fill("#global-model", "llama-3.3-70b-versatile")
        page.fill("#global-api-key", groq_key)
        page.click("#save-ai-config")
        print(f"✅ Groq API key 已設定（{groq_key[:8]}…）")
    else:
        print("⚠️  找不到 GROQ_API_KEY，法師B 將 fallback 隨機")

    page.click("details:has(summary:text('角色設定'))")
    page.wait_for_timeout(300)
    page.select_option("#mageB-mode", "smart")
    page.select_option("#mageB-agent", "moon-sparrow")
    print("✅ 法師B → 智能 / 月影靈雀")

    dragon_type = page.eval_on_selector(
        "#dragon-archetype", "el => el.options[el.selectedIndex].text")
    print(f"🐉 惡龍型態：{dragon_type}")

    # ── 開始遊戲 ─────────────────────────────────
    page.click("#player-send")
    page.wait_for_timeout(600)
    print("\n▶️  遊戲開始！")

    # ── 主迴圈：最多玩 8 回合 ─────────────────────
    for turn in range(1, 9):
        print(f"\n─── 回合 {turn} ───")

        # 如果已經 game_over 就不用再等
        if page.evaluate("() => window.gs?.phase") == "game_over":
            print("  🏁 遊戲已結束，停止迴圈")
            break

        # 等輸入欄 active
        page.wait_for_function(
            "() => !document.getElementById('input-bar').classList.contains('idle')",
            timeout=20000
        )

        s = get_state(page)
        print(f"  法師A: {s['aHp']} {s['aSkill']}  法師B: {s['bHp']}  惡龍: {s['dHp']} {s['dSkill']}")

        # 策略：龍吸氣/噴火 → 開盾；否則奇數回合閃電、偶數無
        d_skill = s["dSkill"] or ""
        if "👃" in d_skill or "🔥" in d_skill:
            choice = "2"
            print("  🛡️ 龍蓄力，選護盾")
        elif turn % 2 == 1:
            choice = "1"
            print("  ⚡ 選閃電")
        else:
            choice = "0"
            print("  ⭕ 選無動作")

        # 法師A 強制施放中則不需輸入
        if is_mageA_forced(page):
            print("  ⏩ 法師A 強制施放，跳過輸入")
        else:
            page.fill("#player-input", choice)
            page.click("#player-send")
            print(f"  ✅ 法師A 送出 {choice}")

        # 等結算（dragon-skill 從 ❓/✅ 變成真實狀態）
        page.wait_for_function(
            "() => { const s = document.getElementById('dragon-skill')?.textContent; "
            "return s && s !== '❓' && s !== '✅'; }",
            timeout=25000
        )

        s2 = get_state(page)
        print(f"  結算後 → A:{s2['aHp']} B:{s2['bHp']} 龍:{s2['dHp']}")
        print(f"  📜 {last_system_msg(page)}")

        if s2["phase"] == "game_over":
            print("\n🏁 遊戲結束")
            break

        page.wait_for_timeout(600)

    # ── 截圖 ──────────────────────────────────────
    page.screenshot(path=SCREENSHOT)
    print(f"\n📸 截圖：{SCREENSHOT}")

    # ── 完整訊息紀錄 ──────────────────────────────
    print("\n📋 完整訊息紀錄：")
    for m in all_messages(page):
        print(f"  {m}")

    page.wait_for_timeout(2000)
    browser.close()
