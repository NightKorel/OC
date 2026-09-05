#!/usr/bin/env python3
"""掃描「新寫版本」的專有名詞候選，供作者篩選要留用的清單。

只掃 novels/北境/重寫/（新版本），預設不碰原文。重寫尚無內容時輸出為空。
用途：重寫累積一些後跑這支，把重複出現的專有名詞候選連同類別、次數、首見
出處與一句上下文列出來；作者再挑要留的進留用清單（清單格式待定，不由本腳本
決定）。涵蓋：人名（對話者）、地名、草藥／材料、魔獸、組織、《》專名。

heuristics 靠中文詞尾線索，會過抓也會漏抓，只給「候選」不是最終索引；有真實
重寫內容後再據以調整。主角名與明顯常用詞先排除，其餘交作者篩。

用法：
  python3 tools/scan_novel_names.py            # 掃 重寫/，印候選表
  python3 tools/scan_novel_names.py --dir 路徑  # 指定其他目錄（預設 重寫/）
  python3 tools/scan_novel_names.py --min 2     # 出現次數門檻（預設 1）
"""
import re, argparse, pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_DIR = ROOT / "novels" / "北境" / "重寫"

# 主角與別名不列入候選（已在設定角色卡）
MAIN = {"布萊克", "伯恩", "羅爾", "埃洛", "凱", "耶里昂", "維伊",
        "修", "南璐", "坦因", "索亞", "卡茨", "卡修斯", "苑", "璱"}

# 明顯常用詞，過濾掉降噪（可再補）
STOP = {"樹木", "樹葉", "草地", "草叢", "花瓣", "石頭", "木頭", "石板",
        "石階", "火光", "水面", "山上", "山下", "爬山", "靠山", "河邊",
        "河面", "海面", "地面", "牆面", "桌面", "後山", "半山", "花朵",
        "枯草", "野草", "木板", "木門", "木樁", "石縫", "石牆"}

H = "一-鿿"


def suf(chars, minlen):
    """名字＝(minlen-1..4) 個漢字加一個詞尾字。"""
    return re.compile(rf"([{H}]{{{minlen-1},4}}[{chars}])")


# (類別, regex)。詞尾越專用噪音越低；單字地形詞要求較長以降噪。
CATS = [
    ("人", re.compile(rf"([{H}]{{2,4}})(?=說|道|問|答|喊|叫|笑道|開口|低聲|嘆道|回道)")),
    ("地名", suf("城鎮村驛堡港嶺", 2)),
    ("地形", suf("山河湖海谷坡島關塔殿橋丘峰", 3)),
    ("草藥料", suf("苔蘚根藤菌草花葉木果粉籽脂", 2)),
    ("魔獸", suf("鳥鷹鷲豬兔鹿狼蛇獸龍狐蟲鼠", 2)),
    ("組織", re.compile(rf"([{H}]{{1,4}}(?:公會|小隊|協會|議會|神殿|商會|聯盟|聯合))")),
    ("專名", re.compile(r"《([^》]{1,20})》")),
]

FM = re.compile(r"^---\s*$")
STAMP = re.compile(r"^(新曆)?\s*\d{3,4}\s*年\s*\d{1,2}\s*月")


def strip_meta(text):
    out, in_fm = [], False
    for i, ln in enumerate(text.splitlines()):
        if FM.match(ln):
            in_fm = not in_fm if i < 30 else in_fm
            continue
        if in_fm or STAMP.match(ln.strip()):
            continue
        out.append(ln)
    return "\n".join(out)


def scan(dirpath, min_count):
    cand = defaultdict(lambda: {"n": 0, "first": None, "snip": ""})
    files = sorted(p for p in dirpath.rglob("*")
                   if p.suffix in (".md", ".txt") and p.is_file())
    for p in files:
        body = strip_meta(p.read_text(encoding="utf-8"))
        for label, pat in CATS:
            for m in pat.finditer(body):
                name = m.group(1)
                if name in MAIN or name in STOP or len(name) < 2:
                    continue
                c = cand[(name, label)]
                c["n"] += 1
                if c["first"] is None:
                    c["first"] = p.name
                    s = max(0, m.start() - 8)
                    c["snip"] = body[s:m.start() + len(name) + 10].replace("\n", " ")
    rows = [(k[0], k[1], v["n"], v["first"], v["snip"])
            for k, v in cand.items() if v["n"] >= min_count]
    rows.sort(key=lambda r: (-r[2], r[1], r[0]))
    return len(files), rows


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
    print(f"掃了 {n_files} 個檔，候選 {len(rows)} 條（次數 >= {args.min}）：\n")
    print("| 候選 | 類別 | 次數 | 首見 | 上下文 |")
    print("|------|------|-----:|------|--------|")
    for name, label, n, first, snip in rows:
        print(f"| {name} | {label} | {n} | {first} | {snip} |")


if __name__ == "__main__":
    main()
