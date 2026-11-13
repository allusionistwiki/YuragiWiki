# YuragiWiki

『ゆらぎの神話』— 多人数で神話を創る試みの解析 wiki ＋ 記述（原文）アーカイブ。

## 内容

- `raw/bbs/jbbs/movie-7039/` — 外部BBS「ゆらぎの神話BBS」（したらば movie/7039）全スレ・全レス
- `raw/bbs/mixi/373088/` — mixi コミュ「架空の神話を作ろう」全トピック・全コメント
- `raw/bbs/**/posts/` — **② 投稿チャンク層（記事参照用）**: 各 BBS の各投稿を 1 ファイルに切り分けた層。
  同一投稿者の隣接連投は 1 ファイルに統合（`p0123-0127.md` 形式・単独は `p0001.md`）。
  各篇の `posts/_manifest.json` に元ファイル SHA1・領域・disk round-trip 検証記録。
  生成: `tools/split_posts.py`（元ファイルは無改変）。はてな portal BBS（bbs/1）は 1 ページ 1 投稿のため対象外。
- **③ `structured.jsonl`（各篇・LLM 用）**: 各投稿を構造化レコード化（unit_id・post_no・作者・日時・URL・**全文省略なし**）。
- **④ `chains.jsonl`（各篇）**: 同一作者かつ同一話題で ③ を一まとめ。話題規則（決定論）: 隣接＋同一作者＋【…】語彙が群語彙の部分集合なら merge、新規【…】で新群、削除投稿は連鎖を断つ。
- **⑤ `thread.json`（各篇）**: 一連の話題（スレッド全体）で ③ を一まとめ（全文投稿順連結）。
- 各篇 `_layers_manifest.json`（③④⑤ SHA1・検証記録）。生成: `tools/build_raw_layers.py`（①〜⑤ の対応は README・tools 冒頭）。
- 台帳（unit ID 台帳・アンカー・索引）は work repo `AllusionistWiki_work/work/yuragi/` 側。
- unit ID: `YJ-T###`（したらば篇）/ `YJ-M<トピックID>`（mixi）/ `YJ-H01`（portal BBS）。
- （今後）はてなふりかー日記ページ（`raw/bbs/hatena_flicker/md` の bbs 以外）の unit 化、wiki 解析層

## ライセンス

- wiki テキスト（解析・記述ページ）: **CC0**
- code・config: **CC0**（第三者配布物は当該ライセンス維持）
- `raw/`（BBS 投稿文）: **著作権は各投稿者に帰属**（本リポジトリは CC0 ではない）。
  出典（サイト・板・コミュ・取得日）を明記して公開している。
  根拠: コミュ「架空の神話を作ろう」規約は「元の設定を考えた人の許可を得る必要は全くありません」「誰でも引用可能な神話」「活動を当コミュ内に限る必要はありません」と記述の再利用・分散を明示的に許容している。

## 出典

- mixi コミュ「架空の神話を作ろう」 https://mixi.jp/view_community.pl?id=373088 （2005-10-22 開設）
- したらばBBS 映画板 7039「ゆらぎの神話BBS」 https://jbbs.shitaraba.net/movie/7039/
- ポータル（はてなふりかー） http://flicker.g.hatena.ne.jp/

取得日: 2026-10-12
