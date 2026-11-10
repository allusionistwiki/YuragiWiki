#!/usr/bin/env python3
"""YuragiWiki raw 層: 掲示板スレの投稿単位ファイル化（チャンク化）.

意味論（2026-11-11 ユーザー確定）:
- 各 BBS の各投稿を 1 ファイルに切り分ける。
- 同一投稿者の隣接連投は 1 ファイルにまとめる（連投群 = 1 ファイル）。
- 削除投稿（したらば `<<名前削除>>` 系）は連結を断ち、単独ファイル。

もとの Thread.md / *_topic_comment.md は取得記録として無改変（書換・削除しない）。
切り分け産出は各篇ディレクトリの `posts/` に追加する:
    posts/p0001.md          — 1 投稿
    posts/p0123-0127.md     — 連投群（同一投稿者の隣接レス）
    posts/_manifest.json    — 篇_manifest（元ファイル sha1・ファイル別 region/post_range）

損失なし保証: 全 group ファイルの連結 == 元ファイルの「最初のレスヘッダ開始〜最終レス末尾」領域
（前文ヘッダブロック・後文は元ファイルに残る。manifest に preamble_len/footer_len を記録）。
はてな portal BBS（bbs/1）は 1 ページ 1 投稿で既に投稿単位 = split 対象外。
"""
import json
import re
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # YuragiWiki repo
BBS = ROOT / "raw" / "bbs"

HEADER_RE = re.compile(
    r"^## (\d+) ：(.*?) ：((?:\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日)]?.*?\d{1,2}:\d{2}(?::\d{2})?)?)\s*$"
)
DELETED_RE = re.compile(r"^<<.+>>$")


def sha1_bytes(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


def regions(text: str):
    """各レスの [region_start, region_end)（元テキスト上の char 境界・ヘッダ含む）とメタを返す。"""
    lines = text.splitlines(keepends=True)
    offs, acc = [], 0
    for ln in lines:
        offs.append(acc)
        acc += len(ln)
    heads = []
    for i, ln in enumerate(lines):
        m = HEADER_RE.match(ln.rstrip("\r\n"))
        if m:
            heads.append((i, m))
    out = []
    for k, (i, m) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        start = offs[i]
        stop = offs[end - 1] + len(lines[end - 1])
        out.append(
            {
                "post_no": int(m.group(1)),
                "author": m.group(2).strip(),
                "date": (m.group(3) or "").strip(),
                "region_start": start,
                "region_end": stop,
                "chars": len(text[start:stop].strip()),
            }
        )
    return out, len(text)


def group_posts(posts):
    groups = []
    for p in posts:
        deleted = bool(DELETED_RE.match(p["author"]))
        g = groups[-1] if groups else None
        if g and not deleted and not g["deleted"] and p["author"] == g["author"]:
            g["posts"].append(p)
        else:
            groups.append({"author": p["author"], "deleted": deleted, "posts": [p]})
    return groups


def group_filename(posts):
    a = posts[0]["post_no"]
    b = posts[-1]["post_no"]
    # 群の post 範囲は群間で互いに素 → この名前は一意的
    return f"p{a:04d}.md" if len(posts) == 1 else f"p{a:04d}-{b:04d}.md"


def split_unit(src: Path, posts_dir: Path):
    data = src.read_bytes()
    text = data.decode("utf-8", errors="replace")
    posts, total_len = regions(text)
    if not posts:
        return {"src": str(src), "posts": 0, "groups": 0, "verify": "no-posts"}
    groups = group_posts(posts)
    posts_dir.mkdir(parents=True, exist_ok=True)
    files = []
    concat = []
    for g in groups:
        gp = g["posts"]
        seg = text[gp[0]["region_start"]: gp[-1]["region_end"]]
        fname = group_filename(gp)
        (posts_dir / fname).write_text(seg, encoding="utf-8")
        concat.append(seg)
        files.append(
            {
                "file": fname,
                "author": g["author"],
                "deleted": g["deleted"],
                "post_range": [gp[0]["post_no"], gp[-1]["post_no"]],
                "n_posts": len(gp),
                "region_start": gp[0]["region_start"],
                "region_end": gp[-1]["region_end"],
                "sha1": sha1_bytes(seg.encode("utf-8")),
            }
        )
    joined = "".join(concat)
    ok = joined == text[posts[0]["region_start"]: posts[-1]["region_end"]]
    manifest = {
        "src": src.name,
        "src_sha1": sha1_bytes(data),
        "n_posts": len(posts),
        "n_groups": len(groups),
        "preamble_len": posts[0]["region_start"],
        "footer_len": total_len - posts[-1]["region_end"],
        "verify_concat_exact": ok,
        "files": files,
    }
    (posts_dir / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return {"src": str(src.relative_to(ROOT)), "posts": len(posts), "groups": len(groups),
            "verify": "exact" if ok else "FAIL"}


def main():
    results = []
    jbbs = BBS / "jbbs" / "movie-7039"
    for d in sorted(p for p in jbbs.iterdir() if p.is_dir()):
        src = d / "Thread.md"
        if src.exists():
            results.append(split_unit(src, d / "posts"))
    mixi = BBS / "mixi" / "373088"
    for d in sorted(p for p in mixi.iterdir() if p.is_dir()):
        for cf in sorted(d.glob("*_topic_comment.md")):
            results.append(split_unit(cf, d / "posts"))
    fails = [r for r in results if r["verify"] not in ("exact",)]
    tot = {
        "units": len(results),
        "posts": sum(r["posts"] for r in results),
        "groups": sum(r["groups"] for r in results),
        "verify_fail": len(fails),
    }
    print(json.dumps(tot, ensure_ascii=False))
    for f in fails[:10]:
        print("FAIL", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
