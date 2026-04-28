# CHANGELOG — 法師鬥惡龍

---

## 2026-04-29 — Playwright 自動測試 + 雙視窗 + Bug 修復

### 新增
- `dual-view.html`：iframe 3:1 並排（Host 景觀：Guest 直向），供 Playwright 全螢幕雙視窗測試
- `playwright_full_game.py`：重構為單 browser + 雙 iframe，`--start-maximized` 全螢幕
- `playwright_stress_test.py`：P2P 連線只建一次，10 局連測，統計勝率
- `gsSetWaiting()`：Guest 行動後保留輸入框但 disable 送出鈕，placeholder 改為「等待結算中，可傳訊息給隊友…」

### 修復
- **回合記錄重複 bug**：`gsCheckReady()` 在 aForced + bForced 同時成立時被呼叫兩次，各自排程一次 `gsReveal()`。修法：排程前設 `gs.phase = 'revealing'` 防止第二次排程
- **Guest 行動後輸入框消失**：`gsSetIdle('等待結算…')` 改為 `gsSetWaiting()`，保留輸入框
- **Playwright game_over 偵測**：改用按鈕文字包含「再來」判斷，比讀 `gs.phase` 更可靠

### 架構決策
- Playwright 從雙 browser instance 改為單 browser + iframe frames，操作 API 相同，視窗管理更簡單
- `check_game_over()` 和 `guest_submitted()` 改用 DOM 狀態偵測取代 phase 值

---

## 2026-04-28 前 — MVP 核心完整實作

### 新增
- **完整遊戲引擎**（index.html）：State machine、傷害結算、勝負判定、再來一局
- **詠唱承諾機制**：action 1-3 詠唱，下回合強制施放 4-6，不可取消
- **EMBER_DUMMY 惡龍腳本**：固定 pattern [1,1,3,0]（吸氣、吸氣、噴火、無）
- **P2P 對戰**（PeerJS WebRTC）：邀請碼產生/加入，Host-Guest 非對稱結算
- **P2P 訊息集**：game_start / turn_start / action / ready_update / resolve / chat
- **LLM 接入（法師B）**：BYO API key，支援 Groq/OpenRouter，action + 台詞
- **對戰紀錄 + 戰報統計**：回合表格、雙閃/雙盾/雙補次數
- **手機 tab 版 UI**：規則 / 對戰 / 儀表，`@media max-width: 768px`
- **❓→✅→reveal 視覺節奏**：ready_update 同步 Host/龍的 ✅ 給 Guest
- `playwright_host.py`：自動化 Host 端，列印邀請碼等 Codex 加入

### 架構決策
- 純前端無後端，所有狀態在 browser JS 中，API key 存 localStorage
- Host 為唯一 source of truth，Guest 只送 action，不做本地結算
- WebLLM 路線擱置（移動端 WebGPU 不成熟）

---

## 2026-04-09 — 設計定案 + UI Mockup

- 確定同步回合制 + 詠唱承諾機制為核心設計
- WebLLM + WebGPU 技術選型（桌機優先）
- 靜態 UI Mockup 完成
- Qwen 模型本地跑通測試
