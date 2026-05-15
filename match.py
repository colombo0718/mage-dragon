"""
match.py — 極簡編排層
讓兩個 agent 各扮演法師 A / B 對著 daemon 出招。

用法：
  python match.py --a codex --b gemini
  python match.py --a gemini --b codex --rounds 1

注意：daemon 必須先在 localhost:8080 跑。
"""
import argparse, subprocess, time, json, sys, io, urllib.request, urllib.parse, re, shutil
from pathlib import Path
from datetime import datetime

CODEX_EXE = shutil.which("codex.cmd") or shutil.which("codex")
GEMINI_EXE = shutil.which("gemini.cmd") or shutil.which("gemini")

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

HOST = "http://localhost:8080"
LOG_DIR = Path("C:/Users/USER/mage-dragon/matches")
LOG_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = """你是法師鬥惡龍遊戲裡的玩家。
規則：
- 你跟隊友合作打惡龍（你 HP 通常 5、隊友 HP 通常 5、龍 HP 20）
- 每回合三選一：1=⚡閃電（雙人同步=雙倍傷害）、2=🛡️護盾（擋火、可反彈）、3=💚補血（雙人同步=滿血）
- 龍會吸氣 2 回合後噴火、噴火造成大量傷害（要出盾）
- 隊伍策略：龍吸氣時兩人都出盾、平時兩人都閃電、HP 危險時補血

我會告訴你戰場狀態、你只能回答一個數字：1、2、或 3。
不要解釋、不要多餘文字、只回那一個數字。
"""

def get_state(player):
    with urllib.request.urlopen(f"{HOST}/state?player={player}", timeout=10) as r:
        return json.loads(r.read())

def submit(player, value):
    data = json.dumps({"player": player, "value": str(value)}).encode("utf-8")
    req = urllib.request.Request(f"{HOST}/action", data=data, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def parse_hp(txt):
    try: return int(''.join(c for c in (txt or '') if c.isdigit()))
    except: return 0

def make_prompt(state, player):
    a, b, d = parse_hp(state["aHp"]), parse_hp(state["bHp"]), parse_hp(state["dHp"])
    me_hp = a if player == "A" else b
    tm_hp = b if player == "A" else a
    last = state.get("last_msg") or ""
    return f"""【法師鬥惡龍 - 你是法師 {player}】
你 HP: {me_hp}
隊友 HP: {tm_hp}
惡龍 HP: {d}
最近系統訊息：{last}

選擇你的行動，只回 1 / 2 / 3：
"""

def call_ollama(model, prompt):
    """呼叫本機 Ollama API、回傳 response 文字。"""
    full = SYSTEM_PROMPT + "\n\n" + prompt + "\n\n只回答一個數字：1、2、或 3。不要任何其他文字。"
    payload = json.dumps({"model": model, "prompt": full, "stream": False,
                          "options": {"temperature": 0.3, "num_predict": 50}}).encode("utf-8")
    req = urllib.request.Request("http://localhost:11434/api/generate",
                                 data=payload, headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read())
            return data.get("response", ""), 0
    except Exception as e:
        return f"[exception] {e}", -1


def call_agent(agent, prompt):
    """呼叫 agent、回傳 raw 文字。支援 codex / gemini / ollama:<model>"""
    full = SYSTEM_PROMPT + "\n\n" + prompt
    try:
        if agent.startswith("ollama:"):
            model = agent.split(":", 1)[1]
            return call_ollama(model, prompt)
        elif agent == "codex":
            if not CODEX_EXE: return "[err] codex not found in PATH", -1
            r = subprocess.run([CODEX_EXE, "exec", full],
                               capture_output=True, text=True, encoding='utf-8',
                               timeout=120, errors='replace', shell=False)
        elif agent == "gemini":
            if not GEMINI_EXE: return "[err] gemini not found in PATH", -1
            r = subprocess.run([GEMINI_EXE, "-p", full],
                               capture_output=True, text=True, encoding='utf-8',
                               timeout=120, errors='replace', shell=False)
        else:
            return f"[err] unknown agent {agent}", 0
        return (r.stdout or "") + (r.stderr or ""), r.returncode
    except subprocess.TimeoutExpired:
        return "[timeout]", -1
    except Exception as e:
        return f"[exception] {e}", -1

def extract_action(text):
    """從 agent 輸出找 1/2/3。忽略錯誤訊息行、找最後一個獨立數字。"""
    if not text or text.startswith("[err]") or text.startswith("[exception]") or text.startswith("[timeout]"):
        return None
    # 過濾掉錯誤訊息行（WinError 2 etc）
    lines = [ln for ln in text.splitlines() if not re.search(r"WinError|Error|Exception|Traceback", ln)]
    cleaned = "\n".join(lines)
    # 從尾巴往前找獨立的 1/2/3
    matches = re.findall(r"(?<![\d.])([123])(?![\d.])", cleaned)
    return matches[-1] if matches else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="法師 A 的 agent（codex / gemini）")
    ap.add_argument("--b", required=True, help="法師 B 的 agent")
    ap.add_argument("--max-turns", type=int, default=15)
    args = ap.parse_args()

    log_path = LOG_DIR / f"{datetime.now():%Y-%m-%d_%H%M%S}_{args.a}_vs_{args.b}.md"
    log_lines = [f"# {args.a} (A) vs {args.b} (B) — {datetime.now():%Y-%m-%d %H:%M:%S}\n"]

    def log(msg):
        print(msg)
        log_lines.append(msg)

    log(f"\n## Setup")
    log(f"- A: **{args.a}**")
    log(f"- B: **{args.b}**")
    log(f"- daemon: {HOST}\n")

    last_turn = None
    for step in range(args.max_turns * 4):  # 每回合可能 4 個 phase
        state = get_state("A")
        if state.get("phase") == "game_over":
            log("\n## 🏁 Game Over")
            log(f"```\nA HP: {state['aHp']}  B HP: {state['bHp']}  Dragon HP: {state['dHp']}\nLast: {state['last_msg']}\n```")
            break

        turn = state.get("turn")
        idle = state.get("input_idle", True)
        if idle:
            time.sleep(0.8); continue

        if turn != last_turn:
            log(f"\n## Turn {turn}")
            log(f"```")
            log(f"A HP: {state['aHp']}  B HP: {state['bHp']}  Dragon HP: {state['dHp']}")
            log(f"System: {state['last_msg']}")
            log(f"```")
            last_turn = turn

        # A 出招
        prompt_a = make_prompt(state, "A")
        log(f"\n### 法師 A ({args.a}) 思考中…")
        raw_a, _ = call_agent(args.a, prompt_a)
        act_a = extract_action(raw_a)
        log(f"<details><summary>{args.a} 原始輸出</summary>\n\n```\n{raw_a[:400]}\n```\n</details>")
        if not act_a:
            log(f"⚠️ A 沒給出有效行動、預設 1")
            act_a = "1"
        log(f"**A 選擇：{act_a}**")
        try:
            submit("A", act_a)
        except Exception as e:
            log(f"❌ submit A 失敗: {e}")

        # B 出招
        state_b = get_state("B")
        prompt_b = make_prompt(state_b, "B")
        log(f"\n### 法師 B ({args.b}) 思考中…")
        raw_b, _ = call_agent(args.b, prompt_b)
        act_b = extract_action(raw_b)
        log(f"<details><summary>{args.b} 原始輸出</summary>\n\n```\n{raw_b[:400]}\n```\n</details>")
        if not act_b:
            log(f"⚠️ B 沒給出有效行動、預設 1")
            act_b = "1"
        log(f"**B 選擇：{act_b}**")
        try:
            submit("B", act_b)
        except Exception as e:
            log(f"❌ submit B 失敗: {e}")

        # 等結算
        time.sleep(2.5)

    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"\n📄 log: {log_path}")


if __name__ == "__main__":
    main()
