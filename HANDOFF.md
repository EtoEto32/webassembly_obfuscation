# 研究引き継ぎ（2026-10-27）

**CSEC研究の引き継ぎ:** [別PCでの再開手順](docs/csec-another-pc.md) に、対象ブランチ・成果物復元・性能評価と正規化検討の資料をまとめた。以下の修士研究の探索記録とは区別して読む。

現在の目的は **WebAssemblyセキュリティにおける修士研究の新規性と検証可能な効用の確立**。特許を主目的とする段階は終了した。難読化から、GC入力生成・境界観測・実行系検査へ対象を広げている。主テーマとして十分な新規性はまだ未確立。実装数や検査件数を新規性の根拠にしない。

## 読む順序

1. [最新研究状態](research/STATUS.md)
2. [外部GC観測の実装・実測](research/heap-observer/README.md)、[既存技術との差と採用ゲート](research/heap-observer/prior-art.md)
3. [型付きcallerの単純対照](research/boundary-alias/caller-results.md)
4. 過去の候補：[R](research/gc-witness/README.md)、[S](research/gc-realization/README.md)、[K](research/state-witness/status.md)、[J](research/logical-reset/strict-review.md)

## 引き継ぎ直前に得た追加結果

`research/heap-observer/two.py` と [比較計画](research/heap-observer/two-plan.md) を追加。Binaryen133の `--fuzz-import` と2module実行の実経路を使い、抽象型/具体型の各条件で10系列×64 context×3実行方式×2変種、合計7,680 processを実行した。

- `results/heap-observer/two-abstract-v1` と `two-concrete-v1` にraw stdout/stderr、正規化出力、binary、seed、JSON集計を保存。
- 既存検査の3方式（Binaryen interpreter、upstream Node shell、typed/multi修正版）は、用意したGC内部8系列の差をこの条件で検出しなかった。通常のi32戻り値差は全試行で検出した。NaN正対照は差なし。
- これは人工系列での結果。Two handler全体、merge、全pass campaignを再現したわけではない。到達性の原因分析・時間予算比較・独立監査は未完了。結果を新しい不具合発見や主テーマ完成として扱わない。
- 公開の修正履歴34件の検索結果と、そこから選んだ8 PRのpatchを `history-search-v1` / `history-patches-v1` に保存。一次資料を取得したことと、不具合を再現したことを分ける。
- PR7857の入れ子struct/ref.eqを切り出してreturnを付けた派生試験をBinaryen123/133で比較したが、**この試行では誤最適化を再現しなかった**。`history-probe-v1` に3形態×3compiler条件×2engineの18行（表示と観測の計36 process）。旧版は公式SHA256照合済み。元の回帰testそのものではなく、観測用の改変を加えたものなので、その改変によってtriggerが消えた可能性も残る。

これらの追加結果は、直前の `checkpoint-v1` の検証対象外。引き継ぎ時の保存対象には含める。

## 再開時の優先事項

1. Two比較の出力・集計・metadata・target無変更を監査する。全0件をそのまま能力の限界と断定せず、importの存在、実際の呼出し、field読出し到達を調べる。
2. 強い単純対照である「型を知った手書きgetter」との差を保つ。現試作はそれより速くない。自動生成の適用範囲と、既存ランダムcontextに追加できる検出を評価する。
3. 既知の実不具合を原文test・適切な直前版で再現する。再現しない例を検出成功に数えない。修正履歴の型不正・compiler crash・数値差・prototype差を分ける。
4. 差が弱ければ、外部GC読出しを新アルゴリズムとは呼ばず、Wasmテストの観測不足を体系的に検証する修士テーマとしての成立可能性を検討する。

## clone後の成果物復元

コード・Markdown・通常のログ/JSONはGitで直接管理する。従来 `.gitignore` の対象だった実験 `.wasm` / `.wat`、大容量の生成表、取得元metadata、paper履歴等は、`handoff/snapshot-20261027/` の40 MiB以下の分割archiveとSHA256 manifestに保存する。

```powershell
python scripts/restore_handoff.py --verify-only
python scripts/restore_handoff.py
```

既存の異なるfileを上書きしない。同一内容の既存fileは検証して再利用する。復元後のファイルが再びignoreされるのは既存設定による。研究ごとの手順は各READMEを参照。CLIには固定Windows pathを使う古いscriptもあり、別環境で全研究が無修正で動くことは未保証。

## 環境・大容量元データ

検証環境はWindows x64、Python3.9、Node24.15.0、SpiderMonkey150.0.1、Binaryen133、Wasmtime Python50.0.1、Rust1.97 nightly。`.tools/` / `.venv/` / `.tf/` 等のインストール済み環境、認証用local JSON、Git内部情報は転送パッケージに含めない。Cargo.lock、取得script、元URL・hashは保存する。

取得済み元データは約226 GBあり、通常Gitの対象にしない。再取得に必要な `data/catalog/` と `data/upstream/` のmetadata/sourceは補助archiveに含める。[従来データの再現手順](docs/reproduction.md)、`experiments/dataset-registry.json`、`scripts/acquire.py`、`scripts/acquire_corpora.py` を参照。元の全226 GBを保存したバックアップとは異なる。別ストレージへの完全コピーは保存先が必要。

取得元の履歴にも認証情報の形が残っていたため、第三者資料の `cert_key.pem` と `data/catalog/wasmizer/resolved-commit.json` は転送から除外した。後者は過去のtoken削除diffを含むmetadataである。ローカル原本は変更していない。除外pathはpackage.jsonにも明記する。

## 作業上の制約

会話・研究ノートは日本語。文献検索は英語も使用。正当なローカル防御研究として進める。新規性・意味保存・効果の仮説と実測を区別する。過去の否定的結果や失敗ログも保存する。今回のユーザー依頼で既存Gitリモートへの引き継ぎが許可されたが、課金や無関係な外部送信を許可したものではない。研究自体は完了していない。
