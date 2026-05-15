# Multi-Agent 共鬥架構

法師鬥惡龍的三方 AI 對局設計。

---

## 三方角色與資訊邊界

```
[MageA Agent]  ←─ P2P ─→  [Game Engine (Host)]  ←─ P2P ─→  [Dragon Agent]
                                    ↑
                           ←─ P2P ─┘
                           [MageB Agent]
```

| 角色 | 目標 | 可見資訊 | 特殊能力 |
|------|------|---------|---------|
| 法師A | 合作擊龍 | 自身 HP/狀態、隊友詠唱 ✅/❓、龍蓄力狀態 | 承諾機制（詠唱不可取消） |
| 法師B | 合作擊龍 | 自身 HP/狀態、隊友詠唱 ✅/❓、龍蓄力狀態 | 承諾機制（詠唱不可取消） |
| 惡龍 | 擊倒雙法師 | 雙方 HP、雙方詠唱 ✅/❓、自身蓄力進度 | **台詞可以說謊** |

資訊隔離由 P2P 訊息協議強制——各方只收到應該知道的欄位，不依賴信任。

---

## 通訊架構

Game Engine（Host 頁面）是唯一的 source of truth，負責所有結算。  
三方 Agent 各自透過 P2P 連線送出行動、接收結算結果。

### 現有訊息（法師B ↔ Host）

| 訊息 | 方向 | 內容 |
|------|------|------|
| `game_start` | Host→Guest | 通知開始新局 |
| `turn_start` | Host→Guest | `{ turn, bDead, bForced, bAction }` |
| `action` | Guest→Host | `{ value: 0-3 }` |
| `ready_update` | Host→Guest | `{ mageA: bool, dragon: bool }` |
| `resolve` | Host→Guest | `{ gs, log, msgs, over }` |
| `chat` | 雙向 | `{ from, text }` |

### 新增訊息（惡龍 ↔ Host）

| 訊息 | 方向 | 內容 |
|------|------|------|
| `dragon_turn_start` | Host→Dragon | `{ turn, dragon_state, mageA_committed, mageB_committed, mageA_hp, mageB_hp }` |
| `dragon_action` | Dragon→Host | `{ action: 0-4, dialogue: string }` |
| `dragon_resolve` | Host→Dragon | `{ gs_snapshot, msgs, over }` |

`dragon_turn_start` 只送「✅ 已承諾」的布林值，不送承諾的是什麼法術——資訊邊界在協議層強制。

---

## MCP 層設計

每個 Agent 掛一個本機 MCP server，Claude Code / Codex 透過 MCP tools 操作。

### Game Bridge MCP（共用基礎）

在 `index.html` 加入 `window.gameAPI`，MCP server 透過 Playwright CDP 呼叫：

```js
window.gameAPI = {
    getState:      () => ({...structured game state...}),
    submitAction:  (n) => { /* trigger handlePlayerInput equivalent */ },
    sendChat:      (text) => { appendMessage('player', text); },
    screenshot:    () => null  // handled by Playwright
};
```

### 法師A MCP Server（mage-a-mcp.py）

```python
@mcp.tool()
def observe() -> dict:
    """取得法師A視角的遊戲狀態"""
    return page.evaluate("window.gameAPI.getMageAState()")

@mcp.tool()
def submit_action(action: int) -> str:
    """送出法師A的招式選擇（0-3）"""
    page.evaluate(f"window.gameAPI.submitMageAAction({action})")
    return f"已選擇 {action}"

@mcp.tool()
def send_chat(text: str) -> str:
    """對隊友說話"""
    page.evaluate(f"window.gameAPI.sendChat({json.dumps(text)})")
    return "已傳送"
```

### 法師B MCP Server（mage-b-mcp.py）

結構同上，但操作 Guest 頁面，透過 P2P 送 `action` 訊息。

### 惡龍 MCP Server（dragon-mcp.py）

```python
@mcp.tool()
def observe() -> dict:
    """取得惡龍視角：只含應見資訊"""
    # { turn, dragon_hp, dragon_action, canFire, canClaw,
    #   mageA: {hp, committed}, mageB: {hp, committed} }

@mcp.tool()
def act(action: int, dialogue: str) -> str:
    """送出惡龍行動（0-4）與公開台詞（可說謊）"""
```

---

## 技術路線

### Phase 1（現在）：遊戲核心補完
- [x] 腳本龍（EMBER_DUMMY、MECHA_DUMMY）
- [x] LLM 龍（霧息欺詐龍、雷冠壓制龍）in-page 版
- [x] 法師A 智能模式
- [ ] 訊息自動捲底、結算節奏

### Phase 2：Game Bridge
- [ ] `window.gameAPI` 加入 index.html
- [ ] `game-mcp-server.py`（Playwright + FastMCP）
- [ ] Host 維護兩條 P2P 連線（Guest + Dragon）

### Phase 3：三方 Agent 對局
- [ ] `mage-a-mcp.py`、`mage-b-mcp.py`、`dragon-mcp.py`
- [ ] Claude Code 控法師A，Codex 控法師B，第三個 session 控龍
- [ ] 回合 log JSON 匯出（記錄龍台詞 vs 實際行動）

### Phase 4：Research Layer
- [ ] 每回合記錄 `{ dialogue, actual_action, mages_response }`
- [ ] 統計「龍說謊時法師是否被騙」
- [ ] 多局勝率、雙閃協調率、說謊成功率

---

## 關鍵設計決策

**為什麼選 P2P 而非 CDP 直連**：CDP 讓龍 agent 能讀 Host 記憶體，破壞資訊隔離。P2P 的訊息是主動設計的資訊邊界，研究效度有保障。

**龍不需要 GUI**：龍永遠是 AI 控制，結構化資訊透過 MCP tools 傳遞，不需要視覺介面。龍的台詞透過現有 `appendMessage('dragon', ...)` 顯示在法師畫面上。

**單一 source of truth**：Host 頁面是唯一做結算的地方，三方 agent 都只負責送行動、收結果，不做任何結算邏輯。
