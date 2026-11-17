#!/usr/bin/env python3
"""
fetch_recent_commits.py — GitHub API から vault（Obsidian）の直近コミットを取得し、
content/recent-commits.md を生成する。CI（deploy.yml）でビルド前に実行する。

- 認証不要（公開リポジトリの API・レート制限 60 回/時/IP）
- 直近 N 件（既定 100 件）を Markdown テーブルとして出力
- 日時は JST に変換
"""
import json
import os
import sys
import urllib.request
import urllib.error
import datetime

REPO = "allusionistwiki/AllusionistLLMWiki2_Obsidian"
OUT = "content/recent-commits.md"
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 100

def esc(s: str) -> str:
    # 角括弧を全角化: コミットメッセージ内の [[...]] が wikilink 化して
    # 存在しないスラッグへのリンク（broken）になるのを防ぐ。
    # \[ \] エスケープは micromark が先に解決してテキストノードで
    # [[...]] に復元されるため wikilink 正規表現を止められない（全角が確実）
    return s.replace("|", "\\|").replace("\n", " ").replace("[", "［").replace("]", "］")

def main():
    url = f"https://api.github.com/repos/{REPO}/commits?per_page={LIMIT}"
    tok = os.environ.get("GH_TOKEN", "")
    # 公開API 60回/時は共有IP（Actions runner）で枯渇し得る。CI はリトライ専用で
    # 失敗させない（レート制限 403/429 と一時的転送 5xx）。
    last_err: Exception | None = None
    commits = None
    for attempt in range(6):
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "quartz-ci"}
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                commits = json.load(r)
            break
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (403, 429, 500, 502, 503, 504):
                sys.stderr.write(f"github api {e.code}, retry {attempt + 1} in {2 ** attempt * 15}s\n")
                import time
                time.sleep(2 ** attempt * 15)
                continue
            raise
    else:
        raise last_err

    lines = [
        "---",
        "title: 直近コミット",
        "description: vault（Obsidian）の直近のコミット（自動生成）",
        "---",
        "",
        "# 直近コミット",
        "",
        f"vault（Obsidian）の直近のコミット {len(commits)} 件です（自動生成・GitHub API から取得）。",
        "",
        "| 日時 (JST) | コミット | メッセージ |",
        "|---|---|---|",
    ]
    for c in commits:
        sha = c["sha"]
        date = c["commit"]["author"]["date"]
        dt = datetime.datetime.fromisoformat(date.replace("Z", "+00:00"))
        jst = dt.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
        date_str = jst.strftime("%Y-%m-%d %H:%M")
        msg = esc(c["commit"]["message"].split("\n")[0])
        lines.append(
            f"| {date_str} | [{sha[:7]}](https://github.com/{REPO}/commit/{sha}) | {msg} |"
        )

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {OUT} with {len(commits)} commits")

if __name__ == "__main__":
    main()
