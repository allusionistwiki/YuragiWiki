# Wayback バックログ: flicker.g.hatena.ne.jp（ゆらぎの神話ポータル）

はてなグループ「ゆらぎの神話」ポータル（[http://flicker.g.hatena.ne.jp/](http://flicker.g.hatena.ne.jp/)）は **2020-01-31 のはてなグループ終了で閲覧不能**。Internet Archive（Wayback Machine）の CDX 台帳から取得できる範囲で HTML スナップショットを保存する。

## 構成（2026-10-14 指示）

```
raw/bbs/hatena_flicker/
├── MANIFEST.json      # 取得台帳（url / wayback timestamp / ファイル名 / bytes / 成否）※git 管理
└── HTML/              # ★当面 gitignore（取得物本体は未コミット）
    └── <URL_sanitized>_<yyyymmdd>.html
```

- 取得元: `http://web.archive.org/web/{ts}id_/{url}`（`id_` = Wayback 加工前の原文 HTML）
- 対象: CDX `matchType=domain`・`collapse=urlkey`・status 200 の全 URL（1,406 件）＋ ルートページの経年スナップショット（`collapse=6mo`）
- ファイル名: URL の非英数文字を `_` に置換（ASCII・150 字上限）＋ `_` + Wayback timestamp（yyyymmddHHMMSS）
- 当面 HTML は gitignore（`raw/bbs/hatena_flicker/HTML/`）。コミット方針が決まり次第、台帳とスナップショットの公開範囲を決定する。

## 取得スクリプト

使い捨て（`_temp/` 相当・scratch の `wayback_flicker.py`）。再取得は CDX 再クエリ → 差分（新 timestamp）のみ追記する運用を想定。

## 関連

- はてなグループ終了告知: https://hatena-announce.hatenastaff.com/entry/2019-12-09/000000
- エクスポートデータは 2020-02-28 にメール送付済み（告知追記）。エクスポートデータを保有している場合は HTML より一次資料になるため、入手時に合流させる。
