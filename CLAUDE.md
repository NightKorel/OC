# OC 世界資料庫 — 專案規則

這個 repo 收整我（作者）的多個 OC 世界。世界「相似又不同」，還有各種 if 分支。
以下規則給 Claude（與未來的我）遵守。

## 目錄結構

```
sets/<編號-世界名>/      每一「套」世界一個資料夾
  world/                 世界觀設定、名詞對照
  characters/            角色卡，一角色一檔
  storylines/            劇情線／編年紀事，一線一檔
  gallery/               生成圖與對應 prompt
shared/                  跨世界共用的原型與設定（相似世界的共同基底）
templates/               開新世界/角色/劇情線用的空白範本
tools/                   所有輔助腳本
FILEMAP.md               檔案地圖（自動產生）
```

## 硬規則（務必遵守）

1. **所有工具都要進 git。** 任何為此 repo 寫的腳本一律放 `tools/`，並隨變更 commit，
   絕不留在暫存區或 scratchpad。
2. **檔案地圖要隨時更新。** 只要新增／刪除／搬移檔案，就執行
   `python3 tools/gen_filemap.py` 重建 `FILEMAP.md`，並一起 commit。
3. **忠實原則。** 整理既有設定時**一字不改**內文，只做拆分、加 metadata、修結構。
   要改動設定內容必須先問作者。
4. **每個角色卡開頭放 YAML frontmatter**（name/id/set/race/age/pair/status/image_prompt…），
   劇情線放（title/set/type/order/status），方便程式化處理與未來做酷東西。
5. **每一世界只掌握自己世界的資訊**；跨世界共用的東西才放 `shared/`。
6. **給生圖提示詞前，先上網搜尋該 AI 的提示詞技巧**（例：Gemini／Nano Banana、PixAI／
   Illustrious、Midjourney 各有偏好），再依查到的技巧客製提示詞，不要憑印象亂給。
   - Gemini／Nano Banana：偏好豐富**自然語言**描述，涵蓋主體、風格、光線、構圖、氛圍、
     長寬比；2–5 行、精準勝過冗長。
   - PixAI／Illustrious：偏好 **danbooru 標籤式**（`1boy, silver hair, ...`）＋負面提示詞。

## 常用指令

- 更新檔案地圖：`python3 tools/gen_filemap.py`
- 拆分第一套原始檔（一次性，已完成）：`python3 tools/split_set01.py`

## 生圖

免費、可直接用的無金鑰服務：`https://image.pollinations.ai/prompt/<英文描述>?width=768&height=768&nologo=true`
（已加入本環境網路白名單）。流程：Claude 依角色卡的 `image_prompt` 生圖 → 自行審核破綻
（手指、對稱、文字亂碼）→ 只把過關的給作者 → 存進該套的 `gallery/`。
商用需求另議（Pollinations 無商用保障，商用建議 Adobe Firefly）。
