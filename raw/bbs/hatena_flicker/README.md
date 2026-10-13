# Wayback バックログ: flicker.g.hatena.ne.jp（ゆらぎの神話ポータル）

はてなグループ「ゆらぎの神話」ポータル（[http://flicker.g.hatena.ne.jp/](http://flicker.g.hatena.ne.jp/)）は **2020-01-31 のはてなグループ終了で閲覧不能**。Internet Archive（Wayback Machine）の CDX 台帳から取得できる範囲でスナップショットを保存する。

## 構成（2026-10-14 指示）

```
raw/bbs/hatena_flicker/
├── MANIFEST.json      # 取得台帳（url / wayback timestamp / ファイル名 / bytes / 成否）※git 管理
├── README.md          # 本ファイル ※git 管理
├── HTML/  md/  Pic/   # 本体: flicker.g.hatena.ne.jp ドメイン全体
└── mention/           # ★flicker 引用・関連系（2026-10-14 指示で分離）
    ├── HTML/          #   はてブ(b.hatena) flicker 引用ページ / mixi コミュニティページ /
    ├── md/            #   keyword.hatena 解説ページ / flicker.photo グループ
    └── Pic/           #   ※md/・Pic/ は HTML と同じ変換・抽出手順
```
（上記 5 フォルダは当面 gitignore・取得物本体は未コミット）

- 取得元: `https://web.archive.org/web/{ts}id_/{url}`（HTML）/ `{ts}im_/`（画像）
- 対象:
  1. `flicker.g.hatena.ne.jp` ドメイン全体（CDX `collapse=urlkey`・status 200・1,406 URL）
  2. ルートページの経年スナップショット（`collapse=6mo`）
  3. mention（引用・関連系・別フォルダ）: `b.hatena.ne.jp` の flicker 引用ブックマークページ / `mixi.jp/view_community.pl?id=373088` / `keyword.hatena.ne.jp/operated::ゆらぎの神話` / `flicker.photo.hatena.ne.jp`
- ファイル名: URL の非英数文字を `_` 置換（ASCII・150 字上限）＋ Wayback timestamp
- 再取得は CDX 再クエリ → 新 timestamp のみ追記する差分運用を想定

## 関連

- はてなグループ終了告知: https://hatena-announce.hatenastaff.com/entry/2019-12-09/000000
- エクスポートデータは 2020-02-28 にメール送付済み（告知追記）。保有していれば HTML より一次資料になるため入手時に合流させる。
