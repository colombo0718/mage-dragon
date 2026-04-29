"""
Solo 全自動壓力測試（smart A + smart B）
  - 木樁 × 3：每隻 GAMES_STUB 局
  - 機械 × 3：每隻 GAMES_MECH 局
  - 狡詐 × 3：每隻 GAMES_LLM 局（需 API key，否則跳過）

結果：每個 archetype 的勝/負/錯誤統計。
"""
import sys, io, re, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from pathlib import Path
from playwright.sync_api import sync_playwright

URL  = "file:///C:/Users/USER/mage-dragon/index.html"
ENV  = Path("C:/Users/USER/mage-dragon/.env")

GAMES_STUB = 5   # 木樁每隻跑幾局
GAMES_MECH = 5   # 機械每隻跑幾局
GAMES_LLM  = 3   # 狡詐每隻跑幾局

# mageA 用 Python 腳本策略（手動模式），避免每回合雙 LLM 打爆 rate limit
# mageB 用 smart（驗 LLM 智能）

STUBS = ['stub-fire', 'stub-claw', 'stub-brutal']
MECHS = ['mech-fire', 'mech-claw', 'mech-brutal']
LLMS  = ['llm-fire',  'llm-claw',  'llm-brutal']

NAMES = {
    'stub-fire':  '木樁烈焰龍', 'stub-claw':  '木樁利爪龍', 'stub-brutal': '木樁暴虐龍',
    'mech-fire':  '機械烈焰龍', 'mech-claw':  '機械利爪龍', 'mech-brutal': '機械暴虐龍',
    'llm-fire':   '狡詐烈焰龍', 'llm-claw':   '狡詐利爪龍', 'llm-brutal':  '狡詐暴虐龍',
}

def p(msg=""): print(msg, flush=True)

def groq_key():
    try:
        m = re.search(r"GROQ_API_KEY=(.+)", ENV.read_text())
        return m.group(1).strip() if m else ""
    except: return ""

def get_state(page):
    return page.evaluate("""() => ({
        aHp:   document.getElementById('mageA-hp')?.textContent,
        bHp:   document.getElementById('mageB-hp')?.textContent,
        dHp:   document.getElementById('dragon-hp')?.textContent,
        phase: gs?.phase,
        turn:  gs?.turn,
    })""")

def parse_hp(text):
    try: return int(''.join(c for c in (text or '') if c.isdigit()))
    except: return 99

def last_sys(page):
    return page.evaluate(
        "() => [...document.querySelectorAll('.system-msg .msg-text')].at(-1)?.textContent ?? ''")

def wait_input_active(page, timeout=20000):
    page.wait_for_function(
        "() => !document.getElementById('input-bar').classList.contains('idle')",
        timeout=timeout)

def wait_round_done(page, timeout=60000):
    page.wait_for_function(
        "() => { const s = document.getElementById('dragon-skill')?.textContent;"
        "  return s && s !== '❓' && s !== '✅'; }",
        timeout=timeout)

def choose_action(page):
    """mageA 腳本策略：龍吸氣→盾，血量低→補血，其餘閃電"""
    s = get_state(page)
    msg = last_sys(page)
    a_hp = parse_hp(s['aHp'])
    b_hp = parse_hp(s['bHp'])
    if "吸氣" in msg or "第 1 回合" in msg or "第 2 回合" in msg:
        return "2"
    if a_hp <= 2 or b_hp <= 2:
        return "3"
    return "1"

def setup_config(page, api_key, dragon):
    # mageA = manual（Python 腳本策略），mageB = smart（單 LLM/turn，不打爆 rate limit）
    if URL not in (page.url or ''):
        page.goto(URL)
        page.wait_for_load_state("domcontentloaded")
    page.evaluate(f"""() => {{
        localStorage.setItem('mage-dragon-ai-config-v2', JSON.stringify({{
            global: {{
                provider: 'groq',
                model: 'llama-3.3-70b-versatile',
                apiKey: '{api_key}'
            }},
            roles: {{
                mageA:  {{ mode: 'manual', strategy: '' }},
                mageB:  {{ mode: 'smart', agent: 'moon-sparrow' }},
                dragon: {{ archetype: '{dragon}' }}
            }}
        }}));
    }}""")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(400)

def run_game(page, arc_key, game_num, max_turns=30):
    """mageA 手動腳本 + mageB smart，回傳 ('win'|'lose'|'error', 回合數, 耗時s)"""
    t0 = time.time()
    page.click("#player-send")
    page.wait_for_timeout(400)

    for turn in range(1, max_turns + 1):
        s = get_state(page)
        if s['phase'] == 'game_over':
            elapsed = round(time.time() - t0, 1)
            result = 'win' if parse_hp(s['dHp']) <= 0 else 'lose'
            return result, s['turn'], elapsed

        try:
            wait_input_active(page, timeout=15000)
        except Exception:
            elapsed = round(time.time() - t0, 1)
            s = get_state(page)
            p(f"    ⚠️  等輸入逾時 turn={s['turn']} phase={s['phase']}")
            return 'error', turn, elapsed

        # 判斷 A 是否已強制施放（不需送輸入）
        a_forced = page.evaluate("() => { const a=gs?.mageA?.action; return a>=1&&a<=3; }")
        if not a_forced:
            choice = choose_action(page)
            page.fill("#player-input", choice)
            page.click("#player-send")

        try:
            wait_round_done(page, timeout=60000)
            page.wait_for_timeout(400)
        except Exception:
            elapsed = round(time.time() - t0, 1)
            p(f"    ⚠️  結算逾時 turn={turn}")
            return 'error', turn, elapsed

        s = get_state(page)
        if s['phase'] == 'game_over':
            elapsed = round(time.time() - t0, 1)
            result = 'win' if parse_hp(s['dHp']) <= 0 else 'lose'
            return result, s['turn'], elapsed

    # 超過回合上限視為超時落敗
    return 'lose', max_turns, round(time.time() - t0, 1)

# ─────────────────────────────────────────────────────
with sync_playwright() as pw:
    key = groq_key()
    p(f"API key: {'✅ 已載入' if key else '❌ 未找到，LLM 龍測試將跳過'}\n")

    # stub/mech 不需要 API key 也能跑；LLM 龍需要 key
    archetypes_to_test = []
    for a in STUBS: archetypes_to_test.append((a, GAMES_STUB))
    for a in MECHS: archetypes_to_test.append((a, GAMES_MECH))
    if key:
        for a in LLMS: archetypes_to_test.append((a, GAMES_LLM))
    else:
        p("⚠️  狡詐系列（LLM 龍）跳過，需要 GROQ_API_KEY\n")

    total_games = sum(n for _, n in archetypes_to_test)
    p(f"📋 測試計劃：{len(archetypes_to_test)} 種龍型態，共 {total_games} 局\n")

    browser = pw.chromium.launch(
        headless=False, slow_mo=300,
        args=["--start-maximized"])
    page = browser.new_page(no_viewport=True)
    page.on("pageerror", lambda e: p(f"[JS ERROR] {e}"))

    all_stats = {}

    for arc_key, n_games in archetypes_to_test:
        name = NAMES[arc_key]
        is_llm = arc_key.startswith('llm')
        p("=" * 55)
        p(f"【{name}】（{arc_key}）× {n_games} 局")
        p("=" * 55)

        setup_config(page, key, arc_key)

        stats = {'win': 0, 'lose': 0, 'error': 0}

        for i in range(1, n_games + 1):
            result, turns, elapsed = run_game(page, arc_key, i)
            stats[result] += 1
            icon = '🎉' if result == 'win' else ('💀' if result == 'lose' else '❌')
            p(f"  局 {i:>2}/{n_games}  {icon} {result:<5}  {turns} 回合  {elapsed}s")
            page.wait_for_timeout(800)

        win_rate = stats['win'] / n_games * 100
        p(f"  ─ 小計：勝 {stats['win']} 負 {stats['lose']} 錯 {stats['error']}  勝率 {win_rate:.0f}%\n")
        all_stats[arc_key] = stats

    # ── 總結 ──────────────────────────────────────────
    p("\n" + "=" * 55)
    p("📊 全部測試結果")
    p("=" * 55)
    grand_win = grand_lose = grand_err = 0
    for arc_key, stats in all_stats.items():
        n = sum(stats.values())
        win_rate = stats['win'] / n * 100 if n else 0
        p(f"  {NAMES[arc_key]:<10}  勝{stats['win']} 負{stats['lose']} 錯{stats['error']}  勝率{win_rate:.0f}%")
        grand_win  += stats['win']
        grand_lose += stats['lose']
        grand_err  += stats['error']

    grand_total = grand_win + grand_lose + grand_err
    p(f"\n  合計 {grand_total} 局  勝{grand_win} 負{grand_lose} 錯{grand_err}  "
      f"勝率{grand_win/grand_total*100:.0f}%")
    p("=" * 55)

    try:
        page.screenshot(path="C:/Users/USER/mage-dragon/screenshots/stress-solo-result.png")
        p("\n📸 stress-solo-result.png")
    except Exception:
        pass
    browser.close()
