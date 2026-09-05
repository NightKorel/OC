#!/usr/bin/env python3
"""掃描「新寫版本」的名詞候選，供作者篩選要留用的小配角、物品、地點。

只掃 novels/北境/重寫/（新版本），預設不碰原文。重寫還沒有內容時輸出為空。
用途：重寫累積一些後跑這支，把重複出現、非主角的名字連同首見出處與一句
上下文列出來；作者再挑要留的進留用清單（清單格式待定，不由本腳本決定）。

heuristics 針對中文，靠幾個線索抓候選（對話者、地點/組織後綴、《》書名）。
準度有限，需要用真實重寫內容調整；本腳本只產「候選」，不是最終索引。

用法：
  python3 tools/scan_novel_names.py            # 掃 重寫/，印候選表
  python3 tools/scan_novel_names.py --dir 路徑  # 指定其他目錄（預設 重寫/）
  python3 tools/scan_novel_names.py --min 2     # 出現次數門檻（預設 1）
"""
import re, sys, argparse, pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_DIR = ROOT / "novels" / "北境" / "重寫"

# 主角與別名：不列入候選（這些已在設定角色卡）
MAIN = {"布萊克", "伯恩", "羅爾", "埃洛", "凱", "耶里昂", "維伊",
        "修", "南璐", "坦因", "索亞", "卡茨", "卡修斯", "苑", "璱"}

HAN = r"[一-鿿]"
# 對話／動作者：名字後接說話或動作動詞
SPEAKER = re.compile(rf"({HAN}{{2,4}})(?=說|道|問|答|喊|叫|笑道|開口|低聲|嘆道|回道)")
# 地點／組織：名字後接場所或團體後綴
PLACE = re.compile(rf"({HAN}{{2,4}})(?=小隊|酒館|工坊|公會|驛|堡|寒鐵城|分局)")
# 書名／物品專名
TITLE = re.compile(r"《([^》]{1,20})》")

FRONTMATTER = re.compile(r"^---\s*$")
STAMP = re.compile(r"^(新曆)?\s*\d{3,4}\s*年\s*\d{1,2}\s*月")


def strip_meta(text):
    lines = text.splitlines()
    out, in_fm = [], False
    for i, ln in enumerate(lines):
        if FRONTMATTER.match(ln):
            in_fm = not in_fm if i < 30 else in_fm
            continue
        if in_fm:
            continue
        if STAMP.match(ln.strip()):
            continue
        out.append(ln)
    return "\n".join(out)


def scan(dirpath, min_count):
    cand = defaultdict(lambda: {"n": 0, "first": None, "snip": ""})
    files = sorted(p for p in dirpath.rglob("*")
                   if p.suffix in (".md", ".txt") and p.is_file())
    n_files = 0
    for p in files:
        n_files += 1
        body = strip_meta(p.read_text(encoding="utf-8"))
        for pat, kind in ((SPEAKER, "人"), (PLACE, "地/組"), (TITLE, "專名")):
            for m in pat.finditer(body):
                name = m.group(1)
                if name in MAIN:
                    continue
                c = cand[(name, kind)]
                c["n"] += 1
                if c["first"] is None:
                    c["first"] = p.name
                    start = max(0, m.start() - 8)
                    c["snip"] = body[start:m.start() + len(name) + 12].replace("\n", " ")
    rows = [(k[0], k[1], v["n"], v["first"], v["snip"])
            for k, v in cand.items() if v["n"] >= min_count]
    rows.sort(key=lambda r: (-r[2], r[0]))
    return n_files, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(DEFAULT_DIR))
    ap.add_argument("--min", type=int, default=1)
    args = ap.parse_args()
    d = pathlib.Path(args.dir)
    if not d.exists():
        print(f"目錄不存在：{d}")
        return
    n_files, rows = scan(d, args.min)
    if n_files == 0:
        print(f"{d} 下沒有 .md/.txt，重寫尚無內容，無候選。")
        return
    if not rows:
        print(f"掃了 {n_files} 個檔，沒有達門檻的候選。")
        return
    print(f"掃了 {n_files} 個檔，候選 {len(rows)} 條（出現次數 >= {args.min}）：\n")
    print("| 候選 | 類 | 次數 | 首見 | 上下文 |")
    print("|------|----|-----:|------|--------|")
    for name, kind, n, first, snip in rows:
        print(f"| {name} | {kind} | {n} | {first} | {snip} |")


if __name__ == "__main__":
    main()
