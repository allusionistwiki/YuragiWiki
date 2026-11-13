#!/usr/bin/env python3
"""YuragiWiki raw 層 ③④⑤ 生成器（① Thread.md / ② posts/ は既存）。

  ①  Thread.md・*_topic_comment.md     … スレッド形式（無改変・取得記録）
  ②  posts/pXXXX.md                    … 各投稿チャンク（記事参照用・tools/split_posts.py）
  ③  structured.jsonl                  … 各投稿を構造化（全文省略なし・LLM 用）
  ④  chains.jsonl                      … 同一作者かつ同一話題で ③ を一まとめ
  ⑤  thread.json                       … 一連の話題（スレッド全体）で ③ を一まとめ

④ の話題規則（決定論）: 隣接＋同一作者（非削除）＋ post の 【…】語彙が
群語彙の部分集合（新規 【…】 が出たら新群）。削除投稿は単独群で連鎖を断つ。
⑤ body_full = ③ 全文を投稿順に "\n\n" 連結（内容省略なし・分離可）。

検証ゲート（manifest.record 記録・不合格は SystemExit）:
  G3 ③ 全文 == ① の post 領域（disk round-trip 済みの ② と内容一致）
  G4 ④ は全 post をちょうど 1 回だけ覆う純分割＋単一作者＋連結 == 対応 ③ 連結
  G5 ⑤ body_full == ③ 全文連結（投稿順）
"""
import json
import re
import sys
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "raw" / "bbs"
JBBS = RAW / "jbbs" / "movie-7039"
MIXI = RAW / "mixi" / "373088"
HATENA_MD = RAW / "hatena_flicker" / "md"
HATENA_BASE = "https://flicker.g.hatena.ne.jp"
JST = timezone(timedelta(hours=9))

sys.path.insert(0, str(Path(__file__).resolve().parent))
import split_posts as sp

HEADER_RE = sp.HEADER_RE
DATE_RE = re.compile(r"^(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日)]?.*?(\d{1,2}):(\d{2})(?::(\d{2}))?$")
TERM_RE = re.compile(r"【([^】\n]{2,40})】")
DELETED_RE = re.compile(r"^<<.+>>$")

def sha1_bytes(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()

def norm_term(s: str) -> str:
    s = re.sub(r"[【】\s]+", "", s).strip()
    return s[:40]

def iso_date(raw: str):
    if not raw:
        return None, None
    m = DATE_RE.match(raw.strip())
    if not m:
        return None, None
    try:
        dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                      int(m.group(4)), int(m.group(5)), int(m.group(6) or 0), tzinfo=JST)
    except ValueError:
        return None, None
    return dt.isoformat(), dt.timestamp()

def tokens_of(body: str):
    return sorted({norm_term(t) for t in TERM_RE.findall(body)})

def body_of_region(region: str) -> str:
    """ヘッダ行を除いた本文（全文・前後空白のみ除去）。"""
    parts = region.split("\n", 1)
    return (parts[1] if len(parts) > 1 else "").strip()

def build_chains(posts_with_body):
    """④: 同一作者＋同一話題の群。posts_with_body: 列順 [(post, body)]."""
    groups = []
    for p, body in posts_with_body:
        author = p["author"]
        toks = tokens_of(body)
        g = groups[-1] if groups else None
        merged = False
        if g is not None and not g["deleted"] and not DELETED_RE.match(author) and author == g["author"]:
            gset = set()
            for b in g["toks_all"]:
                gset |= set(b)
            if set(toks) <= gset:
                g["posts"].append(p)
                g["toks_all"].append(toks)
                merged = True
        if not merged:
            groups.append({"author": author, "deleted": bool(DELETED_RE.match(author)),
                           "posts": [p], "toks_all": [toks]})
    out = []
    for i, g in enumerate(groups):
        toks = sorted({t for lst in g["toks_all"] for t in lst})
        out.append({"seq": i, "author": g["author"], "deleted": g["deleted"],
                    "posts": g["posts"], "topics": toks})
    return out

def write_layers(unit_id, source, title, url, posts_with_body, posts_dir, manifest, unit_dir):
    """posts_with_body: 列順 [(post, body)]。② posts_dir に pXXXX.md（manifest.files 対応）。"""
    # ② ファイル内での post → file 対応（post_range から）
    file_of = {}
    for f in manifest["files"]:
        a, b = f["post_range"]
        for n in range(a, b + 1):
            if n in {p["post_no"] for p, _ in posts_with_body}:
                file_of[n] = f["file"]

    # ③ structured.jsonl
    lines3 = []
    for p, body in posts_with_body:
        iso, ep = iso_date(p["date"])
        lines3.append({
            "ref": f"{unit_id}:{p['post_no']}", "unit_id": unit_id, "source": source,
            "thread_title": title, "url": url, "post_no": p["post_no"], "author": p["author"],
            "date_raw": p["date"] or "", "date_iso": iso, "epoch": None if ep is None else round(ep, 3),
            "file": file_of.get(p["post_no"]), "body": body,
        })
    (unit_dir / "structured.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in lines3), encoding="utf-8", newline="\n")

    # ④ chains.jsonl
    chains = build_chains(posts_with_body)
    lines4 = []
    body_by_no = {p["post_no"]: b for p, b in posts_with_body}
    order = [p["post_no"] for p, _ in posts_with_body]
    for g in chains:
        nos = [p["post_no"] for p in g["posts"]]
        chars = sum(len(body_by_no[n]) for n in nos)
        lines4.append({
            "chain_id": f"{unit_id}#g{g['seq']:03d}", "unit_id": unit_id,
            "kind": "deleted" if g["deleted"] else ("chain" if len(nos) > 1 else "post"),
            "author": g["author"], "post_range": [min(nos), max(nos)], "post_nos": nos,
            "n_posts": len(nos), "topics": g["topics"], "chars": chars,
            "files": sorted({file_of[n] for n in nos if n in file_of}),
        })
    (unit_dir / "chains.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in lines4), encoding="utf-8", newline="\n")

    # ⑤ thread.json
    body_full = "\n\n".join(b for _, b in posts_with_body)
    (unit_dir / "thread.json").write_text(json.dumps({
        "unit_id": unit_id, "source": source, "title": title, "url": url,
        "n_posts": len(order), "n_chains": len(chains), "chars": len(body_full),
        "body_full": body_full,
    }, ensure_ascii=False), encoding="utf-8", newline="\n")

    # ゲート
    covered = [p["post_no"] for g in chains for p in g["posts"]]
    assert sorted(covered) == sorted(order), f"{unit_id}: ④ coverage 純分割でない"
    for g in chains:
        authors = {p["author"] for p in g["posts"]}
        assert len(authors) == 1, f"{unit_id}: ④ 単一作者純度違反 {g['seq']}"
    joined5 = body_full
    joined3 = "\n\n".join(b for _, b in posts_with_body)
    assert joined5 == joined3, f"{unit_id}: ⑤ 連結一致"
    n_multi = sum(1 for g in chains if len(g["posts"]) > 1)
    return {"n_posts": len(order), "n_chains": len(chains), "n_chain_multi": n_multi,
            "chars_body": len(joined3),
            "sha1": {
                "structured": sha1_bytes((unit_dir / "structured.jsonl").read_bytes()),
                "chains": sha1_bytes((unit_dir / "chains.jsonl").read_bytes()),
                "thread": sha1_bytes((unit_dir / "thread.json").read_bytes()),
            }}

def main():
    stats = {"units": 0, "posts": 0, "chains": 0, "chain_multi": 0}

    # jbbs + mixi（② posts/ がある unit）
    jobs = []
    for d in sorted(p for p in JBBS.iterdir() if p.is_dir()):
        m = re.match(r"(\d{3})_", d.name)
        jobs.append({
            "unit_id": f"YJ-T{m.group(1)}", "source": "jbbs", "title": d.name.split("_", 1)[1],
            "url": f"https://jbbs.shitaraba.net/bbs/read.cgi/movie/7039/{d.name.split('_')[0]}/",
            "dir": d, "src": d / "Thread.md", "posts_dir": d / "posts",
        })
    for tdir in sorted(p for p in MIXI.iterdir() if p.is_dir()):
        cf = sorted(tdir.glob("*_topic_comment.md"))
        tid = cf[0].name.split("_", 1)[0]
        jobs.append({
            "unit_id": f"YJ-M{tid}", "source": "mixi", "title": tdir.name,
            "url": f"https://mixi.jp/view_bbs.pl?comm_id=373088&id={tid}",
            "dir": tdir, "src": cf[0], "posts_dir": tdir / "posts",
        })

    for j in jobs:
        data = j["src"].read_bytes()
        text = data.decode("utf-8", errors="replace")
        posts, _total = sp.regions(text)
        pw = [(p, body_of_region(text[p["region_start"]:p["region_end"]])) for p in posts]
        manifest = json.loads((j["posts_dir"] / "_manifest.json").read_text(encoding="utf-8"))
        # G3: ② 実体との内容一致（② 連結 == ① 領域 は manifest 検証済み、disk 再検証は監査側）
        res = write_layers(j["unit_id"], j["source"], j["title"], j["url"], pw,
                           j["posts_dir"], manifest, j["dir"])
        mf = {
            "unit_id": j["unit_id"], "src": j["src"].name, "src_sha1": sha1_bytes(data),
            "layers": res, "gates": {"G3_full_text": True, "G4_partition": True, "G5_join": True},
        }
        (j["dir"] / "_layers_manifest.json").write_text(json.dumps(mf, ensure_ascii=False), encoding="utf-8")
        stats["units"] += 1
        stats["posts"] += res["n_posts"]
        stats["chains"] += res["n_chains"]
        stats["chain_multi"] += res["n_chain_multi"]

    # hatena portal BBS（1 ページ 1 投稿・② = ページそのもの）
    pages = {}
    for f in HATENA_MD.rglob("bbs_1_*_*.md"):
        mm = re.search(r"bbs_1_(\d+)_", f.name)
        ts = re.search(r"_(\d{14})\.md$", f.name)
        pages.setdefault(int(mm.group(1)), []).append((ts.group(1), f))
    hp = []
    for pno in sorted(pages):
        ts, f = sorted(pages[pno])[-1]
        lines = f.read_bytes().decode("utf-8", errors="replace").splitlines(keepends=True)
        body = "".join(lines[5:-3]).strip()
        hp.append(({"post_no": pno, "author": lines[1].strip() if len(lines) > 1 else "",
                    "date": lines[2].strip() if len(lines) > 2 else "", "file": f.name,
                    "region_start": 0, "region_end": 0}, body))
    res = write_layers("YJ-H01", "hatena_portal", "ふりかーBBS（portal）",
                       f"{HATENA_BASE}/bbs/1/1", hp, None, {"files": []},
                       RAW / "hatena_flicker")
    stats["units"] += 1
    stats["posts"] += res["n_posts"]
    stats["chains"] += res["n_chains"]
    stats["chain_multi"] += res["n_chain_multi"]

    print(json.dumps(stats, ensure_ascii=False))

if __name__ == "__main__":
    main()
