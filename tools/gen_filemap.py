#!/usr/bin/env python3
"""產生／更新檔案地圖 FILEMAP.md。
掃描整個 repo，讀取每個 .md 的 YAML frontmatter 摘要，輸出一份索引。
用法：python3 tools/gen_filemap.py
"""
import os, re, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "gallery", "切分"}  # 切分為腳本生成，另有自身索引，不逐檔列入
OUT = ROOT / "FILEMAP.md"

def read_front(path):
    """取出 YAML frontmatter 的幾個常用欄位。"""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].splitlines():
        m = re.match(r"([A-Za-z_]+):\s*(.*)", line.strip())
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm

def tree_lines(base):
    lines = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        rel = pathlib.Path(dirpath).relative_to(base)
        depth = 0 if str(rel) == "." else len(rel.parts)
        if str(rel) != ".":
            lines.append(("  " * (depth - 1)) + f"- **{rel.parts[-1]}/**")
        for fn in sorted(filenames):
            if fn.startswith("."):
                continue
            p = pathlib.Path(dirpath) / fn
            note = ""
            if fn.endswith(".md"):
                fm = read_front(p)
                bits = [fm[k] for k in ("name", "title", "type") if fm.get(k)]
                if bits:
                    note = " — " + " / ".join(dict.fromkeys(bits))
            lines.append(("  " * depth) + f"- `{fn}`{note}")
    return lines

def main():
    now = datetime.date.today().isoformat()
    out = ["# 檔案地圖 (FILEMAP)", "",
           f"_自動產生，最後更新：{now}。請執行 `python3 tools/gen_filemap.py` 更新，勿手動編輯。_", ""]

    # 各套統計
    sets_dir = ROOT / "sets"
    if sets_dir.exists():
        out.append("## 世界套目錄\n")
        out.append("| 套 | 角色 | 劇情線 | 世界觀檔 |")
        out.append("|----|-----:|-------:|--------:|")
        for s in sorted(p for p in sets_dir.iterdir() if p.is_dir()):
            nc = len(list(s.glob("**/characters/*.md")))
            ns = len(list(s.glob("**/storylines/*.md")))
            nw = len(list(s.glob("**/world/*.md")))
            out.append(f"| {s.name} | {nc} | {ns} | {nw} |")
        out.append("")

    out.append("## 完整檔案樹\n")
    out += tree_lines(ROOT)
    out.append("")
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("已更新", OUT)

if __name__ == "__main__":
    main()
