# OC 世界資料庫

收整多個 OC 世界的設定、角色與劇情線。世界之間相似又不同，並有各種「if」分支。

<p align="center">
  <img src="assets/oc-readme-portrait.png" alt="OC 抽象肖像" width="420">
</p>

## 快速導覽

- 各世界在 [`sets/`](sets/)，目前有：
  - [`01-艾弍大陸`](sets/01-艾弍大陸/) — 北境底下的奇幻大陸，中世紀＋魔法的四大勢力世界。
  - [`02-北大`](sets/02-北大/) — 北境大學；主要現代世界觀，包含多個 IF 分支。
  - [`03-北迴`](sets/03-北迴/) — 現代異能世界觀；角色們一邊做 VT，一邊對抗異常。
  - [`04-北娛`](sets/04-北娛/) — 北境娛樂；角色們身為演員的現代世界觀。
  - [`05-北靈`](sets/05-北靈/) — 角色們身為處靈師的現代世界觀。
- 世界套導覽與新增方式見 [`sets/README.md`](sets/README.md)。
- 完整檔案清單見 [`FILEMAP.md`](FILEMAP.md)（自動產生）。
- 專案規則與慣例見 [`CLAUDE.md`](CLAUDE.md)。

## 結構

| 資料夾 | 內容 |
|--------|------|
| `sets/` | 每套世界一資料夾（world / characters / storylines / gallery） |
| `shared/` | 跨世界共用的原型與設定 |
| `templates/` | 開新世界／角色／劇情線的空白範本 |
| `tools/` | 所有輔助腳本（拆分、檔案地圖產生器…） |

## 維護

新增或搬移檔案後，執行 `python3 tools/gen_filemap.py` 更新檔案地圖。

## 圖庫

角色圖片集中於 [gallery/](gallery/)，以角色為第一層；世界觀、服裝與風格放在角色底下的子資料夾。
