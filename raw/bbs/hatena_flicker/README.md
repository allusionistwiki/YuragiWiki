# Wayback バックログ: flicker.g.hatena.ne.jp（ゆらぎの神話ポータル）

はてなグループ「ゆらぎの神話」ポータル（[http://flicker.g.hatena.ne.jp/](http://flicker.g.hatena.ne.jp/)）は **2020-01-31 のはてなグループ終了で閲覧不能**。Internet Archive（Wayback Machine）の CDX 台帳から取得できる範囲でスナップショットを保存する。

## 構成（2026-10-14 指示）

```
raw/bbs/hatena_flicker/
├── MANIFEST.json      # 取得台帳（url / wayback timestamp / ファイル名 / bytes / 成否）※git 管理
├── README.md          # 本ファイル ※git 管理
└── 以下すべて当面 gitignore（取得物本体・未コミット）
    ├── HTML/          # <URL_sanitized>_<yyyymmddHHMMSS>.html（Wayback `id_` 版＝加工前 HTML）
    ├── md/            # HTML の markdown 変換（html2text、script/style 除去）
    └── Pic/           # HTML 内の Wayback `im_` 画像リンクを抽出して取得（<ts>_<name>）
```

- 取得元: `https://web.archive.org/web/{ts}id_/{url}`（HTML）/ `{ts}im_/`（画像）
- 対象:
  1. `flicker.g.hatena.ne.jp` ドメイン全体（CDX `collapse=urlkey`・status 200・1,406 URL）
  2. ルートページの経年スナップショット（`collapse=6mo`）
  3. 追加: `flicker.photo.hatena.ne.jp`（はてなフォトグループ）/ `mixi.jp/view_community.pl?id=373088`（mixi コミュニティページ）/ `keyword.hatena.ne.jp/operated::ゆらぎの神話`（解説ページ）/ `b.hatena.ne.jp` の flicker 関連ブックマークページ（コミュニティ反応コメント）
- ファイル名: URL の非英数文字を `_` 置換（ASCII・150 字上限）＋ Wayback timestamp
- 再取得は CDX 再クエリ → 新 timestamp のみ追記する差分運用を想定

## 関連

- はてなグループ終了告知: https://hatena-announce.hatenastaff.com/entry/2019-12-09/000000
- エクスポートデータは 2020-02-28 にメール送付済み（告知追記）。保有していれば HTML より一次資料になるため入手時に合流させる。
