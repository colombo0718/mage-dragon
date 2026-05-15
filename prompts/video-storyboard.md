# MD 法師鬥惡龍 — 影片分鏡 prompt

> 4-clip 分鏡：**失敗 → 領悟 → 反殺** 三幕結構
> 採 Anchor + Beat 雙層 prompt 設計、跨 clip 一致性最佳化
> 模型適用：Sora 2 / Veo 3（首選）、Kling 2.1 / Hailuo（中文版）、Runway / 開源（簡化版）

---

## 結構說明

```
每個 clip 的 prompt = Part 0（錨點、不動）+ Beat N（場景、變）

Part 0 鎖角色 + 世界 + 風格、確保跨 clip 一致性
Beat 描述當下動作 + 鏡頭 + 音效

進階：搭配 image-to-video 用 first frame 影像錨點、一致性更高
```

---

## 🎬 Part 0 — 錨點（每個 clip 都帶）

### 英文版（Sora 2 / Veo 3 / Runway）

```
[CHARACTERS]
TWO WIZARDS standing as a team:
- BLUE WIZARD: tall, hooded deep blue robe with silver trim,
  grey beard, gnarled wooden staff topped with crackling
  sapphire-blue lightning, channeling electric magic.
  Stance: aggressive, staff forward.
- CRIMSON WIZARD: shorter, hooded scarlet/crimson robe with
  gold trim, clean-shaven, dark wooden staff, summons
  emerald-green circular runes from his outstretched palm.
  Stance: defensive, palm forward.

DRAGON: colossal, hulking black-scaled armored dragon,
glowing molten lava cracks across body and chest,
spike crown and ridge horns, massive bat wings,
smoldering red eyes, breathes orange-white searing fire.

[WORLD]
Battlefield at night, smoldering ruins of war banners and
broken weapons, thick ash falling, embers swirling, sky a
deep stormy crimson with flickering storm clouds, scattered
fires illuminating the ground.

[STYLE]
Dark fantasy painterly photoreal cinematic style.
Dramatic high-contrast lighting with strong rim light.
Volumetric smoke and embers. Cinematic depth of field.
Color palette: deep blacks, crimson, ember orange,
electric blue, emerald green.

[CAMERA & VFX]
Cinematic motion, deliberate camera moves. Particle effects
on every spell. Slow-motion for impact moments.
No anime style, no cartoon. Photoreal painterly.
```

### 中文版（Kling 2.1 / Hailuo / MiniMax）

```
【角色】
兩名法師組隊：
- 藍袍法師：高挑、戴兜帽、深藍長袍配銀邊、灰白鬍鬚、
  扭曲木杖頂端凝聚電光、藍色閃電法術。姿態：進攻、杖前。
- 紅袍法師：較矮、戴兜帽、緋紅長袍配金邊、淨面、
  深色木杖、伸掌召喚翡翠綠圓形符文。姿態：防禦、掌前。

惡龍：巨型黑甲龍、軀幹胸口透出熔岩裂痕、頭頂尖冠脊角、
巨大蝙蝠翼、燃燒紅瞳、口噴橘白色炙焰。

【世界】
夜晚戰場、焚毀的戰旗與斷裂武器殘骸、厚重灰燼飄落、
火星旋繞、暗紅暴風雲翻騰、地面散落火堆映照。

【風格】
陰暗奇幻繪畫感寫實電影風。強反差光、強邊緣光、
體積煙霧與火星、電影級景深。
配色：深黑、緋紅、火星橘、電光藍、翡翠綠。

【鏡頭與特效】
電影級運鏡、刻意的鏡頭運動。每個法術帶粒子特效。
衝擊瞬間用慢動作。非動畫風、非卡通。繪畫感寫實。
```

---

## 🎥 Beat 1 — Dragon's Wrath（5-6 秒）

### 英文（拼接 Part 0 在前）

```
SCENE: The DRAGON rears up and unleashes a thunderous roar.
Wings spread wide, blocking the crimson sky. Shockwave of
heat and ash rolls outward. Sparks swirl violently.
CAMERA: low-angle pull-back, slow dolly out.
DURATION: 5 seconds.
SOUND: deep guttural dragon roar, distant thunder rumble.
```

### 中文

```
場景：惡龍立起身軀、發出震耳咆嘯。雙翼展開遮蔽暗紅天空。
熱浪與灰燼向外滾動。火星劇烈旋繞。
鏡頭：低角度仰拍、緩慢後拉。
時長：5 秒。
音效：低沉龍吼、遠方雷鳴。
```

---

## 🎥 Beat 2 — Failed Synergy 不同步失敗（6-8 秒）

### 英文

```
SCENE: Wide cinematic shot. The BLUE WIZARD raises his staff,
channeling a brilliant lightning bolt at the dragon — it
fizzles against the scales for minimal effect. The CRIMSON
WIZARD summons an emerald shield in front of HIMSELF ONLY,
not extending it to his teammate. The dragon exhales a
torrent of orange-white fire that sweeps across both wizards.
The blue wizard's lightning crackles uselessly. Both wizards
are blown back, scorched, robes smoldering, knees buckling.
Smoke and embers everywhere.
CAMERA: medium-wide, slow dolly-in to capture both.
DURATION: 7 seconds.
SOUND: lightning crack, fire roar, robes tearing, bodies
hitting ground.
```

### 中文

```
場景：寬景電影鏡頭。藍袍法師舉杖凝聚一道閃亮閃電劈向惡龍 —
打在龍鱗上幾乎無效。紅袍法師只在自己身前召喚翡翠綠魔法盾、
未延伸給隊友。惡龍吐出橘白色烈焰覆蓋兩人。藍袍的閃電無力散去。
兩人被火焰震退、衣袍焦黑、跪倒在地。煙霧火星瀰漫。
鏡頭：中寬景、緩慢推近、同時捕捉雙人。
時長：7 秒。
音效：閃電炸裂、火焰咆嘯、衣袍撕裂、身體著地。
```

---

## 🎥 Beat 3 — The Wordless Pact 默契浮現（4-5 秒）

### 英文

```
SCENE: Extreme close-up. Both wizards kneeling in burning
debris. The BLUE WIZARD, blood on his cheek, slowly turns his
head. The CRIMSON WIZARD, panting, meets his eyes. A heartbeat.
Time slows. A shared, wordless understanding crystallizes in
their gaze. The blue wizard nods almost imperceptibly. The
crimson wizard tightens his grip on his staff. Embers float
in slow motion between them.
CAMERA: tight close-up, slow rack focus blue→crimson, shallow DoF.
DURATION: 5 seconds.
SOUND: heavy breath, distant ambient roar, soft heartbeat thump.
```

### 中文

```
場景：極特寫。兩名法師跪在燃燒的廢墟上。藍袍法師臉頰流血、
緩緩轉頭。紅袍法師喘息著與他四目相對。一拍心跳。時間放慢。
眼神中浮現無聲的默契。藍袍法師幾乎不可察地點頭。紅袍法師
握緊法杖。火星在兩人之間慢動作飄浮。
鏡頭：特寫、緩慢拉焦從藍到紅、淺景深。
時長：5 秒。
音效：沉重呼吸、遠處龍吼回響、輕微心跳聲。
```

---

## 🎥 Beat 4 — Double Shield Reversal 雙盾反殺（6-8 秒）

### 英文

```
SCENE: Both wizards rise in PERFECT UNISON, staffs slamming
the ground simultaneously. Twin radiant shields — sapphire-blue
and emerald-green — burst into existence in front of each, then
EXPAND and FUSE into one colossal dome of crackling magical light.
The DRAGON unleashes its full fire breath; the dome catches the
inferno, holds it for a heartbeat, then VIOLENTLY reflects it
backward as a concentrated lance of white-hot energy. The
reversed firestream slams the dragon's chest, breaks through
scales. The dragon roars in agony and collapses backward in a
shower of embers and shattered armor.
CAMERA: epic sweeping wide shot, slow-motion impact, shockwave
ripple effect across screen.
DURATION: 7 seconds.
SOUND: synchronized staff stomp, magical surge crescendo,
dragon's pained roar, shattering crystalline impact.
```

### 中文

```
場景：兩名法師完美同步起身、法杖頓地。青藍與翡翠綠雙盾在身前
迸發、隨後擴張融合成一個巨大的魔法光罩。惡龍噴出滿口烈焰、
撞上光罩、停滯一拍、然後被猛烈反彈回去成為一道白熱光柱、
貫穿龍胸、擊碎鱗甲。惡龍痛吼倒地、餘燼與碎甲飛濺。
鏡頭：史詩級寬景橫掃、慢動作衝擊、全螢幕震波擴散效果。
時長：7 秒。
音效：法杖頓地同步聲、魔法湧現的漸強樂、惡龍痛苦咆嘯、
水晶破碎般的衝擊聲。
```

---

## 📐 影片規格（比例 / 解析度 / 幀率）

### 本專案推薦規格

```
主版本（YouTube / 對外宣傳片）：
  ─ 比例：16:9（橫向、電影感、雙人 + 龍同框最佳）
  ─ 解析度：1920×1080（1080p）
  ─ 幀率：24 fps（電影標準、最戲劇感）
  ─ Codec：H.264 / MP4
  
短影音版本（YT Shorts / TikTok / IG Reels）：
  ─ 比例：9:16（直向）
  ─ 解析度：1080×1920
  ─ 幀率：30 fps（短影音慣例）
  ─ 重點 reframe：Beat 3 特寫直接適配、Beat 1/4 須裁切龍翼
  ─ 長度上限：60 秒（Shorts）/ 90 秒（Reels）

正方形版本（IG Feed / 預覽）：
  ─ 比例：1:1
  ─ 解析度：1080×1080
  ─ 用途：縮圖 / 預告卡
  ─ 不建議全片、構圖太擠
```

→ **首推 16:9 1080p 24fps 主版本、再 reframe 出 9:16 短影音版**。

### 各模型支援的規格上限（2026-05）

| 模型 | 預設比例 | 解析度上限 | 幀率 | 單 clip 長度 | 自訂比例 |
|------|---------|-----------|------|-----------|---------|
| **Sora 2** | 16:9 | 1080p（Pro 4K）| 24/30 fps | 20 秒（Pro 60s）| 16:9 / 9:16 / 1:1 |
| **Veo 3** | 16:9 | 1080p | 24 fps | 8 秒 | 16:9 / 9:16 |
| **Kling 2.1** | 16:9 | 1080p | 30 fps | 10 秒（Pro 2 分鐘）| 16:9 / 9:16 / 1:1 |
| **Runway Gen-4** | 16:9 | 720p（Alpha 1080p）| 24 fps | 16 秒 | 多種 |
| **Hailuo** | 9:16 / 16:9 | 1280×720 | 25 fps | 6 秒 | 16:9 / 9:16 |
| **LTX-Video（home）** | 自訂 | 768×512（6GB 上限）| 24 fps | 5 秒 | 任意 |
| **HunyuanVideo（24GB+）** | 自訂 | 1280×720 | 24 fps | 5 秒 | 任意 |

→ **本專案 Sora 2 / Veo 3 / Kling 都能滿足 16:9 1080p 24fps**。
→ Veo 3 / Hailuo 單 clip 上限 6-8 秒、剛好對應我們 Beat 1-4 的 5-7 秒設計。

### Prompt 內怎麼指定（各模型方式）

```
Sora 2：UI 下拉選單選 ratio + resolution、prompt 內可加 "16:9 cinematic"
Veo 3：UI 設定 aspectRatio 參數、prompt 強化"widescreen cinematic"
Kling：UI 選比例、prompt 內可加「電影寬螢幕」
Runway：UI 選 aspect + Director Mode 鎖定
ComfyUI：節點直接設 width / height、注意比例
```

### 在 prompt 末尾加這行強化（可選）

英文版：
```
ASPECT: 16:9 widescreen cinematic.
RESOLUTION: 1080p.
FRAME RATE: 24 fps cinematic.
```

中文版：
```
比例：16:9 寬螢幕電影感。
解析度：1080p。
幀率：24 fps 電影感。
```

→ 即使 UI 已設、寫進 prompt 雙重保險、避免模型默選 9:16。

---

## 🛠️ 模型使用備註

### Sora 2 / Veo 3（最強、首選）

```
✓ 接受長 prompt、Part 0 + Beat 全文丟最好
✓ 多次提到的角色 = 一致性更高
✓ Part 0 放最前面、Beat 放最後
✓ 上限約 ~500 字、超過會被截
✓ Veo 3 額外好處：自帶音效生成、SOUND 描述會被自動配
```

### Kling 2.1 / Hailuo（中文版好用、免費 tier）

```
🟡 prompt 太長會迷失、容易抓主詞混亂
🟡 建議：Part 0 精簡到 100 字內（只留 character + style）
🟡 Beat 寫前、不要堆細節
🟡 中文 prompt 比英文穩
🟡 免費 quota：每天 6 個 clip、足夠 4-clip storyboard
```

### Runway Gen-4

```
✓ 支援 Reference Image 上傳（取代部分 Part 0）
✓ Director Mode 可分 shot
✓ 建議：Part 0 + 一張角色定錨圖（如本專案 cover.jpg）
```

### 開源（LTX-Video / Wan / HunyuanVideo）

```
🟡 prompt 不能太長、會 OOM
🟡 建議：Part 0 跟 Beat 各壓到 50 字內
🟡 i2v 模式下「first frame image」就是角色錨、文字 Part 0 可省
🟡 home 6GB VRAM：用 LTX-Video FP8 量化版 / Wan 2.1 1.3B
```

---

## 🎯 進階：i2v + Part 0 雙錨點

```
最強做法（模型支援 image-to-video 時）：

1. 用本專案 cover.jpg / 概念圖當 Beat 1 的 first frame
   ─ AI 鎖定該圖中的人物 / 龍面貌
2. Beat 2-4 用 Beat 1 的「最後一幀」當 first frame
   ─ 角色延續性接近 95%
3. 仍寫 Part 0 文字錨點（補強）
   ─ 文字 + 影像雙重綁定

實作：
  Sora 2 / Veo 3：上傳「starting image」+ prompt
  Runway：上傳「reference」+ prompt
  ComfyUI：i2v workflow + CLIP prompt 兩個輸入
```

---

## 💰 預算估算

```
最低成本路線：
  1. Kling 2.1 免費 tier 試 4 clips（0 元）
  2. 不滿意 → 同 prompt 丟 Hailuo（也免費）
  3. 還不滿意 → 升級 Sora 2 / Veo 3 付費版（$5-15/clip）
  
最高品質路線：
  Sora 2 Pro 或 Veo 3、每 clip $5-8、4 clips $20-30
  
混合路線（推薦）：
  ─ home ComfyUI 試 i2v 看構圖會不會動好看（0 元）
  ─ 雲端 Sora 2 / Veo 3 出 4 clips（$20-30）
```

---

## ⏱️ 後製建議

```
剪輯：CapCut / DaVinci Resolve（都免費）
─ 4 clip 串接、加轉場
─ Beat 3 拉慢、加心跳音效
─ Beat 4 衝擊瞬間加 zoom in + chromatic aberration

音效：
  Veo 3 自帶 → 直接用
  其他 → Epidemic Sound / Artlist 找 dark fantasy battle SFX
  
標題卡：「法師鬥惡龍 MAGES vs DRAGON」放開頭或結尾
封面圖：本專案 cover.jpg 質感頂、直接用當 YT 封面
```

---

## 🔄 套用到其他 LL 影片的通用結構

這套 Anchor + Beat 結構**通用於所有 LL 影片**：

```
NN 六貓直播片頭：
  Part 0 = 六貓角色定錨 + 武俠世界觀
  Beat 1-N = 各貓登場 + 互動 + 結尾

SS 競技場 demo：
  Part 0 = 競技場視覺 + 兩 agent 風格
  Beat 1-N = 對戰節奏（開局 / 中盤 / 高潮 / 結局）

ii 接待室宣傳：
  Part 0 = 小葉小月接待員形象 + LL 主視覺
  Beat 1-N = 用戶進場 / 召喚專家 / 完成互動

→ 4-beat 「失敗 → 領悟 → 反殺」也是 LL 通用敘事節奏
→ 任何「困境 → 突破 → 解決」故事都可套這個結構
```

---

## 一句話

```
Anchor + Beat 雙層結構 = prompt 工程的「system + user」應用到影片生成。
跨 clip 一致性接近 95%、可重用、可擴展。
本檔同時是 MD 影片分鏡 + LL 影片 prompt 範本。
```

---

## 相關文件

- 概念圖：[`../cover.jpg`](../cover.jpg) — Beat 1 first frame 候選
- 遊戲規格：[`../docs/ShadowProtocol_MVP_v0.1.md`](../docs/)
- 影片工具評估：[`../../image-studio/notes/`](../../image-studio/notes/)（home ComfyUI 能耐）
