"""
單機模式測試：
  場景1 — 法師A 手動 + 法師B 智能（月影靈雀）+ 木樁烈焰龍 (stub-fire)
  場景2 — 法師A 智能 + 法師B 智能 + 木樁烈焰龍（全自動）(stub-fire)
  場景3 — 法師A 手動 + 法師B 智能 + 機械利爪龍 (mech-claw)
  場景4 — 法師A 手動 + 法師B 智能 + 狡詐暴虐龍 (llm-brutal)
"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "file:///C:/Users/USER/mage-dragon/index.html"
ENV = Path("C:/Users/USER/mage-dragon/.env")

def p(msg=""): print(msg, flush=True)

def groq_key():
    try:
        m = re.search(r"GROQ_API_KEY=(.+)", ENV.read_text())
        return m.group(1).strip() if m else ""
    except:
        return ""

def get_state(page):
    return page.evaluate("""() => ({
        aHp:   document.getElementById('mageA-hp')?.textContent,
        bHp:   document.getElementById('mageB-hp')?.textContent,
        dHp:   document.getElementById('dragon-hp')?.textContent,
        phase: gs?.phase,
        turn:  gs?.turn,
    })""")

def count_msgs(page, css_class):
    return page.evaluate(f"() => document.querySelectorAll('.{css_class}').length")

def last_hint(page):
    return page.evaluate(
        "() => [...document.querySelectorAll('.hint-msg .msg-text')].at(-1)?.textContent ?? ''")

def wait_input_active(page, timeout=20000):
    page.wait_for_function(
        "() => !document.getElementById('input-bar').classList.contains('idle')",
        timeout=timeout)

def wait_round_done(page, timeout=60000):
    """等 dragon-skill 從 ❓/✅ 變成真實 emoji（代表結算完成）"""
    page.wait_for_function(
        "() => { const s = document.getElementById('dragon-skill')?.textContent;"
        "  return s && s !== '❓' && s !== '✅'; }",
        timeout=timeout)

def wait_game_over(page, timeout=180000):
    page.wait_for_function("() => gs?.phase === 'game_over'", timeout=timeout)

def setup_config(page, key, mageA_mode, mageB_mode, mageB_agent, dragon):
    """透過 localStorage 直接注入設定，跳過 UI 點擊"""
    page.evaluate(f"""() => {{
        localStorage.setItem('mage-dragon-ai-config-v2', JSON.stringify({{
            global: {{
                provider: 'groq',
                model: 'llama-3.3-70b-versatile',
                apiKey: '{key}'
            }},
            roles: {{
                mageA:  {{ mode: '{mageA_mode}', strategy: '' }},
                mageB:  {{ mode: '{mageB_mode}', agent: '{mageB_agent}' }},
                dragon: {{ archetype: '{dragon}' }}
            }}
        }}));
    }}""")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(400)

def play_manual_a(page, max_turns=25):
    """法師A 手動出招，最多跑 max_turns 回合"""
    for turn in range(1, max_turns + 1):
        s = get_state(page)
        if s["phase"] == "game_over":
            p(f"  🏁 game_over（第 {s['turn']} 回合）")
            return True

        try:
            wait_input_active(page, timeout=15000)
        except:
            p("  ⚠️  等輸入欄逾時")
            return False

        s = get_state(page)
        p(f"  回合 {s['turn']} | A:{s['aHp']} B:{s['bHp']} 龍:{s['dHp']}")

        # 判斷 A 是否強制施放
        a_forced = page.evaluate("() => { const a=gs?.mageA?.action; return a>=1&&a<=3; }")
        if a_forced:
            p("    A ⏩ 強制施放，等結算…")
        else:
            hint = last_hint(page)
            # 簡單策略：龍吸氣→開盾，HP低→補血，其餘閃電
            if "吸氣" in hint or "第 1 回合" in hint or "第 2 回合" in hint:
                choice = "2"
            elif s["aHp"] and int(''.join(c for c in s["aHp"] if c.isdigit()) or "99") <= 2:
                choice = "3"
            else:
                choice = "1"
            page.fill("#player-input", choice)
            page.click("#player-send")
            p(f"    A 出招 {choice}")

        # 等結算
        try:
            wait_round_done(page, timeout=60000)
            page.wait_for_timeout(600)
        except:
            p("  ⚠️  結算逾時")
            return False

    return False

# ──────────────────────────────────────────────
with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=False, slow_mo=250,
        args=["--start-maximized"])
    page = browser.new_page(no_viewport=True)
    page.on("pageerror", lambda e: p(f"[JS ERROR] {e}"))
    page.goto(URL)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(500)

    key = groq_key()
    p(f"API key: {'✅ 已載入' if key else '❌ 未找到，LLM 測試會 fallback 隨機'}\n")

    # ── 場景 1：手動A + 智能B + 木樁烈焰龍 ──────────
    p("=" * 50)
    p("場景1：手動A + 智能B（月影靈雀）+ 木樁烈焰龍")
    p("=" * 50)
    setup_config(page, key, "manual", "smart", "moon-sparrow", "stub-fire")
    page.click("#player-send")        # 開始遊戲
    page.wait_for_timeout(500)

    result = play_manual_a(page, max_turns=25)

    ally_count = count_msgs(page, "ally-msg")
    p(f"  法師B 說話次數：{ally_count}（> 0 代表 LLM 有回應）")
    page.screenshot(path="C:/Users/USER/mage-dragon/test-s1.png")
    p("  📸 test-s1.png\n")
    page.wait_for_timeout(1500)

    # ── 場景 2：智能A + 智能B + 木樁烈焰龍（全自動）──
    p("=" * 50)
    p("場景2：智能A + 智能B + 木樁烈焰龍（全自動）")
    p("=" * 50)
    setup_config(page, key, "smart", "smart", "ember-monk", "stub-fire")
    page.click("#player-send")        # 開始遊戲
    page.wait_for_timeout(500)

    try:
        wait_game_over(page, timeout=180000)
        s = get_state(page)
        p(f"  ✅ 遊戲結束 | A:{s['aHp']} B:{s['bHp']} 龍:{s['dHp']}")
    except:
        p("  ⚠️  全自動模式逾時（可能卡在 LLM 等待）")

    ally_count = count_msgs(page, "ally-msg")
    player_count = count_msgs(page, "player-msg")
    p(f"  法師A 說話：{player_count}  法師B 說話：{ally_count}")
    page.screenshot(path="C:/Users/USER/mage-dragon/test-s2.png")
    p("  📸 test-s2.png\n")
    page.wait_for_timeout(1500)

    # ── 場景 3：手動A + 智能B + 機械利爪龍 ──────────
    p("=" * 50)
    p("場景3：手動A + 智能B + 機械利爪龍")
    p("=" * 50)
    setup_config(page, key, "manual", "smart", "glass-heron", "mech-claw")
    page.click("#player-send")
    page.wait_for_timeout(500)

    play_manual_a(page, max_turns=20)
    page.screenshot(path="C:/Users/USER/mage-dragon/test-s3.png")
    p("  📸 test-s3.png\n")
    page.wait_for_timeout(1500)

    # ── 場景 4：手動A + 智能B + 狡詐暴虐龍（LLM 龍）──
    if key:
        p("=" * 50)
        p("場景4：手動A + 智能B + 狡詐暴虐龍 llm-brutal")
        p("=" * 50)
        setup_config(page, key, "manual", "smart", "moon-sparrow", "llm-brutal")
        page.click("#player-send")
        page.wait_for_timeout(500)

        play_manual_a(page, max_turns=15)

        dragon_count = count_msgs(page, "dragon-msg")
        p(f"  惡龍說話次數：{dragon_count}（> 0 代表 LLM 龍有回應）")
        page.screenshot(path="C:/Users/USER/mage-dragon/test-s4.png")
        p("  📸 test-s4.png\n")
        page.wait_for_timeout(1500)
    else:
        p("場景4 跳過（無 API key）\n")

    p("=" * 50)
    p("全部測試完成，視窗保留 20 秒…")
    page.wait_for_timeout(20000)
    browser.close()
