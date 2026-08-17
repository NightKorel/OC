#!/usr/bin/env python3
"""把第一套（艾弍大陸）的三個原始 txt 忠實拆成結構化 md。內文一字不改。"""
import os, re, pathlib

SRC = "/root/.claude/uploads/855a9f06-2b37-5d67-8804-6faa7ff5568d"
CHARS = f"{SRC}/ee8dc570-__4.6_____1.txt"
STORY = f"{SRC}/664cc5e9-__4.6____.txt"
WORLD = f"{SRC}/ce090266-__4.6____.txt"
ROOT = "/home/user/OC/sets/01-艾弍大陸"

def read(p):
    with open(p, encoding="utf-8-sig") as f:
        return f.read().replace("\r\n", "\n").replace("\r", "\n")

def write(path, text):
    pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("寫入", path)

def split_on_hr(text):
    """以獨立一行的 --- 為分隔，回傳去除頭尾空白的區塊清單。"""
    parts = re.split(r"\n-{3,}\n", "\n" + text.strip() + "\n")
    return [p.strip("\n") for p in parts if p.strip()]

def first_line(block):
    for ln in block.split("\n"):
        if ln.strip():
            return ln.strip()
    return ""

def slug(name):
    # 去掉括號附註當檔名，如「卡茨（卡修斯）」-> 卡茨
    return re.split(r"[（(]", name)[0].strip()

# ---------- 角色 ----------
ctext = read(CHARS)
cblocks = split_on_hr(ctext)
# 第一塊是身高對照
height = cblocks[0]
write(f"{ROOT}/characters/00-身高對照.md",
      f"---\ntype: reference\nset: 艾弍大陸\n---\n\n# 身高對照\n\n{height}\n")

char_meta = {
 "埃洛":  dict(race="半精靈", age=19, cp="S 級", pair="凱"),
 "凱":    dict(race="人類", age=22, cp="", pair="埃洛"),
 "耶里昂":dict(race="人類", age=25, cp="", pair="維伊"),
 "維伊":  dict(race="人類", age=18, cp="", pair="耶里昂"),
 "羅爾":  dict(race="人類", age=19, cp="A 級", pair="布萊克"),
 "布萊克":dict(race="人類", age=31, cp="", pair="羅爾"),
 "卡茨":  dict(race="人類", age="歿(19)", cp="", pair="布萊克"),
 "修":    dict(race="人類", age=29, cp="", pair=""),
 "南璐":  dict(race="人類", age="不詳", cp="", pair=""),
 "坦因":  dict(race="人類", age="不詳", cp="", pair=""),
 "索亞":  dict(race="魔獸(影狐)", age="不詳", cp="", pair="修"),
 "苑":    dict(race="人類", age=23, cp="", pair="璱"),
 "璱":    dict(race="蛇妖", age="百年以上", cp="", pair="苑"),
}

for block in cblocks[1:]:
    name = first_line(block)
    key = slug(name)
    meta = char_meta.get(key, dict(race="", age="", cp="", pair=""))
    body = block[len(name):].strip("\n")
    fm = (
        "---\n"
        f"name: {name}\n"
        f"id: {key}\n"
        "set: 艾弍大陸\n"
        f"race: {meta['race']}\n"
        f"age: {meta['age']}\n"
        f"combat: {meta['cp']}\n"
        f"pair: {meta['pair']}\n"
        "status: canon\n"
        "image_prompt: >\n  \n"
        "---\n\n"
    )
    write(f"{ROOT}/characters/{key}.md", f"{fm}# {name}\n\n{body}\n")

# ---------- 劇情線 ----------
stext = read(STORY)
sblocks = split_on_hr(stext)
for i, block in enumerate(sblocks, 1):
    title = first_line(block)
    body = block[len(title):].strip("\n")
    fname = f"{i:02d}-{slug(title)}.md"
    fm = (
        "---\n"
        f"title: {title}\n"
        "set: 艾弍大陸\n"
        "type: storyline\n"
        f"order: {i}\n"
        "status: canon\n"
        "---\n\n"
    )
    write(f"{ROOT}/storylines/{fname}", f"{fm}# {title}\n\n{body}\n")

# ---------- 世界觀 ----------
wtext = read(WORLD)
# 名詞對照/索引在結尾，找切點
m = re.search(r"\n名詞對照\n", wtext)
if m:
    world_body = wtext[:m.start()].strip("\n")
    glossary = wtext[m.start():].strip("\n")
else:
    world_body, glossary = wtext.strip("\n"), ""
write(f"{ROOT}/world/00-世界觀設定.md",
      "---\nset: 艾弍大陸\ntype: worldbuilding\nstatus: canon\n---\n\n" + world_body + "\n")
if glossary:
    write(f"{ROOT}/world/99-名詞對照.md",
          "---\nset: 艾弍大陸\ntype: glossary\nstatus: canon\n---\n\n" + glossary + "\n")

# gallery 佔位
write(f"{ROOT}/gallery/.gitkeep", "")
print("完成")
