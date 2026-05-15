# State Machine 設計計劃（v2）

---

## 一、State 結構

每個角色只有兩個維度：HP + 動作狀態。

```js
const state = {
    turn: 0,

    mageA: { hp: 5, action: 0 },
    mageB: { hp: 5, action: 0 },
    dragon: { hp: 20, action: 0, chargeTurns: 0 },
    //              ↑ chargeTurns 是實作細節，不是概念狀態

    stats: { wins: 0, losses: 0, doubledLightning: 0, doubledShield: 0, doubledHeal: 0 }
};
```

---

## 二、動作狀態編號

> 👄 = 詠唱中（已承諾，下回合強制施放）  
> 👉 = 施放中（本回合生效，已打出去）

### 法師（0~6）

| 編號 | 顯示 | 說明 |
|------|------|------|
| 0 | ⭕⭕ | 無動作 |
| 1 | 👄⚡ | 詠唱閃電，下回合強制施放 |
| 2 | 👄🛡️ | 詠唱護盾，下回合強制施放 |
| 3 | 👄💚 | 詠唱補血，下回合強制施放 |
| 4 | 👉⚡ | 施放閃電，本回合生效 |
| 5 | 👉🛡️ | 施放護盾，本回合生效 |
| 6 | 👉💚 | 施放補血，本回合生效 |

### 惡龍（0~4）

| 編號 | 顯示 | 說明 |
|------|------|------|
| 0 | ⭕ | 無動作 |
| 1 | 👃 | 吸氣，蓄力中（fire） |
| 2 | ✋ | 抬手，蓄力中（claw） |
| 3 | 🔥 | 噴火，本回合施放 |
| 4 | 💥 | 爪擊，本回合施放 |

---

## 三、每回合可選的 action（輸入）

### 法師（0~3）

玩家每回合輸入一個數字，**不一定等於下回合的狀態**：

```
input → 下回合 mage.action
  若當前 action ∈ {1,2,3}（詠唱中）：input 無效，下回合強制 = action+3（施法）
  若當前 action ∈ {0,4,5,6}：input 0→0，1→1，2→2，3→3
```

例：本回合 action=1（詠唱⚡），不管輸入什麼 → 下回合 action=4（施法⚡）

### 惡龍（腳本/LLM 選 0~4）

龍的選擇直接等於下回合的 action，但有特殊效果：

| 條件 | 效果 |
|------|------|
| action=1 連續 3 回合以上再選 3（噴火）| 龍自損 2 HP，噴火傷害仍 8 |
| 未吸滿 2 回合就選 3（噴火）| 噴火不造成傷害 |
| 未抬手直接選 4（爪擊）| 爪擊不造成傷害 |

---

## 四、結算邏輯

結算時看 **當前 action**，不看 input：

### 法師傷害輸出（施法⚡）

| mageA.action | mageB.action | 龍受傷 |
|---|---|---|
| 4 | 4 | 4 |
| 4 | 其他 | 1 |
| 其他 | 4 | 1 |

### 惡龍傷害輸入（噴火=8，爪擊=4，全體平分）

| mageA.action | mageB.action | 結果 |
|---|---|---|
| 5 | 5 | 全反彈給龍，法師不受傷 |
| 5 | 其他 或 其他 | 5 | 傷害減半，兩人各承受一半 |
| 其他 | 其他 | 兩人各承受一半 |

### 補血（施法💚 = action 6）

| mageA.action | mageB.action | 效果 |
|---|---|---|
| 6 | 6 | 各回 3 HP |
| 6 | 其他 | B 回 2 HP |
| 其他 | 6 | A 回 2 HP |

> HP 上限 5，不可超過。

---

## 五、回合流程

```
1. 顯示當前 state，提示玩家輸入
2. 收集所有 action input（法師A：玩家；法師B：LLM/連線；龍：腳本/LLM）
3. 計算下回合 state（依轉換規則）
4. 結算傷害與效果（依當前 action）
5. 更新 HP、chargeTurns、stats
6. 寫入對戰紀錄一列
7. 判斷勝負 → 結束 or 進下一回合
```

---

## 六、惡龍腳本（木樁烈焰龍）

固定 nextAction 序列，每回合讀下一個值：

```js
const emberDummyScript = [1, 1, 3, 0, 1, 1, 3, 0, ...];
// 吸氣 → 吸氣 → 噴火 → 無 → 重複
```

---

## 七、實作順序

1. `initState()` + 畫面初始化
2. `nextMageAction(mage, input)` → 回傳下回合 action
3. `dragonScript()` → 回傳龍的 nextAction
4. `resolve(state)` → 純函式，回傳結算後的新 state
5. `renderState(state)` → 更新畫面所有元素
6. `appendLog(state, prevState)` → 寫入對戰紀錄一列
7. `checkGameOver(state)` → 回傳 null | "win" | "lose"
8. 主迴圈串起以上函式
