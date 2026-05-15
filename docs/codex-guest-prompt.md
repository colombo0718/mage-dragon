# 任務：用 Playwright 加入一場瀏覽器遊戲，扮演法師B

## 遊戲背景
你要加入一款叫「法師鬥惡龍」的回合制遊戲，扮演**法師B（Guest）**。
對手（法師A / Host）是另一個 AI。你們要合作打倒惡龍。

## 遊戲 URL
```
file:///C:/Users/USER/mage-dragon/index.html
```

## 你的任務
1. 用 Playwright 打開上面的 URL
2. 展開右欄「🔗 連線對戰」
3. 在「輸入邀請碼加入」欄位填入給你的邀請碼
4. 按「加入」按鈕
5. 等待連線成功（狀態欄顯示「✅ 已連線！」）
6. 遊戲開始後，每回合收到提示就輸入你的選擇

## 遊戲規則

**你可以選擇（輸入 0-3）：**
- `0` = ⭕ 無動作
- `1` = ⚡ 詠唱閃電（下回合施放，造成傷害：單人1傷、雙人4傷）
- `2` = 🛡️ 詠唱護盾（下回合施放：單人傷害減半、雙盾完全反彈）
- `3` = 💚 詠唱補血（下回合施放：補隊友2HP、雙補各3HP）

**重要機制：**
- 選好招後下回合**強制施放**，不能取消
- 若你正在詠唱中（提示說「即將施放」），本回合**不需要輸入**，系統自動處理

**惡龍攻擊：**
- 🔥 噴火：吸氣2回合後，造成8傷（兩人各4）
- 💥 爪擊：抬手1回合後，造成4傷（打一人）
- 龍會製造假動作——有時吸氣後不噴火

**勝負：**
- 兩名法師HP都歸零 → 失敗
- 惡龍HP歸零 → 勝利

## 策略建議
- 看訊息區的提示（💡），了解現在龍在做什麼
- 龍吸氣第2回合時：計畫本回合詠唱護盾（這樣下回合才能擋火）
- 龍沒在蓄力時：詠唱閃電，希望跟隊友雙閃
- 可以輸入文字訊息跟隊友溝通（不是數字的輸入就是對話）

## Playwright 操作說明

```python
from playwright.sync_api import sync_playwright

INVITE_CODE = "XXXXXX"  # 填入給你的邀請碼

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, slow_mo=400)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto("file:///C:/Users/USER/mage-dragon/index.html")
    page.wait_for_load_state("domcontentloaded")

    # 展開連線對戰
    page.click("details:has(summary:text('連線對戰'))")
    page.wait_for_timeout(300)

    # 填邀請碼並加入
    page.fill("#invite-code-in", INVITE_CODE)
    page.click("#join-game")

    # 等待連線成功
    page.wait_for_function(
        "() => document.getElementById('invite-status')?.textContent?.includes('✅')",
        timeout=20000)
    print("已連線！")

    # 遊戲迴圈
    for turn in range(1, 20):
        # 等輸入欄 active（可以輸入）
        try:
            page.wait_for_function(
                "() => !document.getElementById('input-bar').classList.contains('idle')",
                timeout=20000)
        except:
            break  # 遊戲結束

        # 讀取當前狀態，決定出招
        hint = page.evaluate(
            "() => [...document.querySelectorAll('.hint-msg .msg-text')]"
            ".at(-1)?.textContent ?? ''")
        
        if "即將施放" in hint:
            # 強制施放，等結算
            page.wait_for_timeout(2000)
            continue

        # 讀龍最後一條系統訊息，決定策略
        last_sys = page.evaluate(
            "() => [...document.querySelectorAll('.system-msg .msg-text')]"
            ".at(-1)?.textContent ?? ''")
        
        # 簡單策略：龍在吸氣第2回合 → 盾；否則閃電
        if "第 2 回合" in last_sys or "吸氣" in last_sys:
            choice = "2"  # 護盾
        else:
            choice = "1"  # 閃電

        print(f"回合 {turn}：選 {choice}（{last_sys[:30]}）")
        page.fill("#player-input", choice)
        page.click("#player-send")

        # 等結算
        page.wait_for_function(
            "() => { const s = document.getElementById('dragon-skill')?.textContent;"
            "return s && s !== '❓' && s !== '✅'; }",
            timeout=25000)
        page.wait_for_timeout(600)

    page.wait_for_timeout(3000)
    browser.close()
```

## 注意事項
- 如果「即將施放」出現在提示裡，本回合不需要輸入任何招式，系統自動處理
- 輸入框裡輸入**數字**是出招，輸入**文字**是傳訊息給隊友
- 遊戲結束（惡龍死亡或兩人全滅）後輸入欄會變回按鈕狀態，退出迴圈即可
