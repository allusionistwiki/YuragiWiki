# YuragiWiki

『ゆらぎの神話』— 多人数で神話を創る試みの解析 wiki ＋ 記述（原文）アーカイブ。

## 内容

- `raw/bbs/jbbs/movie-7039/` — 外部BBS「ゆらぎの神話BBS」（したらば movie/7039）全スレ・全レス
- `raw/bbs/mixi/373088/` — mixi コミュ「架空の神話を作ろう」全トピック・全コメント
- `raw/bbs/**/posts/` — **② 投稿チャンク層（記事参照用）**: 各 BBS の各投稿を 1 ファイルに切り分けた層。
  同一投稿者の隣接連投は 1 ファイルに統合（`p0123-0127.md` 形式・単独は `p0001.md`）。
  各篇の `posts/_manifest.json` に元ファイル SHA1・領域・disk round-trip 検証記録。
  生成: `tools/split_posts.py`（元ファイルは無改変）。はてな portal BBS（bbs/1）は 1 ページ 1 投稿のため対象外。
- **③ `structured.jsonl`（各篇・LLM 用）**: 1 行目 = 篇メタ（unit_id・source・thread_title・url・n_posts）。投稿行は `ref`（`unit:post_no`）・post_no・作者・日時（raw/ISO）・② ファイル名・**全文省略なし body** のみ（スレッド情報の行内重複なし）。
- **④ `chains.jsonl`（各篇）**: 同一作者かつ同一話題で ③ を一まとめ。`chain_id` 先頭が unit_id（重複フィールドなし）。話題規則（決定論）: 隣接＋同一作者＋【…】語彙が群語彙の部分集合なら merge、新規【…】で新群、削除投稿は連鎖を断つ。`summary` 欄に LLM 1 文要約（Strata・work 側 L0 run で生成）＋`summary_sha1`（chain 本文ハッシュ来歴）。全群 LLM 品質監査 100% 合格（2026-11-17）。反映は `tools/merge_chain_summaries.py`（chain_sha1 照合ゲート）。
- LLM への読み取りは work repo `scripts/read_yuragi.py`（unit/chain 単位のペイロード生成・篇ヘッダ 1 回付与）。
- **⑤ `thread.json`（各篇）**: 一連の話題（スレッド全体）で ③ を一まとめ（全文投稿順連結）。
- 各篇 `_layers_manifest.json`（③④⑤ SHA1・検証記録）。生成: `tools/build_raw_layers.py`（①〜⑤ の対応は README・tools 冒頭）。
- 台帳（unit ID 台帳・アンカー・索引）は work repo `AllusionistWiki_work/work/yuragi/` 側。
- unit ID: `YJ-T###`（したらば篇）/ `YJ-M<トピックID>`（mixi）/ `YJ-H01`（portal BBS）。
- **公開 Wiki: https://allusionistwiki.github.io/YuragiWiki/** — L1 版（篇記事 `/units/`: 要約＋100 字以内引用＋ref アンカー）＋制約なし自由記述版（`/free/`）＋原文全文版（`/full/`: 投稿単位 permalink 付き）＋topics（話題横断 430）/authors（投稿者 96）/entities（実体 800・相互リンク・言及篇・共起実体付き）/works（創作記述 6,453・掲載文脈付き）/flicker（Hatena Flicker 日記 19 作者 387 投稿・原文逐語・投稿 permalink 付き・装飾行機械除去・LLM 解析記事付き）/chronology（年表・月別集計・主要語句初出）/索引（widx_*・entities_index・free_index・flicker_index）＋サイト案内（`/guide/` 読み方ガイド・`/stats/` 統計ダッシュボード・`/about/` 本 Wiki について）。`content/` は work repo `scripts/publish_yuragi_site.py` で監査済み run から同期（全記事 LLM 全量品質監査 100%・ref は本 repo raw ファイルへリンク）。記事散文の中国語簡体字混入は LLM 整序＋引用逐語保護の字体変体正規化で駆逐済み（投稿者本人の原文 CN は逐語引用で保持）。CI=Quartz→Pages。
- **編集方針: [EDITING.md](EDITING.md)** — 追加専用 run・全量監査収束の公開ゲート・サイトエンジニアリング規約・拡張ロードマップ。編集者（人間・エージェント）はこれに従う。
- **日記 unit ID**: `YJ-F<作者名>`（hatena_flicker・`raw/bbs/hatena_flicker/units.jsonl`＋`units/<uid>/posts/` 逐語チャンク・sha1 検証。生成: `tools/build_flicker_units3.py`＝全クロールページパース・作者/日付は投稿 URL から導出・クロール日以後日付のテスト投稿除外・ブックマーク装飾行除去）。

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
