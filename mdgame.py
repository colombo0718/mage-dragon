"""
MD CLI — agent 友善的薄殼 client。

Usage:
  python mdgame.py --player A
  python mdgame.py --player B --host http://localhost:8080 --poll 0.6

Agent 看到的世界：
  ─ 純文字戰場顯示
  ─ stdin 輸入 1/2/3 出招、或 say "..." 隊友聊天
  ─ 結算後自動顯示下一回合視野
  ─ 沒有連線、認證、player_id 註冊等雜訊
"""
import argparse, sys, time, json, io
import urllib.request, urllib.parse, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')


def http_get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def http_post(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def parse_hp(text):
    try: return int(''.join(c for c in (text or '') if c.isdigit()))
    except: return 0


def render(state, player):
    """畫個簡單的 ASCII 戰場給 agent 看。"""
    a, b, d = parse_hp(state.get("aHp")), parse_hp(state.get("bHp")), parse_hp(state.get("dHp"))
    turn = state.get("turn") or "?"
    phase = state.get("phase") or "?"
    last = state.get("last_msg") or ""
    me = "A" if player == "A" else "B"
    teammate = "B" if player == "A" else "A"
    me_hp = a if player == "A" else b
    tm_hp = b if player == "A" else a

    print(f"\n══════════════ Turn {turn} ({phase}) ══════════════")
    print(f"  你（法師 {me}）   HP: {me_hp:>3}")
    print(f"  隊友（法師 {teammate}）HP: {tm_hp:>3}")
    print(f"  惡龍              HP: {d:>3}")
    if last:
        print(f"\n  📜 {last}")
    print(f"\n  輸入：")
    print(f"    1 = ⚡ 閃電（雙人同步 = 雙倍傷害）")
    print(f"    2 = 🛡️ 護盾（擋火、可反彈）")
    print(f"    3 = 💚 補血（雙人同步 = 滿血）")
    print(f"    say <文字>   隊友聊天（如：say 我去擋）")
    print(f"    quit          離開")
    print(f"  ────────────────────────────────────────")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--player", default="A", choices=["A", "B"])
    ap.add_argument("--host", default="http://localhost:8080")
    ap.add_argument("--poll", type=float, default=0.8, help="輪詢秒數")
    args = ap.parse_args()
    host = args.host.rstrip("/")
    player = args.player

    # health check
    try:
        h = http_get(f"{host}/health")
        if not h.get("ready"):
            print(f"[mdgame] daemon 還沒 ready、等一下再試")
            return
    except Exception as e:
        print(f"[mdgame] 連不上 daemon ({host}): {e}")
        return

    print(f"[mdgame] 連上 daemon、你是法師 {player}。準備出招！")

    last_turn = None
    last_chat_ts = 0.0

    while True:
        try:
            state = http_get(f"{host}/state?player={player}")
        except Exception as e:
            print(f"[mdgame] 讀狀態失敗: {e}")
            time.sleep(1); continue

        if state.get("phase") == "game_over":
            print("\n🏁 遊戲結束。最終戰況：")
            render(state, player)
            break

        # 新回合 → 顯示
        turn = state.get("turn")
        idle = state.get("input_idle", True)
        if turn != last_turn and not idle:
            render(state, player)
            last_turn = turn

        # 撈聊天
        try:
            msgs = http_get(f"{host}/chat?player={player}&since={last_chat_ts}")
            for m in msgs:
                if m["from"] != player:
                    print(f"  💬 [{m['from']}]: {m['text']}")
                last_chat_ts = max(last_chat_ts, m["ts"])
        except Exception:
            pass

        # 輸入欄沒開 → 等
        if idle:
            time.sleep(args.poll)
            continue

        # 等使用者輸入（agent 接 stdin）
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[mdgame] bye"); break

        if not line: continue
        if line.lower() in ("quit", "exit", "q"):
            print("[mdgame] bye"); break

        if line.startswith("say "):
            text = line[4:].strip()
            try:
                http_post(f"{host}/chat", {"player": player, "text": text, "scope": "team"})
                print(f"  💬 [你→隊友]: {text}")
            except Exception as e:
                print(f"  [chat error] {e}")
            continue

        if line in ("1", "2", "3"):
            try:
                http_post(f"{host}/action", {"player": player, "value": line})
                names = {"1": "⚡ 閃電", "2": "🛡️ 護盾", "3": "💚 補血"}
                print(f"  ▶️  送出 {names[line]}、等結算…")
                time.sleep(args.poll)
            except Exception as e:
                print(f"  [action error] {e}")
            continue

        print(f"  ❓ 不認得指令：{line}（試 1/2/3、say <文字>、quit）")


if __name__ == "__main__":
    main()
