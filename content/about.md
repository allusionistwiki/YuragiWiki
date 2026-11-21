---
title: "この Wiki について"
description: "出典・解析パイプライン・ライセンス帰属・編集方針"
run: publish
---

# この Wiki について

## 何の Wiki か

『ゆらぎの神話』— 2005 年頃から複数 BBS で行われた「多人数で神話を創る試み」の実況・議論の記録を、
機械台帳と LLM 解析（全量品質監査付き）で整理したファン解析 Wiki です。
掲載記事は二次著作（紹介・解析）で、引用を通じて原文（一次資料）へ直接接続します。

## 出典（取得 2026-10-12）

- [したらば映画板 7039「ゆらぎの神話BBS」](https://jbbs.shitaraba.net/movie/7039/) — 179 篇
- [mixi コミュ「架空の神話を作ろう」](https://mixi.jp/view_community.pl?id=373088)（2005-10-22 開設）— 5 篇
- [はてなふりかー（portal）](http://flicker.g.hatena.ne.jp/) — 1 篇
- 関連 Hatena Flicker 日記 19 作者（387 投稿）

mixi コミュ規約は記述の再利用・分散を明示的に許容しています（「元の設定を考えた人の許可を得る必要は全く
ありません」「誰でも引用可能な神話」）。原文データの出典・取得日は repo README に記録しています。

## 解析パイプライン

1. **L0 台帳**: 生 BBS データを SHA1 検証付きで取り込み、投稿単位チャンク（②）と
   structured.jsonl（③）へ正規化（48,891 投稿・sha1 ラウンドトリップ検証）。
2. **検索索引**: 語句・日付・篇の転引索引（L0 検索台帳）。
3. **LLM 生成**: ローカル LLM で篇記事・実体・投稿者・創作・日記記事を生成。
4. **全量品質監査**: 全記事を LLM 監査（引用の逐語性・ref 実在・日本語品質）し、
   flagged 件を修復して 100% 収束。
5. **公開同期**: 監査済み run から決定論 publish（本文の機械的変換なし）で本サイトへ反映。

- 作業データ: [AllusionistWiki_work](https://github.com/allusionistwiki/AllusionistWiki_work) の `work/yuragi/`
  （run 単位・追加専用・来歴連鎖）。
- 原文データ: [YuragiWiki repo](https://github.com/allusionistwiki/YuragiWiki) の `raw/bbs/`。
- 全記事の frontmatter に生成 run ID・監査 run ID を記録（来歴）。

## ライセンス帰属

- wiki テキスト（解析・記述ページ）: CC0
- `raw/`（BBS 投稿文）・原文全文版の引用: **著作権は各投稿者に帰属**。
  出典を明記して公開し、削除要請に対応します（[[license|ライセンス]]）。

## 編集方針

今後の編集・拡張の規約は repo ルートの
[EDITING.md](https://github.com/allusionistwiki/YuragiWiki/blob/main/EDITING.md)（追加専用 run・
全量監査収束の原則・公開ゲート・拡張路線）。
