#!/usr/bin/env python3
"""產生 index.html：讀取同資料夾內的教案、網頁資源與 REHA SHINE 影片資料，內嵌到 template.html。"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
D = ROOT

lessons = json.loads((D / "lessons.json").read_text(encoding="utf-8"))
resources = json.loads((D / "resources.json").read_text(encoding="utf-8"))
raw = json.loads((D / "rehashine_database.json").read_text(encoding="utf-8"))

COG = ["相反", "喊", "數字", "漢字", "排序", "計時", "記住", "猜", "口令", "國旗", "指令", "主題卡", "加總", "計算"]
PRECISE = ["平衡", "迷宮", "控", "軌道", "夾", "疊", "架橋", "立盤"]
GROUPY = {"團隊合作", "競賽對戰", "接力傳遞"}
EASY_PROPS = {"氣球", "毛巾／大布", "扇子", "沙包"}


def dementia_levels(v):
    if v["category"] in ("教具製作與介紹", "媒體報導"):
        return []
    t = v["zh_title"] + v["how_to_play"]
    if any(k in t for k in COG):
        return ["輕度"]
    if "站姿" in v["posture"]:
        return ["輕度", "中度"]
    if any(k in t for k in PRECISE) or GROUPY & set(v["participation"]):
        return ["輕度", "中度"]
    return ["輕度", "中度", "重度"]


def settings(v):
    s = ["據點", "日照"]
    solo = set(v["participation"]) & {"個人挑戰", "雙人搭檔"}
    if solo and v["prep_level"] != "需自製教具" and "牆面／立架" not in v["place"]:
        s.append("居家")
    if v["category"] == "毛巾遊戲（レクル系列）" and "居家" not in s:
        s.append("居家")
    return s


videos = []
for v in raw:
    lv = dementia_levels(v)
    videos.append({
        "id": v["video_id"],
        "rs": v["id"],
        "fmt": "Shorts" if v["format"] == "Shorts" else "長片",
        "cat": v["category"],
        "t": v["zh_title"],
        "jp": v["jp_title"],
        "how": v["how_to_play"],
        "goals": v["training_goals"],
        "part": v["participation"],
        "pos": v["posture"],
        "props": v["props"],
        "prep": v["prep_level"],
        "tips": v["leading_tips"],
        "lv": lv,
        "set": settings(v),
        "len": v["length_sec"],
        "lt": v["length_text"],
        "views": v["views"],
        "date": v["publish_date"],
        "ch": "REHA SHINE",
        "src": "rs",
    })

# 為教案配對影片：依關鍵字與道具計分，挑出最適合失智長輩（程度涵蓋較廣）的影片
for L in lessons:
    kws, props = L["vid"]["kw"], set(L["vid"]["props"])
    scored = []
    if kws or props:
        for v in videos:
            if not v["lv"]:
                continue
            text = v["t"] + v["how"]
            s = sum(3 for k in kws if k in text) + 2 * len(props & set(v["props"]))
            if s == 0:
                continue
            s += len(set(v["lv"]) & set(L["stages"]))
            s += min(v["views"], 50000) / 50000
            scored.append((s, v["id"]))
    scored.sort(reverse=True)
    L["videos"] = [i for _, i in scored[:6]]
    del L["vid"]

tpl = (ROOT / "template.html").read_text(encoding="utf-8")
payload = json.dumps({"lessons": lessons, "resources": resources, "videos": videos}, ensure_ascii=False, separators=(",", ":"))
out = tpl.replace("/*__DATA__*/", "window.DB=" + payload + ";")
(ROOT / "index.html").write_text(out, encoding="utf-8")

from collections import Counter
print("lessons", len(lessons), "resources", len(resources), "videos", len(videos))
print("levels", Counter(",".join(v["lv"]) for v in videos))
print("home", sum("居家" in v["set"] for v in videos))
for L in lessons:
    print(L["id"], L["title"], len(L["videos"]))
