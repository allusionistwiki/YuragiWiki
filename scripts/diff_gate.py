#!/usr/bin/env python3
"""CI 差分ビルドの gate（manifest v2 版）: 削除・移動・大規模変更を検知する。

使い方: python3 scripts/diff_gate.py <prev-manifest.json> <content-dir>

manifest v2（public/index.json）= { manifestVersion: 2, pages: { <content相対mdパス>: sha256 } }。

full ビルドへ逃がす条件（exit 1）:
  - manifest が manifestVersion 2 でない（旧形式・壊れ）
  - manifest にある .md が新 content に存在しない（ページ削除・移動）
  - 差分ページ数が多すぎる（大半が変わるなら差分の意味がない = full の方が速い）
それ以外（追加・少数変更）は exit 0（差分ビルドへ）。
"""
import hashlib
import json
import sys
from pathlib import Path

MAX_DIFF_PAGES = 800


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: diff_gate.py <prev-manifest.json> <content-dir>")
        return 2
    manifest_path, content_dir = sys.argv[1], Path(sys.argv[2])

    try:
        raw = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"gate: manifest unreadable: {e}")
        return 1
    if raw.get("manifestVersion") != 2:
        print("gate: manifest is not manifestVersion 2")
        return 1
    prev = raw.get("pages", {})

    new_hashes = {}
    for p in content_dir.rglob("*.md"):
        rel = p.relative_to(content_dir).as_posix()
        new_hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()

    deleted = sorted(set(prev) - set(new_hashes))
    changed = sum(1 for r, h in new_hashes.items() if prev.get(r) != h)
    added = len(set(new_hashes) - set(prev))
    print(
        f"gate: prev={len(prev)} new={len(new_hashes)} added={added} changed={changed} deleted={len(deleted)}"
    )
    for s in deleted[:20]:
        print(f"  deleted: {s}")
    if deleted:
        return 1
    if changed > MAX_DIFF_PAGES:
        print(f"gate: too many changed pages ({changed} > {MAX_DIFF_PAGES}) — full build is faster")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
