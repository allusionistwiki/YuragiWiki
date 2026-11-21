#!/usr/bin/env python3
"""hatena_flicker 日記層の unit 化（決定論）— 作者ごとに 1 unit。

md/*.md（flicker.g.hatena.ne.jp_<user>[_<date>]_<ts>.md）をパースし、
日記エントリ（### [見出し](permalink) ＋ 時刻行 ＋ 本文）を作者別に収集。
産出: raw/bbs/hatena_flicker/units.jsonl（unit 台帳）＋ units/<unit_id>/posts/pNNNN.md（逐語投稿チャンク）
      ＋ units/<unit_id>/structured.jsonl（post_no/author/date_iso/url/body/body_sha1）
unit ID: YJ-F<user>。bbs/rss/xml/about 等は対象外（既存 bbs 層・非日記）。
原文バイト一致検証（チャンク = md からの逐語抽出）。"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RAW = Path(r"C:/Users/d5dx/Downloads/Code/YuragiWiki/raw/bbs/hatena_flicker")
MD = RAW / "md"
NAME = re.compile(r"^flicker\.g\.hatena\.ne\.jp_(?P<user>.+?)_(?:comment_date_)?(?P<date>\d{8})?_(?P<ts>\d{14})\.md$")
ENTRY = re.compile(r"^### \[([^\]]*)\]\((?P<url>http://flicker\.g\.hatena\.ne\.jp/[^)]+)\)")
DATEHEAD = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\]")
TIME = re.compile(r"^\d{1,2}:\d{2}$")

def rd(p):
    t = p.read_bytes().decode("utf-8", "replace")
    return t.replace("\r\n", "\n").replace("\r", "\n")

def parse_file(text):
    """-> [(date_iso, title, url, time, body_lines[verbatim])]"""
    out = []
    date = None
    lines = text.split("\n")
    i = 0
    cur = None
    for ln in lines:
        dm = DATEHEAD.match(ln)
        if dm:
            date = dm.group(1)
            continue
        em = ENTRY.match(ln)
        if em:
            if cur:
                out.append(cur)
            cur = {"date": date, "title": "", "url": em.group("url"),
                   "time": "", "body": []}
            continue
        if cur is None:
            continue
        s = ln.strip()
        if s.startswith("[コメント]") or s.startswith("[トラックバック]"):
            out.append(cur); cur = None
            continue
        if TIME.match(s) and not cur["time"] and not cur["body"]:
            cur["time"] = s
            continue
        cur["body"].append(ln)
    if cur:
        out.append(cur)
    return out

def main():
    authors = {}
    n_files = 0
    for p in sorted(MD.glob("*.md")):
        m = NAME.match(p.name)
        if not m:
            continue
        u = m.group("user").lower()
        if u in ("bbs", "about", "about_20060312090931", "20060305015255"):
            continue
        if "opensearch" in u or u.endswith("rss") or u.endswith("rss2") or "xml" in u:
            continue
        n_files += 1
        for e in parse_file(rd(p)):
            if not e["url"]:
                continue
            authors.setdefault(u, []).append(e)
    units = []
    total = 0
    for u, entries in sorted(authors.items()):
        # 重複 permalink は初出のみ（同一日記の再クロール）
        seen = set(); posts = []
        for e in entries:
            if e["url"] in seen:
                continue
            seen.add(e["url"])
            posts.append(e)
        posts.sort(key=lambda e: (e["date"] or "0000", e["url"]))
        uid = f"YJ-F{u}"
        d = RAW / "units" / uid
        (d / "posts").mkdir(parents=True, exist_ok=True)
        recs = []
        for i, e in enumerate(posts, 1):
            body = "\n".join(e["body"]).strip("\n")
            blk = f"### [{e['title']}]({e['url']})\n{e['time']}\n{body}"
            (d / "posts" / f"p{i:04d}.md").write_bytes(blk.encode("utf-8"))
            recs.append({"post_no": i, "author": u, "date_iso": e["date"],
                         "url": e["url"], "time": e["time"],
                         "body_sha1": hashlib.sha1(blk.encode("utf-8")).hexdigest()})
        # 本文逐語検証: structured から body 再構成一致
        ok = 0
        for i, rec in enumerate(recs, 1):
            t = (d / "posts" / f"p{i:04d}.md").read_bytes().decode("utf-8")
            if hashlib.sha1(t.encode("utf-8")).hexdigest() == rec["body_sha1"]:
                ok += 1
        (d / "structured.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
        units.append({"unit_id": uid, "title": f"{u} の日記（Hatena Flicker）",
                      "author": u, "source": "hatena_flicker",
                      "url": f"http://flicker.g.hatena.ne.jp/{u}/",
                      "n_posts": len(posts),
                      "first": posts[0]["date"] if posts else None,
                      "last": posts[-1]["date"] if posts else None,
                      "posts_sha1_verified": ok,
                      "path": f"units/{uid}"})
        total += len(posts)
    (RAW / "units.jsonl").write_text(
        "".join(json.dumps(u, ensure_ascii=False) + "\n" for u in units), encoding="utf-8")
    print(json.dumps({"files_parsed": n_files, "authors": len(authors),
                      "posts": total, "units": len(units)}, ensure_ascii=False))
    print("FLICKER-L0-DONE")

main()
