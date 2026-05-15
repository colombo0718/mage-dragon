"""
match v2 — Claude CLI vs Codex CLI、各自有 session 持久記憶。

用法：
  python match_v2.py --a claude --b codex --max-turns 12
"""
import argparse, subprocess, time, json, sys, io, re, shutil, urllib.request
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

HOST = "http://localhost:8080"
LOG_DIR = Path("C:/Users/USER/mage-dragon/matches")
LOG_DIR.mkdir(exist_ok=True)

CODEX_EXE = shutil.which("codex.cmd") or shutil.which("codex")
CLAUDE_EXE = shutil.which("claude.cmd") or shutil.which("claude")
SCHEMA = "C:/Users/USER/mage-dragon/action-schema.json"

OPENING_PROMPT_A = """你是法師A、要跟法師B合作打惡龍。
規則：
- 1=⚡閃電（雙人同步 -4 D、單人 -1 D）
- 2=🛡️盾（實測無效、不要選）
- 3=💚補血（雙人同步各 +3 HP）
- 龍：吸氣2回合 → 噴火（兩名法師各 -4 HP）→ 馬上下個循環
- 策略：交替 attack(1) → heal(3)、永不選 2
- 看到 last_msg「吸氣第2回合」表示火即將來、heal 保命
僅回 JSON: {"action":"1|2|3","reason":"..."}"""

OPENING_PROMPT_B = OPENING_PROMPT_A.replace("法師A", "法師B").replace("法師B、要跟法師B", "法師B、要跟法師A")


def http_get(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())

def http_post(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def parse_hp(txt):
    try: return int(''.join(c for c in (txt or '') if c.isdigit()))
    except: return 0

def state_for(player, state):
    a = parse_hp(state["aHp"]); b = parse_hp(state["bHp"]); d = parse_hp(state["dHp"])
    me = a if player=="A" else b
    tm = b if player=="A" else a
    return (f"Turn {state.get('turn')}, phase={state.get('phase')}, "
            f"我HP={me}, 隊友HP={tm}, 龍HP={d}, last_msg={state.get('last_msg','')}\n"
            f"選 action (1/2/3) 並 JSON 回應。")


# ── agent backends ────────────────────────────────────────────────
def codex_open(prompt):
    """First codex call with schema, returns (session_id, action, reason, raw)."""
    r = subprocess.run(
        [CODEX_EXE, "exec", "--output-schema", SCHEMA, "--skip-git-repo-check", prompt],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        timeout=180, shell=False)
    raw = r.stdout + r.stderr
    sid_m = re.search(r"session id:\s*([0-9a-f-]+)", raw)
    sid = sid_m.group(1) if sid_m else None
    # find last JSON object
    json_m = re.findall(r'\{"action"\s*:\s*"[123]"[^}]*\}', raw)
    if json_m:
        data = json.loads(json_m[-1])
        return sid, data["action"], data.get("reason",""), raw
    # fallback last digit
    digits = re.findall(r'(?<![\d.])([123])(?![\d.])', raw)
    return sid, (digits[-1] if digits else "1"), "(no-json)", raw


def codex_resume(sid, prompt):
    r = subprocess.run(
        [CODEX_EXE, "exec", "resume", sid, "--skip-git-repo-check", prompt],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        timeout=180, shell=False)
    raw = r.stdout + r.stderr
    # resume no schema – parse digit
    # try json first
    json_m = re.findall(r'\{"action"\s*:\s*"[123]"[^}]*\}', raw)
    if json_m:
        data = json.loads(json_m[-1])
        return data["action"], data.get("reason",""), raw
    # filter error lines, find action digit
    lines = [ln for ln in raw.splitlines() if not re.search(r"Error|WinError|tokens used|session id|user|codex", ln, re.I)]
    cleaned = "\n".join(lines[-10:])  # last 10 lines = answer area
    digits = re.findall(r'(?<![\d.])([123])(?![\d.])', cleaned)
    return (digits[-1] if digits else "1"), "(parsed-text)", raw


def claude_call(prompt, session_id=None):
    cmd = [CLAUDE_EXE, "--print", "--output-format", "json"]
    if session_id:
        cmd += ["--resume", session_id]
    cmd += [prompt]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=180, shell=False)
    raw = r.stdout + r.stderr
    try:
        data = json.loads(r.stdout)
        sid = data.get("session_id")
        result = data.get("result", "")
        # parse action from result
        json_m = re.findall(r'\{"action"\s*:\s*"[123]"[^}]*\}', result)
        if json_m:
            ad = json.loads(json_m[-1])
            return sid, ad["action"], ad.get("reason",""), raw
        digits = re.findall(r'(?<![\d.])([123])(?![\d.])', result)
        return sid, (digits[-1] if digits else "1"), "(parsed)", raw
    except Exception as e:
        return None, "1", f"(error: {e})", raw


# ── main loop ─────────────────────────────────────────────────────
AVATAR_MAP = {"claude": "🥷", "codex": "😎", "gemini": "🤠", "ollama": "🧞"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, choices=["claude","codex"])
    ap.add_argument("--b", required=True, choices=["claude","codex"])
    ap.add_argument("--max-turns", type=int, default=12)
    args = ap.parse_args()

    # 設玩家身分（直播可讀性）
    for player, agent in [("A", args.a), ("B", args.b)]:
        try:
            http_post(f"{HOST}/identity", {
                "player": player,
                "name": f"{agent.capitalize()}({player})",
                "avatar": AVATAR_MAP.get(agent, "🧙")
            })
            print(f"[identity] {player} = {agent} {AVATAR_MAP.get(agent)}")
        except Exception as e:
            print(f"[identity] set {player} error: {e}")

    log_path = LOG_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{args.a}_vs_{args.b}_v2.md"
    lines = [f"# {args.a}(A) vs {args.b}(B) — {datetime.now():%H:%M:%S}\n"]

    def L(m):
        print(m); lines.append(str(m))

    sid_a = sid_b = None

    def ask(agent, player, prompt, sid):
        L(f"\n### 法師 {player} ({agent}) 思考 …")
        if agent == "codex":
            if sid is None:
                new_sid, act, reason, raw = codex_open(prompt)
                L(f"[codex session: {new_sid}]")
                return new_sid, act, reason
            else:
                act, reason, raw = codex_resume(sid, prompt)
                return sid, act, reason
        elif agent == "claude":
            new_sid, act, reason, raw = claude_call(prompt, sid)
            if sid is None:
                L(f"[claude session: {new_sid}]")
            return new_sid, act, reason

    last_turn = None
    for step in range(args.max_turns * 4):
        state = http_get(f"{HOST}/state?player=A")
        if state.get("phase") == "game_over":
            L(f"\n## 🏁 Game Over — A:{state['aHp']} B:{state['bHp']} D:{state['dHp']}")
            L(f"`{state['last_msg']}`")
            break
        if state.get("input_idle", True):
            time.sleep(1); continue

        turn = state.get("turn")
        if turn != last_turn:
            L(f"\n## Turn {turn}  A:{state['aHp']}  B:{state['bHp']}  D:{state['dHp']}")
            L(f"`{state['last_msg']}`")
            last_turn = turn

        # A
        prompt_a = OPENING_PROMPT_A + "\n\n" + state_for("A", state) if sid_a is None else state_for("A", state)
        sid_a, act_a, reason_a = ask(args.a, "A", prompt_a, sid_a)
        L(f"**A → {act_a}** ({reason_a})")
        try: http_post(f"{HOST}/action", {"player":"A","value":act_a})
        except Exception as e: L(f"submit A error: {e}")

        # B
        state2 = http_get(f"{HOST}/state?player=B")
        prompt_b = OPENING_PROMPT_B + "\n\n" + state_for("B", state2) if sid_b is None else state_for("B", state2)
        sid_b, act_b, reason_b = ask(args.b, "B", prompt_b, sid_b)
        L(f"**B → {act_b}** ({reason_b})")
        try: http_post(f"{HOST}/action", {"player":"B","value":act_b})
        except Exception as e: L(f"submit B error: {e}")

        time.sleep(3)

    log_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📄 log: {log_path}")
    print(f"   A session: {sid_a}")
    print(f"   B session: {sid_b}")


if __name__ == "__main__":
    main()
