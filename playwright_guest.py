import argparse
import io
import os
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

HTML_URL = "file:///C:/Users/USER/mage-dragon/index.html"
DEFAULT_SCREENSHOT = Path("C:/Users/USER/mage-dragon/playwright-guest-result.png")
PORTRAIT_WINDOW_WIDTH = 620
PORTRAIT_WINDOW_HEIGHT = 1180
PORTRAIT_VIEWPORT_WIDTH = 540
PORTRAIT_VIEWPORT_HEIGHT = 960


def parse_args():
    parser = argparse.ArgumentParser(description="用 Playwright 加入法師鬥惡龍的 Guest 對戰。")
    parser.add_argument("invite_code", nargs="?", help="Host 端產生的邀請碼")
    parser.add_argument("--url", default=HTML_URL, help="遊戲頁面 URL")
    parser.add_argument("--headless", action="store_true", help="以無頭模式執行")
    parser.add_argument("--slow-mo", type=int, default=350, help="操作節奏（毫秒）")
    parser.add_argument("--max-turns", type=int, default=30, help="最多觀察幾個回合")
    parser.add_argument("--timeout-ms", type=int, default=30000, help="等待逾時（毫秒）")
    parser.add_argument(
        "--start-timeout-ms",
        type=int,
        default=300000,
        help="連線後等待 Host 開局的逾時（毫秒）",
    )
    parser.add_argument(
        "--screenshot",
        default=str(DEFAULT_SCREENSHOT),
        help="結束時要輸出的截圖路徑",
    )
    return parser.parse_args()


def get_invite_code(args):
    code = (args.invite_code or os.getenv("INVITE_CODE", "")).strip().upper()
    if code:
        return code
    raise SystemExit("請提供邀請碼，例如：py playwright_guest.py ABC123")


def expand_panel(page, title):
    page.evaluate(
        """label => {
            const panel = [...document.querySelectorAll('details')]
                .find(el => el.querySelector('summary')?.textContent?.includes(label));
            if (panel && !panel.open) panel.open = true;
        }""",
        title,
    )


def switch_panel(page, target):
    page.evaluate(
        """panel => {
            if (typeof switchPanel === 'function') {
                switchPanel(panel);
            }
        }""",
        target,
    )


def snapshot(page):
    return page.evaluate(
        """() => {
            const text = selector =>
                document.querySelector(selector)?.textContent?.trim() ?? '';
            const lastText = selector => {
                const nodes = [...document.querySelectorAll(selector)];
                return nodes.length ? (nodes[nodes.length - 1].textContent?.trim() ?? '') : '';
            };
            return {
                phase: typeof gs !== 'undefined' ? (gs?.phase ?? '') : '',
                turn: typeof gs !== 'undefined' ? (gs?.turn ?? 0) : 0,
                role: typeof p2pRole !== 'undefined' ? p2pRole : '',
                inviteStatus: text('#invite-status'),
                inputIdle: document.getElementById('input-bar')?.classList.contains('idle') ?? true,
                sendButtonText: text('#player-send'),
                mageA: {
                    hp: typeof gs !== 'undefined' ? (gs?.mageA?.hp ?? null) : null,
                    action: typeof gs !== 'undefined' ? (gs?.mageA?.action ?? null) : null,
                    hpText: text('#mageA-hp'),
                    skillText: text('#mageA-skill')
                },
                mageB: {
                    hp: typeof gs !== 'undefined' ? (gs?.mageB?.hp ?? null) : null,
                    action: typeof gs !== 'undefined' ? (gs?.mageB?.action ?? null) : null,
                    hpText: text('#mageB-hp'),
                    skillText: text('#mageB-skill')
                },
                dragon: {
                    hp: typeof gs !== 'undefined' ? (gs?.dragon?.hp ?? null) : null,
                    action: typeof gs !== 'undefined' ? (gs?.dragon?.action ?? null) : null,
                    chargeTurns: typeof gs !== 'undefined' ? (gs?.dragon?.chargeTurns ?? 0) : 0,
                    hpText: text('#dragon-hp'),
                    skillText: text('#dragon-skill')
                },
                lastHint: lastText('.hint-msg .msg-text'),
                lastSystem: lastText('.system-msg .msg-text'),
                lastAlly: lastText('.ally-msg .msg-text'),
                lastPlayer: lastText('.player-msg .msg-text')
            };
        }"""
    )


def is_forced_spell(action_value):
    return action_value in (1, 2, 3)


def is_choice_prompt(state):
    hint = state["lastHint"] or ""
    return "選擇法師B的法術" in hint


def choose_action(state):
    mage_a = state["mageA"]
    mage_b = state["mageB"]
    dragon = state["dragon"]
    last_system = state["lastSystem"]

    if dragon["action"] == 2 or "抬起利爪" in last_system:
        return "2", "龍剛蓄爪，先預備護盾"

    if dragon["action"] == 1 and dragon["chargeTurns"] >= 2:
        return "2", f"龍已吸氣第 {dragon['chargeTurns']} 回合，先預備護盾"

    if (mage_a["hp"] or 0) <= 2:
        return "3", "隊友血量偏低，優先補血"

    if (mage_b["hp"] or 0) <= 1 and (mage_a["hp"] or 0) <= 3:
        return "3", "雙方都危險，嘗試補血協調"

    return "1", "預設走閃電輸出"


def wait_for_connected(page, timeout_ms):
    page.wait_for_function(
        """() => {
            const text = document.getElementById('invite-status')?.textContent ?? '';
            return text.includes('✅');
        }""",
        timeout=timeout_ms,
    )


def wait_for_game_start(page, timeout_ms):
    page.wait_for_function(
        """() => {
            const phase = typeof gs !== 'undefined' ? gs?.phase : undefined;
            const turn = typeof gs !== 'undefined' ? (gs?.turn ?? 0) : 0;
            const lastHint = [...document.querySelectorAll('.hint-msg .msg-text')]
                .at(-1)?.textContent ?? '';
            return ['choosing', 'resolving', 'game_over'].includes(phase)
                || turn > 0
                || lastHint.includes('回合 ');
        }""",
        timeout=timeout_ms,
    )


def wait_for_turn(page, seen_turn, timeout_ms):
    page.wait_for_function(
        """seenTurn => {
            const phase = typeof gs !== 'undefined' ? gs?.phase : undefined;
            const turn = typeof gs !== 'undefined' ? (gs?.turn ?? 0) : 0;
            const idle = document.getElementById('input-bar')?.classList.contains('idle') ?? true;
            const hint = [...document.querySelectorAll('.hint-msg .msg-text')]
                .at(-1)?.textContent ?? '';
            return phase === 'game_over'
                || turn > seenTurn
                || (phase === 'choosing' && turn === seenTurn && !idle && hint.includes('選擇法師B的法術'));
        }""",
        arg=seen_turn,
        timeout=timeout_ms,
    )


def submit_action(page, choice, timeout_ms):
    page.fill("#player-input", choice)
    page.click("#player-send")
    page.wait_for_function(
        """() => {
            const bar = document.getElementById('input-bar');
            const skill = document.getElementById('mageB-skill')?.textContent ?? '';
            const phase = typeof gs !== 'undefined' ? gs?.phase : undefined;
            return bar?.classList.contains('idle') || skill === '✅' || phase === 'game_over';
        }""",
        timeout=timeout_ms,
    )


def log_turn(state):
    print(
        f"回合 {state['turn']} | "
        f"A {state['mageA']['hpText']} {state['mageA']['skillText']} | "
        f"B {state['mageB']['hpText']} {state['mageB']['skillText']} | "
        f"龍 {state['dragon']['hpText']} {state['dragon']['skillText']}"
    )
    if state["lastHint"]:
        print(f"  💡 {state['lastHint']}")
    if state["lastSystem"]:
        print(f"  📜 {state['lastSystem']}")


def main():
    args = parse_args()
    invite_code = get_invite_code(args)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=args.headless,
            slow_mo=args.slow_mo,
            args=[
                f"--window-size={PORTRAIT_WINDOW_WIDTH},{PORTRAIT_WINDOW_HEIGHT}",
                "--window-position=20,20",
            ],
        )
        page = browser.new_page(
            viewport={
                "width": PORTRAIT_VIEWPORT_WIDTH,
                "height": PORTRAIT_VIEWPORT_HEIGHT,
            }
        )

        page.on(
            "console",
            lambda msg: print(f"[browser] {msg.text}")
            if "[P2P" in msg.text or "[MageB LLM]" in msg.text
            else None,
        )
        page.on("pageerror", lambda err: print(f"[page error] {err}"))

        print("▶ 打開遊戲頁面")
        page.goto(args.url)
        page.wait_for_load_state("domcontentloaded")

        switch_panel(page, "dashboard")
        expand_panel(page, "連線對戰")
        page.wait_for_selector("#invite-code-in", state="visible", timeout=args.timeout_ms)
        page.fill("#invite-code-in", invite_code)
        page.click("#join-game")
        print(f"⏳ 正在用邀請碼 {invite_code} 加入…")

        try:
            wait_for_connected(page, args.timeout_ms)
        except PlaywrightTimeoutError:
            state = snapshot(page)
            raise SystemExit(f"連線逾時，目前狀態：{state['inviteStatus'] or '未知'}")

        switch_panel(page, "battle")
        print("✅ 已連線，等待 Host 開始遊戲")

        try:
            wait_for_game_start(page, args.start_timeout_ms)
        except PlaywrightTimeoutError:
            state = snapshot(page)
            raise SystemExit(
                "Host 尚未開始遊戲，等待逾時。"
                f" invite={state['inviteStatus'] or '未知'}"
                f" role={state['role'] or '空'}"
                f" phase={state['phase'] or '空'}"
                f" turn={state['turn']}"
                f" button={state['sendButtonText'] or '空'}"
                f" hint={state['lastHint'] or '空'}"
                f" system={state['lastSystem'] or '空'}"
            )

        print("⚔️ 遊戲開始")
        seen_turn = 0

        for _ in range(args.max_turns):
            try:
                wait_for_turn(page, seen_turn, args.timeout_ms)
            except PlaywrightTimeoutError:
                print("⏱ 等待新回合逾時，結束觀察")
                break

            state = snapshot(page)
            if state["phase"] == "game_over":
                print("🏁 遊戲結束")
                break

            seen_turn = state["turn"]
            log_turn(state)

            if state["mageB"]["hp"] is not None and state["mageB"]["hp"] <= 0:
                print("  ⏭ 法師B 已倒下，本回合自動跳過")
                continue

            if is_forced_spell(state["mageB"]["action"]) or "即將施放" in state["lastHint"]:
                print("  ⏭ 本回合為強制施放，等待結算")
                continue

            if not is_choice_prompt(state):
                print("  ⏭ 尚未收到法師B選招提示，先不送指令")
                continue

            if state["inputIdle"]:
                print("  ⏭ 目前沒有可輸入動作，等待下一個事件")
                continue

            choice, reason = choose_action(state)
            print(f"  ✅ 送出 {choice}：{reason}")
            submit_action(page, choice, args.timeout_ms)

        final_state = snapshot(page)
        print(
            f"結束狀態 | phase={final_state['phase']} | "
            f"A={final_state['mageA']['hpText']} | "
            f"B={final_state['mageB']['hpText']} | "
            f"龍={final_state['dragon']['hpText']}"
        )

        screenshot_path = Path(args.screenshot)
        page.screenshot(path=str(screenshot_path))
        print(f"📸 截圖已輸出：{screenshot_path}")

        page.wait_for_timeout(1500)
        browser.close()


if __name__ == "__main__":
    main()
