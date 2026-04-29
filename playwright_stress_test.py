"""
P2P 壓力測試：
  雙 iframe（Host 法師A 手動腳本 + Guest 法師B 智能），多種龍型態輪測。

  測試計劃（DRAGON_PLAN）：
    stub-fire   × GAMES_PER_DRAGON 局   （木樁：最快，驗基礎穩定）
    mech-brutal × GAMES_PER_DRAGON 局   （機械：隨機元素，驗穩健）
    llm-brutal  × LLM_GAMES 局          （LLM 龍：需 API key）
"""
import sys, io, re, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from pathlib import Path
from playwright.sync_api import sync_playwright

URL  = "file:///C:/Users/USER/mage-dragon/dual-view.html"
ENV  = Path("C:/Users/USER/mage-dragon/.env")

GAMES_PER_DRAGON = 3   # 每種非 LLM 龍跑幾局
LLM_GAMES        = 0   # LLM 龍暫跳過

DRAGON_PLAN = [
    ('stub-fire',   '木樁烈焰龍', False),
    ('mech-brutal', '機械暴虐龍', False),
    ('llm-brutal',  '狡詐暴虐龍', True),
]

def p(msg=""): print(msg, flush=True)

def groq_key():
    try:
        m = re.search(r"GROQ_API_KEY=(.+)", ENV.read_text())
        return m.group(1).strip() if m else ""
    except: return ""

def wait_status(frame, text, timeout=25000):
    frame.wait_for_function(
        f"() => document.getElementById('invite-status')?.textContent?.includes('{text}')",
        timeout=timeout)

def wait_p2p_open(frame, timeout=15000):
    frame.wait_for_function(
        "() => window.p2pConn?.open === true", timeout=timeout)

def wait_input_active(frame, timeout=20000):
    frame.wait_for_function(
        "() => !document.getElementById('input-bar').classList.contains('idle')"
        " && !document.getElementById('player-send').disabled"
        " && gs?.phase === 'choosing'",
        timeout=timeout)

def wait_resolve(frame, current_turn, timeout=40000):
    frame.wait_for_function(
        f"() => (window.gs?.turn ?? 0) > {current_turn} || window.gs?.phase === 'game_over'",
        timeout=timeout)

def get_state(frame):
    return frame.evaluate("""() => ({
        aHp:   document.getElementById('mageA-hp')?.textContent,
        bHp:   document.getElementById('mageB-hp')?.textContent,
        dHp:   document.getElementById('dragon-hp')?.textContent,
        phase: gs?.phase,
        turn:  gs?.turn,
    })""")

def last_sys(frame):
    return frame.evaluate(
        "() => [...document.querySelectorAll('.system-msg .msg-text')].at(-1)?.textContent ?? ''")

def parse_hp(text):
    try: return int(''.join(c for c in (text or '') if c.isdigit()))
    except: return 99

def choose(last_msg, a_hp_text, b_hp_text):
    a_hp = parse_hp(a_hp_text)
    b_hp = parse_hp(b_hp_text)
    if "第 1 回合" in last_msg or "第 2 回合" in last_msg:
        return "2", "🛡️"
    if a_hp <= 2 or b_hp <= 2:
        return "3", "💚"
    return "1", "⚡"

def guest_submitted(guest):
    return guest.evaluate(
        "() => document.getElementById('player-send').disabled"
        " || document.getElementById('mageB-skill').textContent === '✅'")

def check_game_over(frame):
    return frame.evaluate(
        "() => document.getElementById('player-send').textContent.includes('再來')")

def wait_guest_turn(guest, expected_turn, timeout=8000):
    try:
        guest.wait_for_function(
            f"() => window.gs?.turn === {expected_turn}", timeout=timeout)
    except Exception: pass

def inject_dragon_config(frame, dragon_key, api_key):
    """透過 localStorage 注入龍型態設定，不重載頁面（P2P 連線已建立）"""
    frame.evaluate(f"""() => {{
        const raw = localStorage.getItem('mage-dragon-ai-config-v2');
        const cfg = raw ? JSON.parse(raw) : {{}};
        if (!cfg.roles) cfg.roles = {{}};
        if (!cfg.global) cfg.global = {{}};
        cfg.global.provider = 'groq';
        cfg.global.model    = 'llama-3.3-70b-versatile';
        cfg.global.apiKey   = '{api_key}';
        cfg.roles.dragon    = {{ archetype: '{dragon_key}' }};
        cfg.roles.mageB     = {{ mode: 'smart', agent: 'moon-sparrow' }};
        localStorage.setItem('mage-dragon-ai-config-v2', JSON.stringify(cfg));
        if (typeof applyAiConfig === 'function') applyAiConfig(cfg);
    }}""")

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
    # 確認 data channel 真正 open（status "✅" 是 conn.on('open') 觸發，但 open 可能隨即掉）
    wait_p2p_open(host, timeout=8000)
    p("✅ P2P 連線建立！")
    host.wait_for_timeout(400)

    guest.click(".tab-btn[data-target='battle']")
    guest.wait_for_timeout(200)

    return host, guest

def run_game(host, guest, game_num):
    """執行單局，回傳 ('win'|'lose'|'error', 回合數, 耗時s)"""
    t0 = time.time()
    host.click("#player-send")
    host.wait_for_timeout(500)

    for turn in range(1, 31):
        if check_game_over(host):
            s = get_state(host)
            elapsed = round(time.time() - t0, 1)
            result = 'win' if parse_hp(s['dHp']) <= 0 else 'lose'
            return result, s['turn'], elapsed

        try:
            wait_input_active(host, timeout=20000)
        except Exception:
            diag = host.evaluate("""() => ({
                phase: gs?.phase, turn: gs?.turn,
                btnText: document.getElementById('player-send').textContent
            })""")
            p(f"    ⏱ 等輸入逾時 {diag}")
            host.screenshot(path="C:/Users/USER/mage-dragon/p2p-stress-timeout.png")
            return 'error', turn, round(time.time() - t0, 1)

        s = get_state(host)
        msg = last_sys(host)
        h_choice, h_icon = choose(msg, s["aHp"], s["bHp"])
        g_choice, g_icon = choose(msg, s["aHp"], s["bHp"])

        a_forced = host.evaluate("() => { const a=gs?.mageA?.action; return a>=1&&a<=3; }")
        if not a_forced:
            host.fill("#player-input", h_choice)
            host.click("#player-send")

        wait_guest_turn(guest, turn)

        if not guest_submitted(guest):
            guest.fill("#player-input", g_choice)
            guest.click("#player-send")

        try:
            wait_resolve(host,  turn, timeout=40000)
            wait_resolve(guest, turn, timeout=40000)
        except Exception:
            p(f"    ⏱ 結算逾時（回合 {turn}）")
            return 'error', turn, round(time.time() - t0, 1)

        host.wait_for_timeout(150)
        s2 = get_state(host)

        if check_game_over(host):
            elapsed = round(time.time() - t0, 1)
            result = 'win' if parse_hp(s2['dHp']) <= 0 else 'lose'
            p(f"  T{turn:>2} A:{s2['aHp']} B:{s2['bHp']} 龍:{s2['dHp']}  {'🎉' if result=='win' else '💀'}")
            return result, s2['turn'], elapsed
        p(f"  T{turn:>2} A:{s2['aHp']} B:{s2['bHp']} 龍:{s2['dHp']}")

    return 'error', 30, round(time.time() - t0, 1)

# ─────────────────────────────────────────────────────
with sync_playwright() as pw:
    key = groq_key()
    p(f"API key: {'✅ 已載入' if key else '❌ 未找到'}\n")

    browser = pw.chromium.launch(
        headless=False, slow_mo=200,
        args=["--start-maximized"])
    page = browser.new_page(no_viewport=True)
    page.on("pageerror", lambda e: p(f"[JS ERROR] {e}"))

    host, guest = setup_p2p(page, key)

    h_role = host.evaluate("() => p2pRole")
    g_role = guest.evaluate("() => p2pRole")
    p(f"  roles: host={h_role} guest={g_role}\n")

    all_stats = {}

    for dragon_key, dragon_name, needs_key in DRAGON_PLAN:
        if needs_key and not key:
            p(f"⏭ 跳過 {dragon_name}（無 API key）\n")
            continue

        n_games = LLM_GAMES if needs_key else GAMES_PER_DRAGON

        p("=" * 55)
        p(f"【{dragon_name}】（{dragon_key}）× {n_games} 局")
        p("=" * 55)

        inject_dragon_config(host, dragon_key, key)
        host.wait_for_timeout(300)

        stats = {'win': 0, 'lose': 0, 'error': 0}

        for game_num in range(1, n_games + 1):
            p(f"\n  ─── 局 {game_num}/{n_games} ───")
            # 每局前確認 P2P 連線，斷了就重連
            if not host.evaluate("() => window.p2pConn?.open === true"):
                p("  ⚠️ P2P 斷線，重新連線中…")
                host, guest = setup_p2p(page, key)
                inject_dragon_config(host, dragon_key, key)
                host.wait_for_timeout(300)
            try:
                result, turns, elapsed = run_game(host, guest, game_num)
            except Exception as e:
                p(f"  ❌ 例外：{e}")
                result, turns, elapsed = 'error', 0, 0
            stats[result] += 1
            icon = '🎉' if result == 'win' else ('💀' if result == 'lose' else '❌')
            p(f"  {icon} {result}  {turns} 回合  {elapsed}s")
            page.wait_for_timeout(600)

        win_rate = stats['win'] / n_games * 100 if n_games else 0
        p(f"\n  小計：勝{stats['win']} 負{stats['lose']} 錯{stats['error']}  勝率{win_rate:.0f}%\n")
        all_stats[dragon_key] = (dragon_name, stats, n_games)

    # ── 總結 ──────────────────────────────────────────
    p("=" * 55)
    p("📊 P2P 壓力測試結果")
    p("=" * 55)
    grand = {'win': 0, 'lose': 0, 'error': 0}
    for dk, (dn, stats, n) in all_stats.items():
        wr = stats['win'] / n * 100
        p(f"  {dn:<10}  勝{stats['win']} 負{stats['lose']} 錯{stats['error']}  勝率{wr:.0f}%")
        for k in grand: grand[k] += stats[k]

    total = sum(grand.values())
    p(f"\n  合計 {total} 局  勝{grand['win']} 負{grand['lose']} 錯{grand['error']}  "
      f"勝率{grand['win']/total*100:.0f}%")
    p("=" * 55)

    try:
        page.screenshot(path="C:/Users/USER/mage-dragon/screenshots/stress-p2p-result.png")
        p("\n📸 stress-p2p-result.png")
    except Exception:
        pass
    browser.close()
