"""
MD CLI Phase 0 Daemon
─────────────────────
Flask + Playwright wrapper, exposes single-player API.

Endpoints:
  GET  /state?player=A|B    當前狀態（HP、phase、最近系統訊息）
  POST /action              body: {"player":"A","value":"1"|"2"|"3"}
  POST /reset               重開一局
  GET  /chat?player=X       取得最近聊天訊息
  POST /chat                body: {"player":"A","text":"...","scope":"team|all"}
  GET  /health              daemon 活著？

Run:
  python daemon.py            → http://localhost:8080
"""
import sys, io, re, threading, time, json
from pathlib import Path
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

URL = "file:///C:/Users/USER/mage-dragon/dual-view.html"
ENV = Path("C:/Users/USER/mage-dragon/.env")

# ─── Game Daemon ───────────────────────────────────────────────────────────
class GameDaemon:
    def __init__(self):
        self.lock = threading.Lock()
        self.pw = None
        self.browser = None
        self.page = None
        self.host = None    # frame for player A
        self.guest = None   # frame for player B
        self.chat_log = []  # [{"from":"A","text":"...","scope":"team","ts":...}]
        self._ready = False

    def _groq_key(self):
        try:
            m = re.search(r"GROQ_API_KEY=(.+)", ENV.read_text())
            return m.group(1).strip() if m else ""
        except: return ""

    def _wait_status(self, frame, text, timeout=25000):
        frame.wait_for_function(
            f"() => document.getElementById('invite-status')?.textContent?.includes('{text}')",
            timeout=timeout)

    def start(self):
        """啟動瀏覽器、建立 P2P 連線、進入可玩狀態。阻塞直到 ready。"""
        print("[daemon] starting browser...")
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=False, args=["--start-maximized"])
        self.page = self.browser.new_page(no_viewport=True)
        self.page.on("pageerror", lambda e: print(f"[page] {e}"))
        self.page.goto(URL)
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(800)

        self.host = self.page.frame(name="host")
        self.guest = self.page.frame(name="guest")

        # API key
        key = self._groq_key()
        if key:
            self.host.click("details:has(summary:text('智能模型'))")
            self.host.wait_for_timeout(200)
            self.host.fill("#global-api-key", key)
            self.host.click("#save-ai-config")
            print(f"[daemon] api key set ({key[:8]}…)")

        # 生邀請碼 + 加入
        self.host.click("details:has(summary:text('連線對戰'))")
        self.host.wait_for_timeout(300)
        self.host.click("#generate-invite")
        self._wait_status(self.host, "等待隊友", timeout=25000)
        code = self.host.input_value("#invite-code-out")
        print(f"[daemon] invite code: {code}")

        self.guest.click(".tab-btn[data-target='dashboard']")
        self.guest.wait_for_timeout(200)
        self.guest.click("details:has(summary:text('連線對戰'))")
        self.guest.wait_for_timeout(300)
        self.guest.fill("#invite-code-in", code)
        self.guest.click("#join-game")
        self._wait_status(self.host, "✅", timeout=20000)
        self._wait_status(self.guest, "✅", timeout=20000)
        self.guest.click(".tab-btn[data-target='battle']")
        self.guest.wait_for_timeout(300)

        # 開局
        self.host.click("#player-send")
        self.host.wait_for_timeout(600)
        self._ready = True
        print("[daemon] ready. game started.")

    def _frame_of(self, player):
        if player == "A": return self.host
        if player == "B": return self.guest
        raise ValueError(f"unknown player: {player}")

    def get_state(self, player):
        with self.lock:
            f = self._frame_of(player)
            return f.evaluate("""() => ({
                aHp: document.getElementById('mageA-hp')?.textContent,
                bHp: document.getElementById('mageB-hp')?.textContent,
                dHp: document.getElementById('dragon-hp')?.textContent,
                phase: (typeof gs !== 'undefined') ? gs?.phase : null,
                turn:  (typeof gs !== 'undefined') ? gs?.turn  : null,
                last_msg: [...document.querySelectorAll('.system-msg .msg-text')].at(-1)?.textContent ?? '',
                input_idle: document.getElementById('input-bar')?.classList?.contains('idle') ?? true,
            })""")

    def submit_action(self, player, value):
        with self.lock:
            f = self._frame_of(player)
            # 等輸入欄開放
            f.wait_for_function(
                "() => !document.getElementById('input-bar').classList.contains('idle')",
                timeout=20000)
            f.fill("#player-input", str(value))
            f.click("#player-send")
            return {"ok": True, "player": player, "value": value}

    def set_identity(self, player, name, avatar):
        """走正規 UI flow：對應 frame 點 avatar-picker、填 player-id input。
        Avatar 必須是預設清單裡的（🧙😎🤠🥷🧝🧞🥸）。"""
        with self.lock:
            f = self.host if player == "A" else self.guest
            # 確保「連線對戰」details 開啟（player-id 在裡面）
            try:
                f.click("details:has(summary:text('連線對戰'))", timeout=1500)
                f.wait_for_timeout(100)
            except: pass
            if avatar:
                try:
                    f.click(f".avatar-opt[data-emoji='{avatar}']", timeout=1500)
                except Exception as e:
                    print(f"[identity] avatar {avatar} not in picker: {e}")
            if name:
                # 用 fill 觸發 input 事件、handler 會更新 mageX-name
                f.fill("#player-id", name)
                f.evaluate("document.getElementById('player-id').dispatchEvent(new Event('input'))")
            f.wait_for_timeout(100)
            return {"ok": True, "player": player, "name": name, "avatar": avatar}

    def reset(self):
        """game_over 後點「再來一局」、保留 P2P 連線。"""
        with self.lock:
            self.chat_log.clear()
            state = self.host.evaluate("() => ({"
                                       " phase: (typeof gs !== 'undefined') ? gs?.phase : null,"
                                       " idle: document.getElementById('input-bar')?.classList?.contains('idle')"
                                       " })")
            if state.get("phase") != "game_over":
                return {"ok": False, "error": f"not game_over yet (phase={state.get('phase')})"}
            if not state.get("idle"):
                return {"ok": False, "error": "input bar not idle, cannot restart"}
            # host 點「再來一局」（gsStart）、P2P 廣播給 guest
            self.host.click("#player-send")
            self.host.wait_for_timeout(800)
            print("[daemon] reset → 再來一局 clicked")
            return {"ok": True, "note": "再來一局"}

    def add_chat(self, player, text, scope="team"):
        with self.lock:
            entry = {"from": player, "text": text, "scope": scope, "ts": time.time()}
            self.chat_log.append(entry)
            return entry

    def get_chat(self, player, since=0.0):
        with self.lock:
            # 簡化：team 模式只能看到隊友的（這版單局沒分隊、全可見）
            return [m for m in self.chat_log if m["ts"] > since]


# ─── Flask API ─────────────────────────────────────────────────────────────
app = Flask(__name__)
daemon = GameDaemon()


@app.get("/health")
def health():
    return jsonify({"ok": True, "ready": daemon._ready})


@app.get("/state")
def state():
    player = request.args.get("player", "A").upper()
    try:
        return jsonify(daemon.get_state(player))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/action")
def action():
    data = request.get_json(force=True)
    player = data.get("player", "A").upper()
    value = data.get("value")
    try:
        return jsonify(daemon.submit_action(player, value))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/identity")
def identity():
    data = request.get_json(force=True)
    try:
        return jsonify(daemon.set_identity(
            data.get("player","A").upper(),
            data.get("name",""),
            data.get("avatar","")))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/reset")
def reset():
    try:
        return jsonify(daemon.reset())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/chat")
def get_chat():
    player = request.args.get("player", "A").upper()
    since = float(request.args.get("since", 0))
    return jsonify(daemon.get_chat(player, since))


@app.post("/chat")
def post_chat():
    data = request.get_json(force=True)
    return jsonify(daemon.add_chat(
        data.get("player", "A").upper(),
        data.get("text", ""),
        data.get("scope", "team")))


# ─── Boot ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    daemon.start()
    print("[daemon] flask serving on http://localhost:8080")
    # threaded=False → Playwright sync API 不是 thread-safe
    app.run(host="127.0.0.1", port=8080, threaded=False, use_reloader=False)
