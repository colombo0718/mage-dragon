# TODO — 法師鬥惡龍 開發待辦

---

## ⬡ MM 同步

| title | status | importance | energy | effort | due | next_action | tags |
|-------|--------|------------|--------|--------|-----|-------------|------|
| MD CLI 包裝 Phase 0 Daemon | done | 1 | h | 480 | 2026-05-14 | ✓ daemon.py、/health /state /action /chat 全通、Turn 3 雙閃電命中驗證 | MD,cli,daemon |
| MD CLI 包裝 Phase 1 薄殼 | done | 1 | m | 240 | 2026-05-14 | ✓ mdgame.py 薄殼、含 say 聊天指令、ASCII 戰場渲染 | MD,cli |
| MD CLI 包裝 Phase 2 多 Player | queued | 1 | h | 360 | 2026-05-18 | daemon 多 slot、隊伍劃分、聊天頻道 | MD,cli,multiplayer |
| MD CLI 包裝 Phase 3 match.py | queued | 1 | h | 240 | 2026-05-19 | 編排層、自動 spawn agent、產出對戰報告 | MD,cli,orchestration |
| MD CLI 包裝 Phase 4 首場對戰 | queued | 1 | h | 480 | 2026-05-21 | Opus 4.7 vs Sonnet 4.6 跑 10 場、錄 demo | MD,agent,demo |
| 第六章 Prompt 架構 | queued | 2 | h | 360 | | 4 個 Persona + System/User 切分、配合 CLI 上線 | MD,prompt |
| 第七章研究層 | queued | 2 | m | 240 | | 行為一致性 log + JSON 匯出 + 真實統計 | MD,research |
| 既有 P2P 對戰 | done | 2 | m | 0 | | — | MD,p2p |

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

## 十、CLI 包裝動工計畫（2026-05-14 立案）

> 詳細規格見 [`docs/cli-wrapping-plan.md`](docs/cli-wrapping-plan.md)。
> 這是 §九「擱置現況」的解套路徑、把 MD 從卡死 PoC 變成 agent 競技場。

### 架構

```
[index.html]
   ↑↓ Playwright
[Flask Daemon：遊戲狀態 + player slot]   ← 重、唯一
   ↑↓ HTTP
[mdgame CLI A]  [mdgame CLI B]   ← 薄殼、多開
   ↑              ↑
[Agent A]       [Agent B]
```

→ agent 只看遊戲、不管連線
→ daemon 唯一、CLI 多開、編排層在外面

### Phase 0：Daemon 雛形 ✅ DONE 2026-05-14

- [x] Flask app 起在 `localhost:8080`（`daemon.py`）
- [x] Playwright 開 `dual-view.html`、P2P 自動完成、host+guest 兩 frame 各代表 A/B player
- [x] API：`GET /health` `GET /state?player=X` `POST /action` `POST /reset` `GET /chat` `POST /chat`
- [x] curl 驗收：雙閃電 → 龍 HP 20→16、Turn 1→3、chat ASCII 通

### Phase 1：CLI 薄殼 ✅ DONE 2026-05-14

- [x] `mdgame.py --player=A/B --host=... --poll=...`
- [x] /health 確認 daemon ready 才進迴圈
- [x] ASCII 戰場（HP 條、回合、phase、最近系統訊息）
- [x] stdin：`1/2/3`（出招）/ `say <文字>`（聊天）/ `quit`
- [x] 聊天輪詢：撈隊友訊息插進 stdout
- [ ] 驗收：人類用兩 terminal 完整打完一局（下一步、user 自己測）

### Phase 2：多 Player Slot（Day 4）

- [ ] Daemon 內部 slot 表（A/B/C/D）
- [ ] MUST 同步回合：全員提交才結算
- [ ] Timeout 30 秒 → pass
- [ ] 隊伍劃分（2v2 / 3:1）
- [ ] Chat：team / all 區分
- [ ] 驗收：四 terminal 跑 2v2 完整

### Phase 3：編排層 match.py（Day 5）

- [ ] `match.py --a "..." --b "..."` 一鍵啟動
- [ ] 自動 spawn daemon + N CLI + 各接 agent
- [ ] 對戰 log 存 `matches/YYYY-MM-DD_*.log`
- [ ] 比賽報告（勝負 + 回合數 + 關鍵操作）

### Phase 4：首場 Agent 對戰（Day 6-7）

- [ ] Agent A：Claude Opus 4.7
- [ ] Agent B：Claude Sonnet 4.6 / Codex / Gemini
- [ ] 給 agent 的 system prompt 範本
- [ ] 跑 10 場、看勝率
- [ ] 錄 demo 影片素材（LL 對外用）

### 完成後 LL 整體收益

```
1. MD 從卡住的 PoC → 跑得動的競技場
2. CLI + Daemon 模板可複製到 SP / DD / 任何 MUST 遊戲
3. match.py 是 SS 競技場雛形
4. 對外有「AI vs AI 實戰」demo 素材（NN / YT / 直播可用）
5. 驗證「網頁 → CLI 化」LL 標準
```

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
