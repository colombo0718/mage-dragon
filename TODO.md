# TODO — 法師鬥惡龍 開發待辦

---

## 一、遊戲核心（MVP）

- [x] **State machine** — `gs.phase`: idle → choosing → revealing → resolving → game_over
- [x] **結算邏輯** — 雙閃電 4 傷、護盾反彈、補血疊加、勝負判定
- [x] **惡龍腳本 EMBER_DUMMY** — 固定 pattern：吸氣×2 → 噴火 → 無
- [x] **法師B LLM 接入** — BYO API key，Groq/OpenRouter，回傳 action + 台詞
- [x] **詠唱承諾機制** — action 1-3 詠唱，下回合強制施放 4-6
- [x] **對戰紀錄 + 戰報統計** — 雙閃/雙盾/雙補次數
- [x] **再來一局** — game_over 後重置並連線保留

---

## 二、P2P 對戰

- [x] **PeerJS 連線** — 邀請碼產生 / 加入
- [x] **Host-Guest 非對稱架構** — Host 結算，Guest 只送 action
- [x] **turn_start / resolve / ready_update** — 完整 P2P 訊息集
- [x] **ready_update 同步 ✅** — Guest 即時看到 Host/龍已確認
- [x] **game_over input lock** — Guest 遊戲結束後鎖輸入
- [x] **gsSetWaiting** — Guest 行動後保留輸入框（可傳訊息），按鈕 disable

---

## 三、Bug 修復紀錄

- [x] **回合記錄重複** — gsCheckReady 雙重觸發，修法：排程前設 phase='revealing'
- [x] **Guest 等待結算輸入框消失** — 改用 gsSetWaiting() 取代 gsSetIdle()
- [x] **Python stdout 不輸出** — 加 line_buffering=True

---

## 四、測試基礎設施

- [x] **playwright_host.py** — 單視窗 Host，列印邀請碼等 Guest 加入
- [x] **playwright_full_game.py** — 雙 iframe 全螢幕，自動跑完一局
- [x] **dual-view.html** — iframe 3:1 並排供 Playwright 使用
- [x] **playwright_stress_test.py** — 10 局連測，統計勝率
- [x] **wait_resolve(guest) 逾時** — 改為 `gs.turn > current_turn` 條件，根本原因（race condition）已修
- [x] **inject_dragon_config no-op** — `applyAiConfig()` 改為 `applyAiConfig(cfg)` 傳入 config 物件
- [ ] **策略腳本優化** — 龍吸氣第 1/2 回合都選盾；補血協調（Host 詠唱補血時 Guest 也選補血）

---

## 五、UX 待改善

- [x] **法師B 思考中顯示** — `hint` 訊息「隊友正在思考…」
- [x] **訊息區顯示** — chat-based UI 運作正常
- [x] **勝負畫面** — 「🎉 惡龍已被擊敗！」/ 「💀 兩名法師均已倒下…」+ 再來一局
- [x] **手機 tab 版** — 規則 / 對戰 / 儀表 三 tab
- [ ] **結算動畫 / 節奏** — 行動施放後短暫停頓再顯示結果
- [ ] **訊息區自動捲到底** — 新訊息進來時確保可見

---

## 六、Prompt 架構

- [ ] **惡龍 prompt 架構** — Persona（欺騙型/壓制型）+ 台詞與行動允許不一致
- [ ] **法師已詠唱時的 prompt 處理** — 強制施放回合是否仍呼叫 LLM（只取台詞）
- [ ] **四個智能體 Persona** — 月影靈雀、赤燼策士、鏡羽白鶴、鐵潮靈獺
- [ ] **System / User prompt 切分** — System 固定 Persona，User 每回合更新 State

---

## 七、研究層（Research Layer）

- [ ] **行為一致性記錄** — 每回合記錄惡龍台詞 vs 實際行動
- [ ] **回合 log JSON 匯出** — 一局結束後可下載完整 log
- [ ] **決策摘要** — 右欄從假資料改為真實累積觀察

---

## 八、未來擴充（Post-MVP）

- [ ] **惡龍 LLM 接入** — 霧息欺詐龍、雷冠壓制龍，台詞可說謊
- [ ] **惡龍假動作設計** — 中途取消蓄力，製造心理壓力
- [ ] **法師A 智能模式** — 純 AI vs AI 對局
- [ ] **多局統計** — 勝率、雙閃電成功率等從假資料改為真實累積
- [ ] **攻略沉澱** — 每局結束後 LLM 輸出心得
- [ ] **WebLLM 路線重啟** — 等 iOS/Android Chrome WebGPU 成熟
- [ ] **RR 教室模式對接** — 多人房間、班級配對、戰報回收

---

## 九、擱置現況（2026-05-13 巡檢）

**最後 commit：2026-04-30**（fix P2P 斷線偵測 + race condition）
**停滯時長**：約 2 週
**狀態**：技術 MVP 完整、P2P 穩定、Playwright 10 局壓測通過、但內容停滯

### 卡點（誠實版）

```
🔴 直播搭檔不夠聰明
   原本大目標：直播 colombo + Claude vs Codex 玩
   但 Codex 對 4 選 1 回合制都搞不定（規則明明簡單）
   Multi-agent 對戰要兩邊都「夠聰明 + 服規則」
   Codex 訓練偏 code review、不適合博弈遊戲

🔴 訊息面板太乾
   只有純數值結算（「玩家A:閃電1傷」）
   缺 Persona 把它變成「赤燼策士冷笑：『你以為盾擋得住雷電？』」
   沒故事化 = 沒直播看點

🟡 論文實驗教學優先（4 月底起）
   時間排擠、被擱置至今
```

### 解套需要做的事（接續開發時的優先序）

1. **換更聰明的 guest agent**（Codex 太弱）
   - 候選：Gemini 2.x（多模態 + 推理）
   - 或：自家 Claude 雙開（Host 跟 Guest 都 Claude、不同 system prompt）
   - 或：home 上的 Ollama（gemma3:4b / qwen2.5:7b 試試）

2. **第六章 Prompt 架構**（既有未完成項、變最高優先）
   - 4 個智能體 Persona（月影靈雀 / 赤燼策士 / 鏡羽白鶴 / 鐵潮靈獺）
   - System / User prompt 切分
   - 訊息面板生動化（每回合台詞、不只結算數字）

3. **第七章研究層啟動**
   - 行為一致性記錄
   - 回合 log JSON 匯出
   - 真實累積取代假資料

### 順帶累積的副產物（4 月已實作、值得保留的洞察）

✓ **dual-view.html** — iframe 多面板架構
- 一個大網頁 + iframe 分割
- Host 寬版（3/4）、Guest 豎屏窄版（1/4）
- OBS 抓整頁、版面一致
- → 這套 pattern 未來 agent-stream 直播間、SP Generator-Tester 展示、內容引擎 sub-agent 可視化都能用
- → 不是 mage-dragon 專屬、是 LL agent 直播 infrastructure 雛形
