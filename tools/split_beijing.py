#!/usr/bin/env python3
"""切分北境重寫項目的原文匯出檔。

輸入：novels/北境/原文/ 下的 NN-*.txt 與 if分支/*.txt（對話匯出）。
輸出：novels/北境/原文/切分/ 下
  <組>/正文/<場號>.md   每場一檔，frontmatter + 逐字正文
  <組>/導演註.md         作者括號指示與讀者論壇，依出現順序，標注鄰近場次
  索引-原文順序.md
  索引-故事時間.md
  進度台帳.md

原則：正文逐字保留，只做拆分與加 metadata。匯出標頭尾、## 標記、時間戳、
模型 Thought 與英文規劃筆記一律丟棄；作者指示與論壇分流到導演註。
用法：python3 tools/split_beijing.py
"""
import os, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "novels" / "北境" / "原文"
OUT = SRC / "切分"

# 故事內時間地點戳記：行首（可含「新曆」）年月日，且整行不長
STAMP = re.compile(r'^(新曆)?\s*(\d{3,4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日(.*)$')
# 匯出時間戳，例：2026/2/18 上午2:36:44
EXPORT_TS = re.compile(r'^\d{4}/\d{1,2}/\d{1,2}\s')
FORUM_POST = re.compile(r'^\s*\d+\s*L(\s|｜|\|)')
FOOTER = "Powered by Claude Exporter"

# 角色偵測（含別名對應）。修為單字，用 regex 排除「修剪/修復/卡修斯」等誤中。
NAME_MAP = [
    ("布萊克", re.compile("布萊克|伯恩")),
    ("羅爾", re.compile("羅爾")),
    ("埃洛", re.compile("埃洛")),
    ("凱", re.compile("凱")),
    ("耶里昂", re.compile("耶里昂")),
    ("維伊", re.compile("維伊")),
    ("修", re.compile(r"(?<!卡)修(?!剪|復|理|補|改|正|建|飾|女|士|行|煉|訂|養|繕|好)")),
    ("南璐", re.compile("南璐")),
    ("坦因", re.compile("坦因")),
    ("索亞", re.compile("索亞")),
    ("卡茨", re.compile("卡茨|卡修斯")),
    ("苑", re.compile("苑")),
    ("璱", re.compile("璱")),
]

SEG_MAP = {"凌晨": 0, "半夜": 0, "清晨": 1, "早": 1, "上午": 2, "午前": 2,
           "午間": 3, "中午": 3, "正午": 3, "午後": 4, "下午": 4,
           "傍晚": 5, "入夜": 6, "夜間": 6, "夜": 6, "晚": 6, "深夜": 7}


def cjk_ratio(s):
    letters = [c for c in s if not c.isspace()]
    if not letters:
        return 0.0
    cjk = sum(1 for c in letters if '一' <= c <= '鿿' or c in "，。、！？；：「」『』（）《》……")
    return cjk / len(letters)


def seg_bucket(rest):
    for k, v in SEG_MAP.items():
        if k in rest:
            return v
    return 3


def find_chars(text):
    found = []
    for canon, pat in NAME_MAP:
        if pat.search(text):
            found.append(canon)
    return found


def parse_blocks(lines):
    """回傳 (header_title, [ (type, [(lineno, text), ...]), ... ])。type 為 'R'/'P'。"""
    blocks = []
    header = []
    cur = None
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")
        if line.strip() in ("## Response:", "## Prompt:"):
            if cur is not None:
                blocks.append(cur)
            cur = ("R" if "Response" in line else "P", [])
            continue
        if cur is None:
            header.append(line)
        else:
            cur[1].append((i, line))
    if cur is not None:
        blocks.append(cur)
    title = ""
    for h in header:
        if h.strip():
            title = h.strip()
            break
    return title, blocks


def is_forum(block_lines):
    posts = sum(1 for _, t in block_lines if FORUM_POST.match(t))
    joined = "\n".join(t for _, t in block_lines)
    return posts >= 3 or "讀者討論樓" in joined or "集中討論樓" in joined


def paras_from(buf_lines):
    """把 (lineno,text) 串成段落，丟掉英文規劃段，回傳純正文段落列表。"""
    paras, cur = [], []
    for _, t in buf_lines:
        if t.strip() == "":
            if cur:
                paras.append(cur); cur = []
        else:
            cur.append(t)
    if cur:
        paras.append(cur)
    keep = []
    for p in paras:
        text = "\n".join(p)
        if cjk_ratio(text) < 0.15:      # 英文規劃筆記
            continue
        keep.append(text)
    return keep


def process_file(path, group):
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    title, blocks = parse_blocks(lines)
    scenes = []          # dict per scene
    director = []        # (kind, near_stamp, text)
    last_stamp = None
    seq = 0
    for btype, blines in blocks:
        # 去掉緊接標記的匯出時間戳、footer
        body = [(ln, t) for ln, t in blines
                if not EXPORT_TS.match(t) and FOOTER not in t]
        if btype == "P":
            text = "\n".join(t for _, t in body).strip()
            if text:
                director.append(("作者指示", last_stamp, text))
            continue
        # Response
        if is_forum(body):
            text = "\n".join(t for _, t in body).strip()
            if text:
                director.append(("論壇", last_stamp, text))
            continue
        # 依戳記切場；戳記前的內容（模型閒聊／規劃）丟棄
        cur = None
        for ln, t in body:
            m = STAMP.match(t) if len(t) < 60 else None
            if m:
                if cur:
                    scenes.append(cur)
                seq += 1
                rest = (m.group(5) or "").strip(" 、，。")
                last_stamp = t.strip()
                cur = {
                    "seq": seq, "line": ln, "stamp": t.strip(),
                    "year": int(m.group(2)), "month": int(m.group(3)),
                    "day": int(m.group(4)), "rest": rest,
                    "seg": seg_bucket(rest), "buf": [],
                }
            elif cur is not None:
                if t.strip().startswith("Thought:") or t.strip().startswith("Thought："):
                    continue
                cur["buf"].append((ln, t))
        if cur:
            scenes.append(cur)
    # 清英文段、組正文
    for s in scenes:
        s["paras"] = paras_from(s["buf"])
        s["chars"] = find_chars("\n".join(s["paras"]))
    return title, scenes, director


def write_group(group, title, scenes, director):
    gdir = OUT / group
    (gdir / "正文").mkdir(parents=True, exist_ok=True)
    rows = []
    for s in scenes:
        sid = f"{group}-{s['seq']:03d}"
        date = f"{s['year']:03d}-{s['month']:02d}-{s['day']:02d}"
        chars = "、".join(s["chars"]) if s["chars"] else ""
        fm = (
            "---\n"
            f"場: {sid}\n"
            f"來源: {group}（{title}）\n"
            f"來源行: {s['line']}\n"
            f"故事日期: {date}\n"
            f"時段地點: {s['rest']}\n"
            f"出現角色: {chars}\n"
            "狀態: 未重寫\n"
            "---\n\n"
        )
        body = s["stamp"] + "\n\n\n" + "\n\n\n".join(s["paras"]) + "\n"
        (gdir / "正文" / f"{sid}.md").write_text(fm + body, encoding="utf-8")
        rows.append({"sid": sid, "date": date, "seg": s["seg"],
                     "rest": s["rest"], "chars": chars, "group": group})
    # 導演註
    if director:
        parts = [f"# {group}（{title}）導演註\n",
                 "作者括號指示與讀者論壇，從原文抽出，供重寫時參考。逐字保留。\n"]
        for kind, near, text in director:
            parts.append(f"\n## {kind}（鄰近場次戳記：{near or '（檔首）'}）\n\n{text}\n")
        (gdir / "導演註.md").write_text("\n".join(parts), encoding="utf-8")
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    all_rows = []
    src_files = sorted(SRC.glob("[0-9][0-9]-*.txt"))
    for p in src_files:
        group = p.name[:2]
        title, scenes, director = process_file(p, group)
        rows = write_group(group, title, scenes, director)
        all_rows.extend(rows)
        print(f"{p.name}: {len(scenes)} 場, 導演註 {len(director)} 則")
    ifdir = SRC / "if分支"
    if ifdir.exists():
        for p in sorted(ifdir.glob("*.txt")):
            group = "if-" + p.stem.split("-")[0]
            title, scenes, director = process_file(p, group)
            rows = write_group(group, title, scenes, director)
            all_rows.extend(rows)
            print(f"{p.name}: {len(scenes)} 場, 導演註 {len(director)} 則")

    # 索引：原文順序
    lines = ["# 切分索引（依原文順序）\n",
             "自動產生，勿手動編輯。重寫依此順序推進。\n",
             "| 場號 | 故事日期 | 時段地點 | 出現角色 |",
             "|------|----------|----------|----------|"]
    for r in all_rows:
        lines.append(f"| {r['sid']} | {r['date']} | {r['rest']} | {r['chars']} |")
    (OUT / "索引-原文順序.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 索引：故事時間軸
    chrono = sorted(all_rows, key=lambda r: (r["date"], r["seg"], r["sid"]))
    lines = ["# 切分索引（依故事時間軸）\n",
             "自動產生，勿手動編輯。各檔跟不同配對線走，故事時間會前後跳。\n",
             "| 故事日期 | 時段地點 | 場號 | 出現角色 |",
             "|----------|----------|------|----------|"]
    for r in chrono:
        lines.append(f"| {r['date']} | {r['rest']} | {r['sid']} | {r['chars']} |")
    (OUT / "索引-故事時間.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 進度台帳
    lines = ["# 重寫進度台帳\n",
             "自動產生初版；重寫時把對應場次狀態改為「已重寫」，成品放 novels/北境/重寫/。\n",
             f"總場數：{len(all_rows)}\n",
             "| 場號 | 故事日期 | 狀態 |",
             "|------|----------|------|"]
    for r in all_rows:
        lines.append(f"| {r['sid']} | {r['date']} | 未重寫 |")
    (OUT / "進度台帳.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"總計 {len(all_rows)} 場")


if __name__ == "__main__":
    main()
