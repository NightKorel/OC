#!/usr/bin/env python3
"""備好一組的重寫材料，拆成兩份：參考包（背景）＋純原文（分場，供逐段餵）。

給 claude.ai 的寫手（4.6）用：先讀「參考包」當背景（規則、角色卡、留用清單、
導演註），再由作者把「純原文」一場一場（或幾場）貼給它重寫。兩份分開，原文不
和規則角色卡攪在一起，也不會一次塞爆短 context。

用法：
  python3 tools/prep_scene.py --group 01     # 備第 01 組
輸出（都在 novels/北境/重寫/_待寫/，已 gitignore）：
  參考-組01.md   規則＋出場角色卡＋留用清單＋導演註
  原文-組01.md   該組逐字原文，一場一段，清楚分隔
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


def build(ids, name):
    scenes = [(sid, *parse_scene(scene_path(sid))) for sid in ids]
    names = []
    for _, fm, _ in scenes:
        for n in re.split(r"[、,，]", fm.get("出現角色", "")):
            n = n.strip()
            if n and n not in names:
                names.append(n)
    cards = cards_for(names)
    notes = director_group(group_of(ids[0]))
    dates = [fm.get("故事日期", "") for _, fm, _ in scenes if fm.get("故事日期")]
    drange = f"{dates[0]} 到 {dates[-1]}" if dates else ""

    OUTDIR.mkdir(parents=True, exist_ok=True)

    # 參考包
    ref = [f"# 參考包 {name}（先讀這份當背景）\n"]
    ref.append(
        "你是北境小說的重寫寫手。這份是背景資料：寫作規則、出場角色卡、要對齊的"
        "專名。先讀進來。作者接下來會把原文一段一段貼給你，你照這些規則把每一段"
        "重寫、精修潤飾：保留原本發生的事，不新增角色、不加角色不該知道的資訊，"
        "設定與劇情衝突時以劇情為準，名字沿用既有專名不改名。每段直接輸出重寫正文。\n")
    ref.append(f"\n本段：{name}（{ids[0]} 到 {ids[-1]}，共 {len(ids)} 場，"
               f"故事日期 {drange}，出場角色：{'、'.join(names)}）\n")
    ref.append("\n---\n\n## 寫作規則\n\n" + RULES.read_text(encoding="utf-8"))
    if cards:
        ref.append("\n\n---\n\n## 出場角色卡（節錄）\n\n" + "\n\n---\n\n".join(cards))
    if notes:
        ref.append("\n\n---\n\n## 導演註（作者當初對本段的指示）\n\n" + notes)
    ref.append("\n\n---\n\n## 留用清單（專名要對齊）\n\n" + KEEP.read_text(encoding="utf-8"))
    ref_path = OUTDIR / f"參考-{name}.md"
    ref_path.write_text("\n".join(ref), encoding="utf-8")

    # 純原文，一場一段
    raw = [f"# 原文 {name}（逐字，一場一段；作者一段一段貼給寫手）\n"]
    for sid, fm, body in scenes:
        loc = fm.get("時段地點", "")
        raw.append(f"\n\n────── 場 {sid}　{fm.get('故事日期','')}　{loc} ──────\n\n"
                   + body.rstrip())
    raw_path = OUTDIR / f"原文-{name}.md"
    raw_path.write_text("\n".join(raw), encoding="utf-8")

    return ref_path, raw_path


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
        name = f"組-{args.group}"
    elif args.sid:
        if not scene_path(args.sid).exists():
            print(f"找不到場次：{args.sid}")
            return
        ids, name = [args.sid], args.sid
    else:
        print("請用 --group 01 備一整組。")
        return

    ref_path, raw_path = build(ids, name)
    print("備好兩份（分開）：")
    print(f"  參考包：{ref_path.relative_to(ROOT)}（給寫手先讀當背景）")
    print(f"  純原文：{raw_path.relative_to(ROOT)}（作者一場一段貼給寫手重寫）")


if __name__ == "__main__":
    main()
