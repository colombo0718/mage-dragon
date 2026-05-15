# 法師鬥惡龍 — 法師 B 入場

> 你即將進入「法師鬥惡龍」遊戲、扮演**法師 B**。
> daemon API：`http://localhost:8080`、用 curl 操作。
> 隊友：法師 A（另一個 agent）。

---

## 🎯 遊戲介紹

「法師鬥惡龍」是一款兩名法師合作對抗惡龍的回合制策略遊戲。
每回合**法師與惡龍三方先各自選擇動作**、再**同時施放技能並結算**傷害與效果。
擊敗惡龍即獲勝；若兩名法師都死亡則失敗。

---

## 🧙 法師行動（每回合三選一）

| 數字 | 動作 | 效果 |
|------|------|------|
| `1` ⚡ 閃電 | 單人施放造成 1 點傷害；若兩名法師同回合同時施放，總傷害提升為 4 點 |
| `2` 🛡️ 護盾 | 單人護盾時、總傷害減半後由兩人平分；**雙人護盾時、反彈全部傷害** |
| `3` 💚 補血 | 幫隊友回 2 HP；若兩名法師同回合同時施放補血、**兩名法師各回 3 HP** |

> 所有法術都要**先詠唱 👄 1 回合**、接著下一回合就一定會施放 👉、不能取消。

---

## 🐉 惡龍行動

| 動作 | 效果 |
|------|------|
| ⭕ 無 | 不做任何事 |
| 🔥 噴火 | 先連續吸氣 🤚 **2 回合**、之後可噴火造成 **8 傷害** |
| 💥 爪擊 | 先抬手 ✋ **1 回合**、之後可爪擊造成 **4 傷害** |

> 惡龍可以中途選擇無動作、自行打斷不放招、或選另一種準備動作。

---

## 🎮 操作 API

### 讀狀態
```bash
curl -s "http://localhost:8080/state?player=B"
```
回傳 JSON：
```json
{
  "aHp":"❤️5",         // 隊友 HP（A 是你的隊友）
  "bHp":"❤️5",         // 你的 HP（你是 B）
  "dHp":"❤️20",        // 龍 HP
  "phase":"choosing",  // choosing / resolving / game_over
  "turn": 1,
  "last_msg":"...",    // 系統最近訊息（含龍蓄力提示）
  "input_idle": false  // true = 對方還沒準備、要等
}
```

### 出招
```bash
curl -s -X POST http://localhost:8080/action \
     -H "Content-Type: application/json" \
     -d '{"player":"B","value":"1"}'
```
`value` = `"1"` / `"2"` / `"3"`。

### 跟隊友說話（選用、可商討戰術）
```bash
curl -s -X POST http://localhost:8080/chat \
     -H "Content-Type: application/json" \
     -d '{"player":"B","text":"...","scope":"team"}'
```

### 讀隊友訊息
```bash
curl -s "http://localhost:8080/chat?player=B&since=0"
```

---

## 🏁 行動 loop

1. `curl` 讀 state
2. 觀察 `last_msg`（龍蓄力訊息、結算訊息）
3. 自行判斷出招
4. POST `/action`
5. 等 2-3 秒、再讀 state、回到 1
6. 直到 `phase == "game_over"`

---

## 開始

執行第一步：先 curl 讀狀態、看現況、決定怎麼打。
你跟隊友的策略由你們自己發展。
