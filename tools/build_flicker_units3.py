#!/usr/bin/env python3
"""hatena_flicker unit 化 v3（決定論）— 作者ごとに 1 unit、作者はエントリ URL のセグメントから。

- 全クロールページをパース（日付/月/ワード/アーカイブ/トップ/コメント）。
- 作者・日付はエントリ URL（/<user>/<YYYYMMDD>/<epoch>）から機械導出（ページ見出しに依存しない）。
- 収録日（ファイル名末尾 14 digit crawl_ts）より後日付のエントリはテストクロールとして除外。
- ページ装飾行（ブックマーク画像・トラックバック行・コメント投稿リンク）は機械除去（本文のみ保持）。
- 同一 permalink 重複は初出採用。
産出: units.jsonl ＋ units/<uid>/posts/pNNNN.md（逐語チャンク）＋ structured.jsonl（body_sha1 検証）。"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RAW = Path(r"C:/Users/d5dx/Downloads/Code/YuragiWiki/raw/bbs/hatena_flicker")
MD = RAW / "md"
ENTRY = re.compile(r"^### \[[^\]]*\]\((?P<url>http://flicker\.g\.hatena\.ne\.jp/[a-zA-Z0-9_-]+/\d{8}/\d+)\)")
DATEHEAD = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\]")
TIME = re.compile(r"^\d{1,2}:\d{2}$")
NOISE = re.compile(r"b\.hatena\.ne\.jp|r\.hatena\.ne\.jp|トラックバック -|\[コメントを書く\]|\[コメント\]\(/")

def rd(p):
    t = p.read_bytes().decode("utf-8", "replace")
    return t.replace("\r\n", "\n").replace("\r", "\n")

def parse_file(text, crawl_iso):
    out = []
    date = None
    cur = None
    for ln in text.split("\n"):
        dm = DATEHEAD.match(ln)
        if dm:
            date = dm.group(1)
            continue
        em = ENTRY.match(ln)
        if em:
            if cur:
                out.append(cur)
            m = re.match(r"http://flicker\.g\.hatena\.ne\.jp/[a-zA-Z0-9_-]+/(\d{4})(\d{2})(\d{2})/\d+", em.group("url"))
            url_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None
            cur = {"date": date, "url_date": url_date, "url": em.group("url"),
                   "time": "", "crawl": crawl_iso, "body": []}
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

def crawl_iso_of(p):
    m = re.search(r"(\d{4})(\d{2})(\d{2})\d{6}\.md$", p.name)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

def main():
    authors = {}
    n_files = 0
    for p in sorted(MD.glob("*.md")):
        n_files += 1
        cis = crawl_iso_of(p)
        for e in parse_file(rd(p), cis):
            m = re.match(r"http://flicker\.g\.hatena\.ne\.jp/([a-zA-Z0-9_-]+)/", e["url"])
            if not m:
                continue
            u = m.group(1).lower()
            authors.setdefault(u, {})[e["url"]] = e
    units = []
    total = 0
    dropped = 0
    for u, by_url in sorted(authors.items()):
        posts = []
        for e in by_url.values():
            d = e["url_date"]
            if not d:
                dropped += 1
                continue
            if e["crawl"] and d > e["crawl"]:
                dropped += 1  # クロール日より後日付＝テスト/先読みページ
                continue
            posts.append(e)
        posts.sort(key=lambda e: (e["url_date"], e["url"]))
        uid = f"YJ-F{u}"
        d = RAW / "units" / uid
        (d / "posts").mkdir(parents=True, exist_ok=True)
        recs = []
        for i, e in enumerate(posts, 1):
            body = "\n".join(l for l in e["body"] if not NOISE.search(l)).strip("\n")
            blk = f"### [{e['url'].rsplit('/', 1)[-1]}]({e['url']})\n{e['time']}\n{body}"
            (d / "posts" / f"p{i:04d}.md").write_bytes(blk.encode("utf-8"))
            recs.append({"post_no": i, "author": u, "date_iso": e["url_date"],
                         "url": e["url"], "time": e["time"],
                         "body_sha1": hashlib.sha1(blk.encode("utf-8")).hexdigest()})
        ok = sum(1 for i, rec in enumerate(recs, 1)
                 if hashlib.sha1((d / "posts" / f"p{i:04d}.md").read_bytes()).hexdigest() == rec["body_sha1"])
        (d / "structured.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
        units.append({"unit_id": uid, "title": f"{u} の日記（Hatena Flicker）",
                      "author": u, "source": "hatena_flicker",
                      "url": f"http://flicker.g.hatena.ne.jp/{u}/",
                      "n_posts": len(posts),
                      "first": posts[0]["url_date"] if posts else None,
                      "last": posts[-1]["url_date"] if posts else None,
                      "posts_sha1_verified": ok,
                      "path": f"units/{uid}"})
        total += len(posts)
    (RAW / "units.jsonl").write_text(
        "".join(json.dumps(u, ensure_ascii=False) + "\n" for u in units), encoding="utf-8")
    print(json.dumps({"files": n_files, "authors": len(authors),
                      "posts": total, "dropped": dropped, "units": len(units)},
                     ensure_ascii=False))
    print("FLICKER-L0-DONE")

main()
