# 連線對戰實作規劃

---

## 一、技術選型

**PeerJS（公共信令伺服器）** → MVP 階段用，不需自架後端。

```
法師A 瀏覽器  ←──── PeerJS 信令 ────→  法師B 瀏覽器
       ↑                                      ↑
   建立邀請碼                           輸入邀請碼加入
       └──────────── WebRTC DataChannel ──────┘
                    （連線建立後 P2P 直連）
```

PeerJS 把 WebRTC 的 SDP 交換、ICE candidate 包好，只需要：
```js
const peer = new Peer(roomId);          // 房主
const peer = new Peer();                // 客人
conn = peer.connect(roomId);            // 客人連過去
```

---

## 二、角色定義

| 角色 | 誰 | 法師 |
|------|----|------|
| 房主（Host） | 先產生邀請碼的玩家 | 法師A |
| 客人（Guest） | 輸入邀請碼加入的玩家 | 法師B |

- 房主控制遊戲主邏輯（state machine、結算、龍腳本）
- 客人每回合只傳一個數字（action input）給房主
- 房主結算後把新 state 廣播給客人，客人更新畫面

---

## 三、訊息協議

所有訊息都是 JSON，有 `type` 欄位。

### 客人 → 房主

```js
{ type: 'action', value: 2 }           // 客人選的招式 0~3
{ type: 'chat', text: '一起開盾！' }    // 對話訊息
```

### 房主 → 客人

```js
{ type: 'state', gs: { ... } }         // 完整 state（每回合結算後）
{ type: 'turn_start', turn: 5 }        // 回合開始，可以輸入了
{ type: 'chat', text: '...',
  from: 'host' }                        // 對話訊息
{ type: 'game_over', result: 'win' }   // 遊戲結束
```

### 為什麼不讓客人也跑結算？

結算邏輯只跑在房主端，避免雙方狀態不同步。客人只渲染房主傳來的 state。

---

## 四、回合流程（連線模式）

```
房主回合開始
  ├─ 房主選招（輸入 0~3）
  ├─ 傳 { type: 'turn_start' } 給客人
  ├─ 客人選招，傳 { type: 'action', value } 給房主
  ├─ 房主等到收到客人 action（或 timeout 用 0）
  ├─ 龍決定（腳本 or LLM）
  └─ 房主結算 → 傳 { type: 'state', gs } 給客人
       └─ 客人更新畫面
```

---

## 五、連線狀態機

```
disconnected
    │ 產生邀請碼
    ▼
hosting（等待客人）
    │ 客人連進來
    ▼
connected
    │ 遊戲結束 / 斷線
    ▼
disconnected
```

```
disconnected
    │ 輸入邀請碼，按加入
    ▼
joining（嘗試連線）
    │ 連線成功
    ▼
connected
```

---

## 六、UI 狀態對應

| 連線狀態 | 邀請碼欄位 | 狀態文字 | 法師B 模式 |
|---------|-----------|---------|-----------|
| disconnected | 可操作 | — | 智能 / 連線 皆可選 |
| hosting | 顯示邀請碼（唯讀） | 等待對手加入… | 自動切換成「連線」並鎖定 |
| joining | 輸入碼唯讀 | 連線中… | 同上 |
| connected | 全部鎖定 | 已連線：{對手名稱} ✅ | 鎖定「連線」 |

---

## 七、斷線處理

- 連線中斷：顯示「對手已離線」，暫停遊戲，等待重連（PeerJS 有 reconnect）
- Timeout：客人 10 秒未回傳 action → 視為出 0（無動作），繼續結算
- 頁面重整：連線重置，需重新配對

---

## 八、實作順序

1. **引入 PeerJS CDN**
   ```html
   <script src="https://unpkg.com/peerjs@1/dist/peerjs.min.js"></script>
   ```

2. **`p2pInit()`** — 建立 Peer 物件、綁定事件（open / connection / data / error / close）

3. **`p2pHost()`** — 以邀請碼為 Peer ID，等待連線；更新 UI 狀態

4. **`p2pJoin(code)`** — 連進指定 Peer ID；更新 UI 狀態

5. **`p2pSend(msg)`** — 包裝 `conn.send(JSON.stringify(msg))`

6. **`p2pOnData(msg)`** — 收到訊息的 dispatch（依 type 分流）

7. **修改 `gsTurnStart()`** — 若連線模式，法師B 等 P2P action 而非 LLM/隨機

8. **修改 `gsReveal()` 結算後** — 房主廣播新 state 給客人

9. **客人端 `gsApplyRemoteState(gs)`** — 收到 state 後更新畫面

10. **聊天整合** — 玩家文字訊息透過 P2P 廣播，顯示在對方的 message-card

---

## 九、已知限制（MVP 範圍外）

- PeerJS 公共信令伺服器有流量限制，大量同時連線不穩定
- 不支援觀戰模式
- 不支援中途換人（斷線即結束）
- 沒有 TURN server → 少數網路環境（企業防火牆）P2P 可能打洞失敗
