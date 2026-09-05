#!/usr/bin/env python3
"""備好一「大段」的場景包，讓作者拿去 claude.ai 的寫手（4.6）重寫。

單位＝原文的一組（01…14，各對應原始檔一大段，數萬字），不是單一小場。
把寫手需要的全部東西湊進一個自足的檔：任務指示、寫作規則、該段逐字原文
（多場依序）、出場角色卡節錄、導演註、留用清單。寫手在對話裡直接寫出重寫
正文，不涉及 repo 操作。

用法：
  python3 tools/prep_scene.py --group 01     # 備第 01 組一整段
  python3 tools/prep_scene.py 01-003          # 只備單一場（供檢視用）
輸出：novels/北境/重寫/_待寫/<名>.md（此資料夾已 gitignore）
"""
import re, argparse, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = ROOT / "novels" / "北境"
SPLIT = BASE / "原文" / "切分"
CARDS = BASE / "設定" / "角色" / "角色卡與身高.md"
RULES = ROOT / "novels" / "寫作規則.md"
KEEP = BASE / "留用清單.md"
OUTDIR = BASE / "重寫" / "_待寫"
INDEX = SPLIT / "索引-原文順序.md"


def ordered_ids():
    ids = []
    for ln in INDEX.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([0-9A-Za-z\-]+-\d{3})\s*\|", ln)
        if m:
            ids.append(m.group(1))
    return ids


def group_of(sid):
    return sid.rsplit("-", 1)[0]


def scene_path(sid):
    return SPLIT / group_of(sid) / "正文" / f"{sid}.md"


def parse_scene(path):
    text = path.read_text(encoding="utf-8")
    fm, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        for line in text[3:end].splitlines():
            m = re.match(r"([^:：]+)[:：]\s*(.*)", line.strip())
            if m:
                fm[m.group(1).strip()] = m.group(2).strip()
        body = text[end + 4:].lstrip("\n")
    return fm, body


def card_sections():
    text = CARDS.read_text(encoding="utf-8")
    out = {}
    for chunk in re.split(r"\n-{3,}\n", text):
        lines = chunk.strip().splitlines()
        if lines:
            out[lines[0].strip()] = chunk.strip()
    return out


def cards_for(names):
    secs = card_sections()
    picked = []
    for nm in names:
        for head, chunk in secs.items():
            if head.startswith(nm):
                picked.append(chunk)
                break
    return picked


def director_group(group):
    dn = SPLIT / group / "導演註.md"
    return dn.read_text(encoding="utf-8").strip() if dn.exists() else ""


def build(ids, out_name):
    scenes = [parse_scene(scene_path(i)) for i in ids]
    # 依序串正文
    bodies = "\n\n\n".join(b.rstrip() for _, b in scenes)
    # 出場角色（依出現順序去重）
    names = []
    for fm, _ in scenes:
        for n in re.split(r"[、,，]", fm.get("出現角色", "")):
            n = n.strip()
            if n and n not in names:
                names.append(n)
    cards = cards_for(names)
    dates = [fm.get("故事日期", "") for fm, _ in scenes if fm.get("故事日期")]
    drange = f"{dates[0]} 到 {dates[-1]}" if dates else ""
    group = group_of(ids[0])
    notes = director_group(group)

    p = []
    p.append(f"# 場景包 {out_name}（重寫用）\n")
    p.append(
        "你是北境小說的重寫寫手。這個檔裡有你需要的全部東西，不用去找別的資料。\n\n"
        "請把下面「原文（本段）」整段重寫、精修潤飾，直接在對話裡輸出重寫後的正文"
        "（不用存檔、不涉及任何檔案操作）：\n"
        "1. 逐條遵守「寫作規則」。\n"
        "2. 依原文的情節與人物；保留原本發生的事，不新增角色、不加角色不該知道的"
        "資訊。設定與劇情衝突時以劇情為準。\n"
        "3. 名字對照「留用清單」與角色卡，沿用既有專名，不改名、不另造。\n"
        "4. 這是一大段、有很多場，依原文順序一場接一場重寫；每場開頭保留故事內的"
        "時間地點戳記。\n"
        "5. 篇幅與原文相當或略多；寫完這一整段。\n"
    )
    p.append("\n---\n\n## 本段資訊\n")
    p.append(f"- 段：{out_name}（{ids[0]} 到 {ids[-1]}，共 {len(ids)} 場）\n"
             f"- 故事日期範圍：{drange}\n"
             f"- 出場角色：{'、'.join(names)}\n")
    p.append("\n---\n\n## 寫作規則\n\n" + RULES.read_text(encoding="utf-8"))
    p.append("\n\n---\n\n## 原文（本段，逐字，供你精修的依據）\n\n" + bodies)
    if cards:
        p.append("\n\n---\n\n## 出場角色卡（節錄）\n\n" + "\n\n---\n\n".join(cards))
    if notes:
        p.append("\n\n---\n\n## 導演註（作者當初對本段的指示）\n\n" + notes)
    p.append("\n\n---\n\n## 留用清單（專名要對齊）\n\n" + KEEP.read_text(encoding="utf-8"))

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / f"{out_name}.md"
    out.write_text("\n".join(p), encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sid", nargs="?")
    ap.add_argument("--group")
    args = ap.parse_args()

    if args.group:
        ids = [i for i in ordered_ids() if group_of(i) == args.group]
        if not ids:
            print(f"找不到第 {args.group} 組的場次。")
            return
        out = build(ids, f"組-{args.group}")
    elif args.sid:
        if not scene_path(args.sid).exists():
            print(f"找不到場次：{args.sid}")
            return
        out = build([args.sid], args.sid)
    else:
        print("請用 --group 01 備一整段，或給場號備單場。")
        return

    print(f"已備好場景包：{out.relative_to(ROOT)}")
    print("把這個檔上傳到 claude.ai 的 4.6，叫它照檔重寫；寫完把正文貼回來給整理窗。")


if __name__ == "__main__":
    main()
