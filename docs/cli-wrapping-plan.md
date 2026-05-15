# MD CLI 包裝動工計畫

> 目標：把法師鬥惡龍（網頁應用）包成 agent 友善的 CLI、讓兩個 AI agent 可以同台對戰。
> 寫於 2026-05-14、預估總時程 5-7 天（不含 polish）。
> 跟「網頁應用 CLI 化是 LL 標準」一致（見 [`../../matrix-manager/meetings/2026-05-13-web-app-cli-wrapping-and-md-revival.md`](../../matrix-manager/meetings/2026-05-13-web-app-cli-wrapping-and-md-revival.md)）。

---

## 架構總覽

```
[index.html 渲染遊戲畫面]            ← 一個瀏覽器、一份遊戲
       ↑↓ Playwright DOM 操作
[Flask Daemon：遊戲狀態 + player slot 管理]
       ↑↓ HTTP（內部協定、agent 看不到）
   ┌────┴────┐
[mdgame CLI A]  [mdgame CLI B]    ← 薄殼、各帶 --player=A/B
       ↑              ↑
   [Agent A]       [Agent B]      ← 只看純文字遊戲視野
```

→ **agent 只看遊戲、不管連線**
→ daemon 唯一、CLI 多開、編排層在外面

---

## Phase 0：Daemon 雛形（Day 1-2）

**目標**：Flask 伺服器能控制一個 index.html、提供基本 API。

- [ ] Flask app 起在 `localhost:8080`
- [ ] Playwright headless 開 `index.html`、注入 player 視角參數
- [ ] API endpoints（最小集）：
  - `GET /state?player=A` — 回傳 player A 視角的遊戲狀態 JSON
  - `POST /action?player=A` — 接收 action（card / target）
  - `POST /join?player=A` — player A 加入遊戲
  - `POST /reset` — 重開一局
- [ ] 單元測試：用 curl 模擬 player A 連續打三回合、不會崩

**驗收**：
```bash
curl http://localhost:8080/state?player=A
# 回傳：{"turn": 1, "hp": 80, "hand": [...], ...}
```

---

## Phase 1：CLI 薄殼（Day 3）

**目標**：30-50 行 Python、把 daemon API 翻成 agent 友善的純文字。

- [ ] `mdgame` 命令、接受 `--player=A` `--host=localhost:8080`
- [ ] 自動 join、進入遊戲迴圈
- [ ] 文字格式化（畫 ASCII 戰場、顯示手牌、敵人 HP 條）
- [ ] 接收 stdin 指令、解析後 POST 給 daemon
- [ ] 顯示對手行動（從 daemon 推播 / poll）
- [ ] 隊友聊天：`say "小心右邊"` → 廣播到同隊另一個 CLI 的 stdout

**驗收**：人類自己用兩個 terminal 跑兩個 CLI、能完整打完一局。

---

## Phase 2：多 Player Slot（Day 4）

**目標**：daemon 同時管 2-4 個 player slot、不混亂。

- [ ] Daemon 內部 player slot 表（A / B / C / D）
- [ ] 同步回合制（MUST）：所有 player 都提交 action 才結算
- [ ] 加 timeout：某 player 超過 30 秒沒交、視為 pass
- [ ] 隊伍劃分：A+B vs C+D（3:1 模式則 A vs B+C+D）
- [ ] 聊天頻道：team chat / all chat 區分

**驗收**：四個 terminal 同時跑、能完整打完 2v2。

---

## Phase 3：編排層 match.py（Day 5）

**目標**：用一個 Python 腳本 spawn N 個 agent、自動跑完整場比賽。

- [ ] `match.py` 接受 agent 設定（agent_a_cmd / agent_b_cmd / ...）
- [ ] 自動：開 daemon → 開 N 個 CLI → 各接一個 agent → 跑到分出勝負
- [ ] 記錄到 `matches/YYYY-MM-DD_<agent_a>_vs_<agent_b>.log`
- [ ] 輸出比賽報告（勝負、回合數、關鍵操作）

**驗收**：
```bash
python match.py --a "claude --model opus-4-7" --b "claude --model sonnet-4-6"
# 全自動跑完、產出對戰報告
```

---

## Phase 4：首場 agent 對戰（Day 6-7）

**目標**：兩個真實 AI agent 完整打完一局、有 highlight 可分享。

- [ ] Agent A：Claude Opus 4.7（深度思考型）
- [ ] Agent B：Claude Sonnet 4.6（快反應型）or Codex / Gemini
- [ ] 給 agent 的 system prompt 範本（規則說明 + 策略提示）
- [ ] 跑 10 場、看誰勝率高
- [ ] 錄一場有趣的、剪輯成 demo 影片素材（給 LL 對外用）

**驗收**：能在 YT 拍一支「兩個 AI 打法師鬥惡龍」的影片、有看頭。

---

## 隊友討論功能（free feature）

CLI 內建指令：

```bash
> say "我去打左邊"         # 隊內可見（同隊另一個 CLI stdout）
> shout "投降吧！"          # 全員可見（含敵隊）
> 火球 → 火龍              # 一般遊戲指令
```

實作：daemon 維護 chat buffer、每個 CLI poll `/chat?player=A&since=...` 取新訊息插進 stdout。

→ Agent 自然會把隊友訊息當 context、自己決定要不要回應
→ 不需要強制 agent 講話、它策略性沉默也是一種風格

---

## 不在這次範圍

- ❌ 觀戰 UI（SP 的工作、不是 MD）
- ❌ 接 RR 平台（iframe 化是另一個 epic）
- ❌ RL agent 訓練（要先有大量 match log 再說）
- ❌ Web UI / Dashboard（CLI 夠了、不過度設計）

---

## 完成後 LL 整體收益

```
1. MD 從「卡住的 PoC」變「跑得動的競技場」
2. CLI + Daemon 模板可複製到其他 MUST 遊戲（SP / DD / 未來新遊戲）
3. 編排層 match.py 是 SS 競技場的雛形
4. 對外有「AI vs AI 實戰」的展示素材（接 NN / YT / 直播）
5. 驗證「網頁 → CLI 化」這條 LL 標準是不是真的好走
```

---

## 一句話總結

```
1 個 daemon、N 個薄 CLI、agent 只看遊戲、編排層在外。
Day 1-3 打地基、Day 4-5 上多人、Day 6-7 看 AI 對戰。
```

→ 等不及要看到 agent 同台競技！
