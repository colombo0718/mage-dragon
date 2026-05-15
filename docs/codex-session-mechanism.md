# Codex CLI Session 機制深探（2026-05-14）

> 改變 match.py 對 codex 定位的關鍵發現。
> 也對應 LL「Per-Agent 記憶軸」討論的現成範本。

---

## 三大關鍵能力

### 1. Session 持久化（預設開啟）

每次 `codex exec` 自動建立 session、印出 `session id: <UUID>`、寫進磁碟：

```
~/.codex/sessions/2026/MM/DD/rollout-*.jsonl  ← 完整對話記錄
~/.codex/session_index.jsonl                  ← 索引（id + thread_name + updated_at）
```

JSONL 內容：system prompt、AGENTS.md、user messages、assistant responses、tool calls、環境 context… **完整重建狀態所需的一切**。

要關掉持久化：`--ephemeral`。

### 2. Session Resume

```bash
codex exec resume <UUID> "新 prompt"
codex exec resume --last "新 prompt"     # 最近一次
codex exec resume --all                  # 列所有
```

實測：
- ✅ 完整繼承之前 session 的角色 / 規則 context
- ✅ Token 用量大降（39k → 17k）、不重複載入
- ❌ `--output-schema` flag 在 resume 不支援
- ⚠️ Resume 後輸出回到自然語言、原 session 的 schema 約束沒繼承

### 3. Output Schema 強制結構化輸出 ⭐

```bash
codex exec --output-schema schema.json "..."
```

`schema.json`：
```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["action", "reason"],
  "properties": {
    "action": {"type": "string", "enum": ["1","2","3"]},
    "reason": {"type": "string"}
  }
}
```

實測輸出（嚴格）：
```json
{"action":"1","reason":"沒吸氣訊息且雙方滿血、照規則先打輸出。"}
```

→ **這解決了「codex 不服 prompt 規則」的根本問題**。
→ 注意：schema 必須帶 `additionalProperties: false`（OpenAI structured output 規定）。

---

## 對 match.py 的設計含義

### 策略 A：每回合都 fresh session + schema（最穩、最貴）

```python
for turn in range(max_turns):
    state = get_state()
    prompt = format_full_prompt(state, rules_inline=True)
    r = subprocess.run([CODEX, "exec", "--output-schema", "action-schema.json",
                       "--ephemeral", prompt], ...)
    action = json.loads(r.stdout)["action"]
    submit(action)
```

- ✅ 嚴格 JSON、無解析錯誤
- ✅ 每場獨立、好 debug
- ❌ 每次塞完整規則 = 高 token 成本
- ❌ 沒累積記憶（codex 不知道自己上局怎麼玩）

### 策略 B：第一回合開 session + 後續 resume（省 token、有記憶、需 parse）

```python
# 第一回合
r = subprocess.run([CODEX, "exec", "--output-schema", "action-schema.json",
                   open_prompt], ...)
session_id = extract_session_id(r.stdout)
action = json.loads(r.stdout_json_part)["action"]

# 後續回合
for turn in range(...):
    r = subprocess.run([CODEX, "exec", "resume", session_id, state_text], ...)
    action = extract_action_from_text(r.stdout)  # 自然語言、需 parse
```

- ✅ Token 省 50-70%（resume context shared）
- ✅ Codex 有持續記憶、可能玩出長期策略
- ❌ Resume 輸出無 schema、要 parse 自然語言
- ❌ Session 越長 context 越大、未來可能爆窗

### 策略 C：混合（推薦）⭐

```
第一場：開 session + schema（穩定第一步）
後續場（同隊同 agent）：resume 同 session（累積戰局經驗）
每場開頭：附短摘要「上場我們輸在 T7、這次注意 X」
```

→ 把 codex 當成「**有戰績的選手**」、不是每場新生兒。
→ 對應 LL 「Per-Agent log + Match learning」軸。

---

## 對 LL 整體戰略含義 ⭐

### Codex sessions 是 LL Per-Agent 軸的現成範本

LL 規劃中的 Per-Agent 結構：
```
matrix-manager/memory/agents/<name>/
  ├── identity.md
  ├── stream-log/
  └── knowledge/
```

Codex 已經自己實作了類似的：
```
~/.codex/sessions/2026/MM/DD/rollout-*.jsonl     ← 等同 stream-log
~/.codex/session_index.jsonl                    ← 等同索引
config.toml + AGENTS.md                         ← 等同 identity
```

→ **不必從零造**、可參考 codex 的結構抄。
→ 但 codex 是「per-thread 記憶」、我們要「per-agent 持久記憶」、語意層不同。

### 對 mage-dragon match.py v2 的具體 todo

1. 加 `--output-schema` 到 codex 呼叫（強制 JSON）
2. 寫 schema 檔（`action-schema.json` 已建）
3. 加 `session_id` 管理（每場一個、累積戰績可選）
4. 解析 JSON 答案、不用 regex 找數字

---

## 對 gemini 的對等檢查（TODO）

- 找 gemini CLI 是否有同等 session / output schema 機制
- 如果沒有、考慮直接打 Gemini API
- 或限制 match.py 只支援有結構化輸出能力的 backend

---

## 一句話總結

```
今天意外發現：codex 不是 oracle、是有完整 session 記憶 + 結構化輸出能力的 agent。
之前 match.py 把它當 oracle 用、完全浪費了它的能力。
v2 match.py 加 schema + resume、codex 應該變競技場真實玩家、不是噪音來源。

順帶發現：codex sessions 結構幾乎就是 LL Per-Agent 軸的雛形、可直接參考。
```
