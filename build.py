#!/usr/bin/env python3
"""產生 index.html：讀取同資料夾內的教案、網頁資源與影片資料，內嵌到 template.html。

影片來源：
- other_videos.json + other_meta.txt：台灣與其他國家頻道的影片（逐支看過畫面挑選）
- rehashine_database.json：REHA SHINE 團康影片，只保留 REHA_KEEP 名單內、適合失智長輩的影片
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
rd = lambda n: json.loads((ROOT / n).read_text(encoding="utf-8"))

lessons = rd("lessons.json")
resources = rd("resources.json")
raw = rd("rehashine_database.json")
other = rd("other_videos.json")
meta = {}
for line in (ROOT / "other_meta.txt").read_text(encoding="utf-8").splitlines():
    if line.strip():
        vid, ch, ln, views, date = line.strip().split("~")
        meta[vid] = (ch, int(ln), int(views), date)

# 坐姿、規則簡單、免自製大型教具、觀看數較高的 REHA SHINE 影片
REHA_KEEP = """h5W-ASCZLyU y3vQanpW4d8 HgPL4mGoXz4 UYRDqa0VM0g e5HEQrITBzs ZvToEppP3Fw xWo8VmeVbp0
zDJkygdtXvc bcgMbb4fCqg Bw8ODMVjcIw YY1hTFjfCw8 8HhkzjpYEg0 ahlncZZBUkM 1qVIeSXLTuQ Zm0BIDQ_LY8
cF4Jw1Ixehc B0YxzoevPrA aYRjuQWNmCk YqB98DcrQr4 yCDFYnXAmPY l6yzdYCF9bU jKmK8G9lIhs PPyh-tgtJYI""".split()

LONG_OVERRIDE = {"vkSjhacD0EA"}


def lt(sec):
    if sec is None:
        return ""
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


GENERIC_TIP = "影片是帶領參考，請依長輩當天的能力與狀態調整速度、次數與難度。"
TIP_SEVERE = "中重度長輩可由照顧者在旁示範或手把手協助，碰到、參與就算成功。"
TIP_STAND = "影片為站姿，失智或平衡較差的長輩請改坐姿進行，旁邊安排人員保護。"

videos = []
for vid, region, t, how, goals, part, pos, props, lv, st in other:
    ch, ln, views, date = meta[vid]
    tips = [GENERIC_TIP]
    if "重度" in lv:
        tips.append(TIP_SEVERE)
    if "站姿" in pos:
        tips.append(TIP_STAND)
    videos.append({
        "id": vid, "fmt": "Shorts" if ln <= 60 and vid not in LONG_OVERRIDE else "長片",
        "t": t, "jp": "", "how": how, "goals": goals, "part": part, "pos": pos, "props": props,
        "prep": "", "tips": tips, "lv": lv, "set": st, "len": ln, "lt": lt(ln), "views": views,
        "date": date, "ch": ch, "region": region, "src": "curated",
    })

for v in raw:
    if v["video_id"] not in REHA_KEEP:
        continue
    videos.append({
        "id": v["video_id"], "fmt": "Shorts" if v["format"] == "Shorts" else "長片",
        "t": v["zh_title"], "jp": v["jp_title"], "how": v["how_to_play"],
        "goals": v["training_goals"], "part": v["participation"], "pos": v["posture"],
        "props": v["props"], "prep": "", "tips": v["leading_tips"][:2],
        "lv": ["輕度", "中度", "重度"], "set": ["據點", "日照"] + (["居家"] if set(v["participation"]) & {"個人挑戰", "雙人搭檔"} else []),
        "len": v["length_sec"], "lt": v["length_text"], "views": v["views"], "date": v["publish_date"],
        "ch": "REHA SHINE（宮崎縣日照中心）", "region": "日本", "src": "curated",
    })

ids = {v["id"] for v in videos}
for L in lessons:
    missing = [i for i in L["vids"] if i not in ids]
    assert not missing, (L["id"], missing)
    L["videos"] = L.pop("vids")

tpl = (ROOT / "template.html").read_text(encoding="utf-8")
payload = json.dumps({"lessons": lessons, "resources": resources, "videos": videos}, ensure_ascii=False, separators=(",", ":"))
(ROOT / "index.html").write_text(tpl.replace("/*__DATA__*/", "window.DB=" + payload + ";"), encoding="utf-8")

from collections import Counter
print("videos", len(videos), Counter(v["region"] for v in videos), Counter(v["fmt"] for v in videos))
print("channels", len({v["ch"] for v in videos}))
print("lessons with videos", sum(bool(L["videos"]) for L in lessons), "/", len(lessons))
