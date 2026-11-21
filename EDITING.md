# YuragiWiki 編集方針（EDITING.md）

この Wiki の今後の編集・拡張の規約。運用の現場は work repo `AllusionistWiki_work/work/yuragi/`（解析 run 群）と
本 repo（raw コーパス + content/ 公開面 + Quartz エンジン）。**編集者（人間・エージェント）はこの文書と
work repo の `CONTACT.md` に従う。**

## 1. 位置づけと恒久原則

- ファン解析 Wiki（二次著作）。**原文至上**: 一切の記述は引用（逐語）と ref（`篇:投稿番号`）で原文に接続する。
  引用なき主張を作らない。LLM 生成物も全量監査（100% 収束）を通らなければ公開しない。
- **追加専用**: 解析産出物は run ディレクトリに追記のみ。旧 run を書き換えない。訂正・再実行は必ず
  新 run（`run.json.derived_from` で来歴を辿る）。退役 run は `archive/` へ物理移動。
- **来歴を切らない**: 全公開記事の frontmatter に生成 run ID（`run:`）と監査 run ID（`link_audit:`）。
  来歴チェーン = 公開記事 → L1 run → L0 台帳（sha1 検証済み生データ）。
- 原文（`raw/`）の著作権は各投稿者に帰属。wiki テキスト・code は CC0。削除要請には速やかに対応する。

## 2. トポロジー（Yuragi 型・1 repo）

- 本 repo = コーパス（raw/）＋公開面（content/・git 追跡）＋エンジン（quartz/・quartz.*.ts）。
  アリュージョニスト系の「authored ページは vault のみ・content/ 非追跡」とは異なる
  （Yuragi は 1 repo 構成で content/ を追跡する。this 構成が正）。
- 層配置則（恒久・全層同一構図）: 節は `content/<節>/` 直下にページ、各節に `index.md` フォルダノート、
  中間ディレクトリの入れ子を作らない。索引ページは `<name>/index.md` ディレクトリ形（GitHub Pages で
  単一 md の clean URL は 404 になるため受け皿必須）。
- 相互参照はサイト URL（`https://allusionistwiki.github.io/YuragiWiki/...`）か wikilink（層内は相対）。
  Pages のディレクトリ URL 検証は trailing slash なしで照会する。

## 3. 公開ゲート（すべて通過しないと公開しない）

1. **生成 run**（Strata ローカル LLM）→ **LLM 全量品質監査 run**（scope 別・機械ゲート付き）。
   flagged 全件を修復・再生成して再監査、**flagged 0（PASS）で収束**。未監査内容を content/ に置かない
   （gen run 内の後続改訂も、その改訂を対象にした audit PASS run が出るまで公開しない）。
2. **機械ゲート**（生成・publish 側に恒久実装）:
   - 引用逐語照合（「…」がコーパスの連続部分文字列）／ref 実在／規定見出し。
   - 中国語簡体字専用グリゲート（CN_CHAR。引用「」内と投稿者原文の逐語は保護）。機械置換禁止・LLM 整序。
   - frontmatter 全件 `yaml.safe_load` 成功（YAML 死は CI ビルドの死亡原因）。日付は quote。
   - 本文の `$` は `\$` エスケープ（Katex 誤認防止）。ビルドログ `unicodeTextInMathMode` 0。
   - リンク機械計測: 空 link `]()` 0・期待リンク数一致。slug に `& # %` を含めない（全角 ＆ 化）。
3. **publish（決定論同期）**: `scripts/publish_yuragi_site.py` のみ content/ に書く。本文の機械的変換は
   linkify・エスケープ・frontmatter 追記まで。**publish を通さず content/ を手で編集しない**
   （次の publish で消える。top/index・索引・フォルダノートも publish 側テンプレが作者）。
4. **CI 検証**: ビルドログの `failed to resolve` 0・Emitted 件数照合。**live 検証**: 新規 URL サンプル 200
   （deploy success だけでは確定しない。Pages 初期化・CDN 遅延あり）。

## 4. サイトエンジニアリング規約（Quartz）

- 恒久設定: `enableSPA: false`・`enablePopovers: false`（iOS 対策・「勝手に飛ぶ」知覚回避）。
- Explorer: `folderDefaultState: collapsed`・`folderClickBehavior: collapse`・40 超節フォルダは mapFn で
  子抑制＋和文 `displayName`（LABELS 表。mapFn は toString でクライアントへ渡されるため**外側変数を閉じない**）。
- ContentIndex: `excludePrefixes`（full/・works/・works_index/・widx_*）＋`excerptChars: 200`
  （大量ミラー節を索引側から除外。対症の layout filterFn は不可）。OG 画像 emitter は無効（ビルド時間）。
- **CSS 変数 `--accent` は custom.scss で両テーマ定義**（未定義だと color-mix 系スタイルが無音で失効する）。
- 日本語 webfont: `body: Noto Sans JP`・`header: Zen Kaku Gothic New`・`includeItalic: false` 必須
  （italic 非対応フォントへの ital 要求は Google Fonts css2 が 400 を返し stylesheet ごと失効）。
- デプロイは push:main 駆動。エンジン変更時は内容も同一コミットで流す（ビルドスキップ罠回避のため
  content と engine は同じ push 周期にまとめる）。

## 5. 記事の質感規約

- 散文は自然な日本語 wiki 文体（機械置換で整えない。LLM refine → 全量監査の順）。語彙は「篇」→文脈で
  「スレッド」。引用は 1 文字も変えない。
- 記事模板: 概要 / 流れ / 主要話題 / 注目投稿（逐語引用＋出典リンク）。実体ページはさらに
  関連する実体 / 言及篇 / 初出・最終言及 / 共起実体。
- 生成プロンプトの仕様変更は**小対象生成 → 全件実読 → 失敗分類 → 規則改修 → 収束 → 範囲拡大**の
  品質ループで行う（大きな一括実行を先に流さない）。監査はサンプリングでなく全量（小規模時）・
  拡大後は 400 件以上・閾値 99%。

## 6. 拡張ロードマップ（優先順）

1. **解析層（allusion/analogy）**: 散在する実世界参照（神話・宗教・文学・歴史・地理・科学）を
   専頁化。構成 = 元説明（出典付き事実）＋作品中での使われ方（解釈・確度ラベル: 確認/蓋然性高/推測）＋
   関連ページ wikilink。1 篇単位の小規模 pilot → 全件実読 → 規則改修 → 全コーパス。`type: reflection`、
   in-world 用語は実体層のままで解析層に置かない。
2. **実体台帳の正規化**: 表記ゆれ（中点・全半角・括弧注記）の機械統合、alias 裁定は候補提示まで可、
   実統合には全コーパス使用状況確認。推移閉包マージ禁止（辺単位）。
3. **関係の可視化（決定論）**: 共起・言及篇・編集中の引用連鎖から篇間・实体間の重み付き一覧を作る
   （グラフ描画は追加しない）。
4. **年代の深化**: 篇寿命グラフ（開始/終息・ burst 月）、主要語句の初出散布を年表に統合。
5. **投稿者活動線**: 上位投稿者の時系列活動（篇をまたぐ活動の流れ）を決定論集計で強化。
6. **用語選定（topics 手当て）**: 出現高频語から「世界の核」用語を選別し、実体層/解析層へ昇格。

## 7. 操作手順（runbook）

```
# 1) 生成・監査（work repo・Strata は 1 ジョブずつ直列・background+notify）
python scripts/build_yuragi_*.py ...      # 新 run 生成
python scripts/audit_yuragi_l1.py --scope <s> --run-dir <新 audit run>   # PASS まで収束ループ

# 2) 公開同期（決定論）
python scripts/publish_yuragi_site.py

# 3) 両 repo を同一サイクルでコミット・push（work: `L1: run <id> (scope)` / site: `publish: <内容>`）
git -C AllusionistWiki_work commit/push   # run 産出・script 変更
git -C YuragiWiki commit/push             # content/・エンジン（CI 自動ビルド）

# 4) 検証（CI run 捕捉は freshness フィルタ・conclusion success 確認・live サンプル 200）
```

- 長時間 job は background+notify で起動しターンを終わる。固定 sleep 手待ち・ポーリング禁止。
- 通知待ちで止まらず、決定論レーン（索引・CSS・スクリプト整備）を並行して進める。

## 8. やってはいけないこと

- 旧 run の書き換え・`rm -rf` 退役（物理移動）。未監査 content の公開。content/ の手編集。
- 引用の機械的編集・散文の機械置換（CN 文字削除等）。
- 大量 DOM 展開（iOS）、popovers・SPA の再有効化、meta refresh スタブ、hover で自動転送するリンク。
- 層骨格の逸脱（入れ子ディレクトリ・単一 md の直 URL 公開）。

## 9. 連絡・帰属

- 運用連絡: work repo `CONTACT.md`（権威）。wiki 寄署名: シナモリアキラ【】。
- 削除・帰属要求は repo 管理者へ。README・ライセンス節が公開側の約束。
