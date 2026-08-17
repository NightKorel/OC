#!/usr/bin/env python3
"""為各角色產生 gallery/<角色>/STYLE.md，並把 danbooru 式 prompt 寫進角色卡 image_prompt。
資料來源：角色卡設定 + 作者參考圖。內文為畫風/生圖輔助，不更動角色卡既有正文。
用法：python3 tools/gen_style.py
"""
import glob, os, re

ROOT = "sets/01-艾弍大陸"
GAL = f"{ROOT}/gallery"
CHAR = f"{ROOT}/characters"

# 共用畫風描述
STYLE_LINE = ("精緻日系動漫插畫（PixAI / Illustrious 系模型）：乾淨線稿、柔和平塗、"
              "低到中彩度、素或淺色背景。避免寫實照片感與 3D/CG 感。")

# 每個角色：外型 canon、招牌服裝、danbooru prompt
DATA = {
"埃洛": dict(
    colors={"眼": "#4E9E7E 翡翠綠", "髮": "#E6E6EA 銀白", "膚": "#F3EAE2 蒼白", "招牌": "#4A5548 墨綠兜帽斗篷"},
    look=["銀白色長直髮、中分、幾綹垂臉", "翡翠綠眼、眼神疲憊半垂憂鬱",
          "蒼白皮膚、尖精靈耳、纖瘦（19 歲）", "半精靈，永遠戴兜帽遮尖耳"],
    outfit=["奇幻：黑色或墨綠高領兜帽斗篷，兜帽戴起遮耳（招牌）",
            "現代休閒：軍綠外套、素 T、銀色墜飾項鍊、深色長褲、白球鞋"],
    prompt="1boy, half-elf, long straight silver-white hair, center part, green eyes, "
           "pointed ears, pale skin, thin slender, melancholic half-lidded eyes, "
           "black or dark green hooded cloak, hood up, masterpiece, best quality, detailed"),
"布萊克": dict(
    colors={"眼": "#7B5EA8 紫", "髮": "#17161C 黑", "膚": "#EDE4E0 蒼白", "招牌": "#322843 暗紫斗篷＋銀飾"},
    look=["黑色長直髮披至腰間", "紫色眼眸", "蒼白、氣質沉穩內斂", "身高最高（31 歲）"],
    outfit=["奇幻：暗紫色斗篷、銀飾、銀色新月胸扣、黑衣，不佩實體武器（影為武器）",
            "現代：黑色高領針織、黑長褲、居家亦全黑"],
    prompt="1boy, mature male, very long straight black hair, purple eyes, pale skin, "
           "tall, calm melancholic expression, dark purple hooded cloak, silver ornaments, "
           "crescent moon brooch, black clothes, masterpiece, best quality, detailed"),
"羅爾": dict(
    colors={"眼": "#D33C3C 紅", "髮": "#B5232A 緋紅", "膚": "#F0DACB", "招牌": "#D4AF37 金耳環／黑頸圈"},
    look=["緋紅色短髮、紅眼", "高挑結實偏瘦", "外冷、底層帶攻擊性", "左耳深金色耳環、黑色頸圈（招牌）"],
    outfit=["日常：連帽上衣、運動褲", "外出：酒紅／紅色外套；戰鬥火系", "左腕內側青色紋身 62"],
    prompt="1boy, spiky short crimson red hair, red eyes, gold hoop earring, black choker, "
           "athletic slim body, hoodie, sharp aggressive expression, masterpiece, best quality"),
"凱": dict(
    colors={"眼": "#6E4A2E 深棕", "髮": "#4A3626 深棕", "膚": "#F1E2D4"},
    look=["深棕色短髮、深棕眼", "清秀纖瘦", "極怕冷、常包裹圍巾風衣手套（22 歲）", "表情溫和帶戒備"],
    outfit=["現代休閒：圍巾、大衣／風衣、手套、長靴", "居家：高領針織、蓋毯、暖襪"],
    prompt="1boy, short dark brown hair, brown eyes, slender, delicate handsome face, "
           "scarf, winter coat, gloves, gentle wary smile, cold, masterpiece, best quality"),
"修": dict(
    colors={"眼": "#E0A63A 琥珀", "髮": "#AEC6A0 淺綠", "膚": "#F0E4D6", "索亞": "#2A1E22 黑紅毛／#3E6FB0 藍眼"},
    look=["淺綠色長髮、平時髮繩束起", "琥珀色眼", "理性溫和（29 歲）", "常伴影狐索亞（黑紅毛、藍眼）"],
    outfit=["上白下黑、簡約", "鑲黑石項鍊、雙腕功能魔法手鐲"],
    prompt="1boy, long light green hair tied back, amber eyes, calm gentle expression, "
           "white coat over black clothes, pendant necklace, bracelets, masterpiece, best quality"),
"維伊": dict(
    colors={"眼(真)": "#466FA8 藍", "眼(偽裝)": "#16151B 黑", "髮": "#16151B 黑", "膚": "#E8DBCF"},
    look=["黑髮（真實瞳色為藍，平時戴黑色隱形眼鏡偽裝）", "瘦小骨架、外表顯小（18 歲）", "慣用左手、極度沉默"],
    outfit=["現代：素色深色外套、乾淨俐落", "奇幻：全黑、低馬尾", "左腕內側青色紋身 51"],
    prompt="1boy, short black hair, blue eyes, small slender youth, silent blank expression, "
           "dark casual clothes, masterpiece, best quality"),
"南璐": dict(
    colors={"眼": "#5A3E2A 褐", "髮": "#6B4632 栗", "膚": "#F0DDCB"},
    look=["栗色短髮", "身形修長、行動俐落", "衣著簡潔實用", "公會會長秘書、成熟俐落"],
    outfit=["軍綠短外套、卡其／黑長褲、工裝", "耳環、俐落配件"],
    prompt="1girl, chestnut short hair, sharp composed expression, olive military jacket, "
           "cargo pants, earring, practical outfit, masterpiece, best quality"),
"耶里昂": dict(
    colors={"眼": "#4A3121 咖啡", "髮": "#6E3F2A 赤褐", "膚": "#EBD3BE"},
    look=["赤褐色頭髮、咖啡色眼", "中等身材、手臂與指節佈滿老繭疤痕（25 歲）", "健談、脾氣好"],
    outfit=["厚皮背心、多口袋工作褲、腰掛工具袋", "身上常沾油漬灰塵；現代亦常見大衣圍巾"],
    prompt="1boy, messy reddish brown hair, brown eyes, average build, calloused hands, "
           "leather vest, utility work pants, tool belt, easygoing smile, masterpiece, best quality"),
"苑": dict(
    colors={"眼": "#8B8B92 灰", "髮": "#9A9AA1 灰", "膚": "#F0EAE6", "招牌": "#E6E6E8 冷白／霧灰袍"},
    look=["如水洗墨的灰髮與灰眼", "五官乾淨、氣質冷靜、存在感強（23 歲）", "常伴白蛇璱（盤在肩上）"],
    outfit=["高領、收腰、無皺摺長袍", "冷白或霧灰色系、面料如霧面紙張"],
    prompt="1boy, straight grey hair, grey eyes, clean calm cold features, high-collar fitted "
           "long robe, pale white and misty grey clothes, elegant, masterpiece, best quality"),
}

def refs(name):
    fs = sorted(glob.glob(f"{GAL}/{name}/{name}_*"))
    return [os.path.basename(f) for f in fs]

def write_style(name, d):
    imgs = refs(name)
    lines = [f"---", f"character: {name}", "set: 艾弍大陸", "type: style-reference", "---", "",
             f"# {name} — 畫風與外型參考", "",
             "依角色卡設定與作者參考圖整理，作為生圖與一致性的基準。", ""]
    cols = d.get("colors")
    if cols:
        lines += ["## 重點色號（建議值，可調）", "", "| 部位 | 色號 |", "|------|------|"]
        lines += [f"| {k} | `{v}` |" for k, v in cols.items()]
        lines += [""]
    lines += ["## 外型 canon"]
    lines += [f"- {x}" for x in d["look"]]
    lines += ["", "## 招牌服裝"]
    lines += [f"- {x}" for x in d["outfit"]]
    lines += ["", "## 畫風", STYLE_LINE, "",
              "## 生圖 prompt（danbooru 標籤式，適合 PixAI / Illustrious）",
              f"> {d['prompt']}", "",
              "## 參考圖檔（本資料夾）"]
    lines += [f"- `{i}`" for i in imgs] if imgs else ["- （尚無）"]
    lines.append("")
    open(f"{GAL}/{name}/STYLE.md", "w", encoding="utf-8").write("\n".join(lines))
    print("STYLE:", name, f"({len(imgs)} 圖)")

def patch_card(name, prompt, colors=None):
    p = f"{CHAR}/{name}.md"
    if not os.path.exists(p):
        print("  ! 找不到角色卡", p); return
    t = open(p, encoding="utf-8").read()
    cblock = ""
    if colors:
        for key, field in (("眼", "eye_color"), ("髮", "hair_color")):
            if colors.get(key):
                cblock += f"{field}: {colors[key]}\n"
    block = (f"image_prompt: >\n  {prompt}\n"
             f"{cblock}"
             f"style_ref: gallery/{name}/STYLE.md\n")
    # 取代既有 image_prompt 區塊（含其後可能的 style_ref），直到下一個頂層鍵或 frontmatter 結尾
    new = re.sub(r"image_prompt: >\n(?:  .*\n)*"
                 r"(?:eye_color: .*\n)?(?:hair_color: .*\n)?(?:style_ref: .*\n)?",
                 block, t, count=1)
    if new == t:  # 沒有既有 image_prompt，插在 status 後
        new = re.sub(r"(status: .*\n)", r"\1" + block, t, count=1)
    open(p, "w", encoding="utf-8").write(new)
    print("  卡片 image_prompt 已更新:", name)

for name, d in DATA.items():
    write_style(name, d)
    patch_card(name, d["prompt"], d.get("colors"))
print("完成")
