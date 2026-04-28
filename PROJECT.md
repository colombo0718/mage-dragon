# PROJECT.md — Mage vs Dragon 專案背景

---

## 這個專案是什麼

**法師鬥惡龍 Mage vs Dragon** — 兩名法師合作對抗惡龍的同步回合制遊戲。
核心特點：LLM 同時負責遊戲決策 + 角色扮演 + 作為研究對象。

隸屬 **LeafLune 宇宙**，與 Shadow Protocol 同屬「玄機界域 SS」品牌，
但定位是獨立的輕量 LLM 實驗專案。

---

## 三層目標

1. **Game Layer** — 規則極簡的同步回合制遊戲，能跑通就是 MVP
2. **Roleplay Layer** — LLM 扮演隊友（策略分析）和惡龍（威脅台詞、場面描繪）
3. **Research Layer** — 觀察 LLM 在承諾機制 + 博弈壓力下是否出現「說一套做一套」的行為

---

## 遊戲規則摘要

**法師（4 選 1，詠唱 1 回合後強制施放，不可取消）：**
- ⭕ 無
- ⚡ 閃電：單人 1 傷；雙人同時 → 4 傷
- 🛡️ 護盾：單人傷害減半；雙人 → 反彈全傷
- 💚 補血：隊友回 2HP；雙人同時 → 各回 3HP

**惡龍（可中途取消蓄力，製造假動作）：**
- ⭕ 無
- 🔥 噴火：吸氣 👃×2 → 8 傷
- 💥 爪擊：抬手 ✋×1 → 4 傷

詠唱承諾機制是核心設計，**不要拿掉**——沒有它法師變成純反應遊戲，協調問題消失。

---

## 技術架構

目標：**純前端，無後端**

**現行 MVP 路線：BYO API Key**
- 玩家自備 provider / model / API key（Groq、OpenRouter、Gemini 等）
- 設定存 localStorage，不寫進任何後端
- 前台包成 chat-based UX，底層是 prompt-based system

**WebLLM 路線（擱置）：**
- `webllm-demo.html` 已可在桌機 Chrome 跑 Qwen2.5 系列
- 擱置原因：移動端 WebGPU 支援不足，教室平板無法使用
- 等 iOS/Android Chrome WebGPU 成熟後再推進

---

## 現狀（2026-04-29 更新）

### 主要檔案

| 檔案 | 狀態 | 說明 |
|------|------|------|
| `index.html` | ✅ 可玩 MVP | 完整遊戲邏輯 + P2P 對戰 + LLM 接入 |
| `dual-view.html` | ✅ 測試用 | iframe 3:1 並排，供 Playwright 自動測試 |
| `playwright_full_game.py` | ✅ 可用 | 單視窗雙 iframe，自動跑完一局 |
| `playwright_stress_test.py` | 🔧 調試中 | 10 局壓力測試，`wait_resolve(guest)` 仍有逾時問題 |
| `llm-provider-chat.html` | ✅ | BYO API key 的 chat demo |
| `webllm-demo.html` | ✅ 擱置 | WebLLM 桌機 Chrome demo |

### 已實作的核心功能

**Game Layer：**
- State machine：`gs.phase` = idle → choosing → revealing → resolving → game_over
- MAGE_STATES / DRAGON_STATES emoji 對照表
- 詠唱承諾機制：法師行動 0→3（詠唱）→ 4→6（施放），不可取消
- 惡龍固定腳本 `EMBER_DUMMY = [1,1,3,0]`（吸氣、吸氣、噴火、無）
- 傷害結算邏輯：雙閃電 4 傷、護盾反彈、補血疊加
- 勝負判定 + 再來一局
- 對戰紀錄 + 戰報統計（雙閃、雙盾、雙補次數）

**P2P 對戰（WebRTC via PeerJS）：**
- Host 產生邀請碼，Guest 輸入加入
- `p2pRole = 'host' | 'guest'` 分流控制
- Host 負責結算，透過 P2P 同步 resolve 結果給 Guest
- 強制施放 / 死亡自動出招
- `ready_update` 訊息讓 Guest 即時看到 Host/龍的 ✅
- Guest 行動後進入「等待結算」：輸入框保留（可傳訊息），按鈕 disable

**LLM 接入（法師B）：**
- BYO API key：支援 Groq、OpenRouter 等 provider
- Prompt 帶入當前 HP、行動狀態、惡龍狀態
- LLM 回傳 action + 台詞，台詞顯示為訊息泡

**UX：**
- 三欄桌機版：規則 / 對戰 / 儀表
- 手機版 tab 切換（`@media max-width: 768px`）
- ❓ → ✅ → 真實 emoji 的視覺節奏
- Guest 等待結算：按鈕文字改為「等待結算…」（disabled），input 保留供傳訊

---

## 關鍵設計決策與已知坑

### ❓→✅→reveal 節奏
- ❓ = 尚未決定，✅ = 已決定（對手不知道是什麼），reveal 才顯示真實 emoji
- 這是核心設計，不要修改 dragon-skill 在 input 階段的顯示邏輯

### gsCheckReady 雙重觸發 bug（已修）
- 當法師A 和法師B 同時強制施放時，`gsTurnStart` 會連呼叫兩次 `gsCheckReady`
- 修法：`gsCheckReady` 排定 reveal 前先將 `gs.phase` 改為 `'revealing'`，防止第二次排程

### wait_resolve(guest) 逾時（調查中）
- `playwright_stress_test.py` 的 `wait_resolve(guest)` 偶爾 40 秒逾時
- Guest 的 dragon-skill 更新依賴 P2P 'resolve' 訊息，可能在某些情況下未觸發 UI 更新
- 尚未找到根本原因

### P2P 信令伺服器連線限制
- PeerJS 免費公用伺服器偶爾不穩，等待中可能斷開
- Host 產生邀請碼後盡快讓 Guest 加入

### slow_mo 與 iframe frame 操作
- Playwright 的 `slow_mo` 不影響 `wait_for_function` polling 頻率
- 使用 `page.frame(name="host/guest")` 取 iframe frame 物件，API 與 Page 相同

---

## 開發規範

- Commit 語言：中文或英文均可，訊息格式 `type: description`
- 避免大改的理由：詠唱承諾機制是研究核心，state machine 邏輯穩定後不要輕易重構
- `.env` 已加入 `.gitignore`，Groq API key 僅本機存放
