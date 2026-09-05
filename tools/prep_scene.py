#!/usr/bin/env python3
"""備好一場的「場景包」，讓短 context 的寫手（如 4.6）自己就能重寫。

把寫手不擅長的找場次、湊資料、翻設定全做完，輸出一個自足的檔，寫手只要讀
那一個檔就有全部需要的東西：任務指示、寫作規則、該場原文、出場角色卡節錄、
導演註、留用清單。

用法：
  python3 tools/prep_scene.py --next     # 自動挑下一個還沒重寫的場
  python3 tools/prep_scene.py 01-001     # 指定場號
輸出：novels/北境/重寫/_待寫/<場號>.md（此資料夾已 gitignore，不會進版控）
"""
import re, sys, argparse, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = ROOT / "novels" / "北境"
SPLIT = BASE / "原文" / "切分"
CARDS = BASE / "設定" / "角色" / "角色卡與身高.md"
WORLD = BASE / "設定" / "世界觀" / "世界觀與名詞對照.md"
RULES = ROOT / "novels" / "寫作規則.md"
KEEP = BASE / "留用清單.md"
OUTDIR = BASE / "重寫" / "_待寫"
DONEDIR = BASE / "重寫"

INDEX = SPLIT / "索引-原文順序.md"


def ordered_ids():
    ids = []
    for ln in INDEX.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([0-9A-Za-z\-]+-\d{3})\s*\|", ln)
        if m:
            ids.append(m.group(1))
    return ids


def scene_path(sid):
    group = sid.rsplit("-", 1)[0]
    return SPLIT / group / "正文" / f"{sid}.md"


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
        lines = [l for l in chunk.strip().splitlines()]
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


def director_for(sid, stamp):
    group = sid.rsplit("-", 1)[0]
    dn = SPLIT / group / "導演註.md"
    if not dn.exists():
        return []
    text = dn.read_text(encoding="utf-8")
    hits = []
    for block in text.split("\n## "):
        if stamp and stamp[:12] in block:
            hits.append("## " + block.strip())
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sid", nargs="?")
    ap.add_argument("--next", action="store_true", dest="nxt")
    args = ap.parse_args()

    if args.nxt:
        sid = None
        for i in ordered_ids():
            if not (DONEDIR / f"{i}.md").exists():
                sid = i
                break
        if sid is None:
            print("所有場都已有重寫成品，沒有下一場。")
            return
    else:
        sid = args.sid
        if not sid:
            print("請給場號，或用 --next。例：python3 tools/prep_scene.py 01-001")
            return

    sp = scene_path(sid)
    if not sp.exists():
        print(f"找不到場次原文：{sp}")
        return

    fm, body = parse_scene(sp)
    names = [n.strip() for n in re.split(r"[、,，]", fm.get("出現角色", "")) if n.strip()]
    cards = cards_for(names)
    stamp = body.splitlines()[0].strip() if body.strip() else ""
    notes = director_for(sid, stamp)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / f"{sid}.md"

    parts = []
    parts.append(f"# 場景包 {sid}（重寫用）\n")
    parts.append(
        "你是北境小說的重寫寫手。這個檔裡有你需要的全部東西，不用再去翻別的檔。\n\n"
        "做這些：\n"
        f"1. 逐條遵守下面「寫作規則」。\n"
        f"2. 依「原文（本場）」的情節與人物重寫這一場，做文字精修潤飾：保留原本發生"
        "的事，不新增角色、不加角色不該知道的資訊。設定與劇情衝突時以劇情為準。\n"
        f"3. 名字對照「留用清單」，沿用既有專名，不要改名或另造。\n"
        f"4. 成品存成 novels/北境/重寫/{sid}.md：第一行寫「對應原文：{sid}」，空一行，"
        "再放重寫正文（正文第一行是故事內時間地點戳記）。不要加其他 metadata。\n"
        "5. git add 該檔、commit、git push origin HEAD:main。被拒就先 "
        "git pull --no-edit origin main 再推，不要 force。\n"
        "6. 不要 commit _待寫/ 這個資料夾。\n"
    )
    parts.append("\n---\n\n## 本場資訊\n")
    parts.append(f"- 場號：{sid}\n- 故事日期：{fm.get('故事日期','')}\n"
                 f"- 時段地點：{fm.get('時段地點','')}\n- 出現角色：{fm.get('出現角色','')}\n")
    parts.append("\n---\n\n## 寫作規則\n\n" + RULES.read_text(encoding="utf-8"))
    parts.append("\n\n---\n\n## 原文（本場，逐字，供你精修的依據）\n\n" + body.rstrip())
    if cards:
        parts.append("\n\n---\n\n## 出場角色卡（節錄）\n\n" + "\n\n---\n\n".join(cards))
    if notes:
        parts.append("\n\n---\n\n## 導演註（作者當初對這附近的指示）\n\n" + "\n\n".join(notes))
    parts.append("\n\n---\n\n## 留用清單（專名要對齊）\n\n" + KEEP.read_text(encoding="utf-8"))

    out.write_text("\n".join(parts), encoding="utf-8")

    print(f"已備好場景包：{out.relative_to(ROOT)}")
    print(f"下一步：讀這個檔，照裡面重寫，成品存 novels/北境/重寫/{sid}.md，"
          f"然後 git commit 並 git push origin HEAD:main。")


if __name__ == "__main__":
    main()
