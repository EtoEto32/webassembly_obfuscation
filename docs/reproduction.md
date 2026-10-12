# 再現手順と測定上の注意

2026-10-06時点で版を固定したデータの再現手順である。PowerShellでリポジトリルートから実行する。取得処理だけがネットワークを使用し、未知のWasmと取得スクリプトは実行しない。

## 環境

- Python環境：`.venv/Scripts/python.exe`。取得・解析・集計の中心部は標準ライブラリのみ。
- WABT 1.0.42：`.tools/wabt-1.0.42/bin/`。`scripts/bootstrap.py`とツール取得記録を参照。
- .7z配布物の展開にはローカル7-Zipを利用。`scripts/ingest_archives.py`の`SEVEN`を必要に応じて変更。
- 図表生成はmatplotlib 3.10.7 / NumPy 2.5.3を使用。図表の依存バージョンと入力CSVハッシュは`results/corpus/figures/generation.json`。
- JSの静的リテラル抽出はNode.jsとAcorn 8.15.0を使用。`npm install --prefix .tools/js-parser --ignore-scripts --no-audit --no-fund acorn@8.15.0`で固定導入する。取得JSは実行しない。

## 配布物の一覧と取得

```powershell
.\.venv\Scripts\python.exe scripts/catalog_datasets.py
.\.venv\Scripts\python.exe scripts/discover_artifacts.py
.\.venv\Scripts\python.exe scripts/acquire_corpora.py swamped wasmmal wasmixer minerray wasim wasm-obf diversification2022 seismic deepminer
.\.venv\Scripts\python.exe scripts/download_artifacts.py wasmbench-filtered diversification2022-data diversification2022-test androwasm
& .\scripts\download_proof_mirror.ps1
.\.venv\Scripts\python.exe scripts/ingest_archives.py wasmbench-filtered diversification2022-data diversification2022-test androwasm proof-of-theft minesweeper-crawled-archive
```

`experiments/dataset-registry.json`と`experiments/archive-registry.json`が候補・取得先を定義する。GitHubのtreeは取得済みキャッシュを固定して使い、tar内の対象ファイルをGit blob SHA-1と照合してからSHA-256を計算する。全通常ファイルの先頭を確認し、拡張子のないWasmも調べる。初回取得の一部は拡張子限定だったため、最終監査では取得方式も確認する。

7-Zipの展開前に全ファイル名とリンクを検査し、作業ディレクトリ外への書き込みを拒否する。ZIP内のファイルは原則として展開せずバイト列として読み、CRCとSHA-256を記録する。

`ingest_archives.py`は入れ子ZIP/APK/JARを深さ5まで再帰的に走査する。tar圧縮にも対応する。JS埋め込みは`extract_js_wasm.cjs`がWobfuscatorの全通常JSファイルを構文解析し、数値配列・base64リテラルを抽出する。動的な復号・連結やネイティブバイナリ埋め込みは未対応で、失敗・未対応範囲を報告する。

追加の配布物には、`scripts/register_archive_assets.py`で登録し、版を固定したファイルを使う。取得後、Cryptic Bytesの分割ZIPは連結コピーを作らず、以下でアーカイブ内のすべてのファイルを順に調べる。

```powershell
.\.venv\Scripts\python.exe scripts/ingest_split_zip.py binaries
.\.venv\Scripts\python.exe scripts/ingest_split_zip.py binaries-opt
.\.venv\Scripts\python.exe scripts/download_industry_dataset.py
.\.venv\Scripts\python.exe scripts/ingest_archives.py industry2025-validwasm
node scripts/test_extract_js_wasm.cjs
node scripts/extract_js_wasm.cjs
```

Industryの匿名取得スクリプトは、既存ファイルがある場合にサイズとSHA-256を再検証し、同じものを再ダウンロードしない。Wobfuscatorの処理は6アーカイブの展開・目録作成後に実行する。

取得マニフェストは`data/catalog/*/acquisition.jsonl`、取得概要は同階層の`acquisition-summary.json`。全体アーカイブのSHA-256/提供MD5は`data/archives/*.receipt.json`。OSの読み取り拒否は記録し、保護機能の無効化や回避をしない。

## 解析と集計

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s scripts -p 'test_*.py' -v
.\.venv\Scripts\python.exe scripts/analyze_corpus.py --workers 4
.\.venv\Scripts\python.exe scripts/audit_control_pairs.py
.\.venv\Scripts\python.exe scripts/summarize_corpus.py
.\.venv\Scripts\python.exe scripts/plot_corpus.py
.\.venv\Scripts\python.exe scripts/plot_control_audit.py
```

`--limit`はデバッグ専用。使った結果を全数解析の完了として扱わない。
解析は取得時のSHA-256で重複を除き、`data/analysis-v2/<sha256>.json`に各ファイルの結果を保存する。関数本体ハッシュ・命令系列・命令ヒストグラム・構造指標もここに残る。

解析v2.1は、元ファイルがWABTで失敗してカスタムセクションを持つ場合に、カスタムセクションを除いたバイト列を別途検証する。元の`valid_wabt=false`とエラーを保持し、復旧しても元ファイルの検証成功には書き換えない。復旧後の逆アセンブルのオフセットは元ファイルと異なる。v2.0の成功キャッシュは測定方法が同一のため再利用し、v2.0の失敗だけ再試行する。

## 指標の意味

- `core_bytes_sha256`：カスタムセクションを除いたファイルの完全一致。すべての入力で同じ動作をすることの証明ではない。
- `code_payload_sha256`：コードセクションのバイト一致。imports、globals、data等が異なると動作も変わる可能性がある。
- `body_sha256`：ローカル宣言を含む関数本体のバイト一致。型、外部への参照、関数が使われる状況まで同じであるとは保証しない。
- 命令系列ハッシュはオペランドを含まない。同じ動作をすること、生成元のファイルが同じであること、同じマルウェアファミリーに属することを示す値とは解釈しない。
- エントロピーはコードセクション／データセクションの内容全体を別々に測る。データセクションにはセグメント数・初期化式等の管理情報も含まれ、純粋なデータバイトだけの値ではない。
- `br_table_in_loop_count`は構文上ループの内側にある分岐表の件数。状態変数や遷移を検証した平坦化の件数ではない。
- 命令数には構造命令と関数終端の`end`を含める。ローカル変数宣言を命令に数えない。
- `pending`は未解析、`validation_failed`は使用したWABTによる失敗。Wasm全仕様で不正だという断定ではない。
- マルウェアの根拠、出典・生成履歴、難読化の根拠は別々に記録する。公開コード、採掘機能、名前情報の欠如を悪性の根拠にしない。

## 出力

`results/corpus/`の主要ファイルを以下に示す。

- `occurrence-manifest.csv`：配布フォルダ内の各ファイルの出典と属性。SHA計算不能な展開失敗も、`acquisition_failed_without_sha256` として残す。
- `module-features.csv`：SHA-256単位の解析状態・指標。
- `cohort-summary.csv`：明示したグループごとの分母、解析成功、失敗、保留件数と特徴分布。
- `dataset-overlap.csv`：ダウンロードバイトからSHA-256を計算できた範囲の完全一致。
- `wasmmal-split-identities.csv`：train/test間のバイト／セクション一致。検出性能への影響を測った結果ではない。
- `summary.json`：2026-10-06に固定した公開範囲の最終集計。

同じ研究のリポジトリ例と対照サブセット（wasm-obf/wasm-obf-controls）は独立した研究データセット2個とは数えない。全リリース取得後の集計では、同じリリースから初期に抜き出した24対照コピーを配布ファイルとして重複して数えない。過去の個別レビュー入力は保存する。

## 個別レビューの再検査

選定対象は`experiments/review-selection-stage1.json`と`review-selection-stage2.json`に固定している。既存の選定ファイルを削除して都合よく再抽出しない。

第3段階の追跡調査は`review-selection-stage3.json`。参照カウンタ関数と一致する良性ラベル3種類すべて、および悪性ラベルから乱数シードを固定して1種類を選ぶ。全体の無作為標本ではない。

```powershell
.\.venv\Scripts\python.exe scripts/prepare_case_reviews.py packets
.\.venv\Scripts\python.exe scripts/prepare_control_reviews.py packets
.\.venv\Scripts\python.exe scripts/compare_review_pairs.py
.\.venv\Scripts\python.exe scripts/compare_control_reviews.py
.\.venv\Scripts\python.exe scripts/audit_case_reviews.py
```

`review-decisions-stage*.json`は逆アセンブルを読んで記述した判断であり、解析用資料の生成や参照先の検査だけで、判定が自動的に決まるわけではない。`audit_case_reviews.py`は関数・オフセットの存在を検査し、人間の独立レビューの代わりにはならない。カスタムセクションを除いた本体を使った事例はオフセットの対象を明記する。

## 追加公開資料と出典・生成履歴監査

公開版を固定したWasmizer Figshare v2を一般用途の比較グループに追加した。以下は既に登録された配布版を取得して監査するコマンドであり、著者のビルドスクリプトや対象のWasmファイルを実行しない。

```powershell
.\.venv\Scripts\python.exe scripts/audit_remaining_sources.py
.\.venv\Scripts\python.exe scripts/audit_literature_sources.py
.\.venv\Scripts\python.exe scripts/download_artifacts.py wasmizer-msr2023
.\.venv\Scripts\python.exe scripts/ingest_archives.py wasmizer-msr2023
.\.venv\Scripts\python.exe scripts/audit_release_parents.py
.\.venv\Scripts\python.exe scripts/audit_wasmizer_metadata.py
.\.venv\Scripts\python.exe scripts/verify_wasmizer_overlap.py
.\.venv\Scripts\python.exe scripts/audit_observation_dates.py
.\.venv\Scripts\python.exe scripts/inventory_acquisition.py
.\.venv\Scripts\python.exe scripts/plot_provenance_audit.py
.\.venv\Scripts\python.exe scripts/audit_minesweeper_crawled.py
.\.venv\Scripts\python.exe scripts/plot_minesweeper_crawled.py
.\.venv\Scripts\python.exe scripts/analyze_cryptic_features.py
```

PDF本文のテキスト抽出には `pypdf` が必要。この作業環境では同梱Pythonランタイムの `pypdf` を使用した。依存がない場合もPDF取得の成否とテキスト抽出の成否を分けて記録する。本文を取得できなかった場合や、テキストを抽出していない場合に、論文やデータが存在しないとは判断しない。

`audit_release_parents.py` は配布パスと固定ソースツリーから元プログラム22本と配布ファイルを対応付ける。変換名は、著者が記載したものとして記録する。名前だけで、変換が実際に加えられたとは判断しない。`verify_wasmizer_overlap.py` はWasmBench配布物の展開コピーとWasmizer ZIPのコピーを独立に読み、112件の一致を再検証する。

Wasmizer追加時には、既存の実行中解析との衝突を避けるため、他のデータセットの全取得ハッシュと共通しない8,788件だけを `experiments/wasmizer-exclusive-sha256.json` に固定して別プロセスに渡した。選定根拠は `results/provenance/wasmizer-analysis-selection.json`。これは全体集計から127件を除外する操作ではない。

```powershell
.\.venv\Scripts\python.exe scripts/analyze_corpus.py --datasets wasmizer --sha256-file experiments/wasmizer-exclusive-sha256.json --run-name wasmizer-exclusive-v21 --workers 1
```

実行名を付けた解析は `results/corpus/runs/` に入力マニフェストとそのSHAを残し、通常の `analysis-run.json` を上書きしない。最終全体実行の受領票は `all-current-process-v21.json`、MineSweeper全配布物の受領票は `minesweeper-full-v21.json` である。全対象を改めて列挙し、保存済み結果を再利用する解析後に `summarize_corpus.py` と全体図を生成する。最終値は18データセット、配布ファイル109,846件、異なるSHAが70,564種類、解析成功67,729、失敗2,835、保留0である。

## WasmMalの感度分析とカウンタ構造

WasmMal全件と参照群の解析キャッシュ、および第1段階の参照ファイルの逆アセンブルを用意してから実行する。

```powershell
.venv\Scripts\python.exe scripts/analyze_malware_sensitivity.py
.venv\Scripts\python.exe scripts/audit_similarity_ties.py
.venv\Scripts\python.exe scripts/prepare_counter_reviews.py
.venv\Scripts\python.exe scripts/audit_counter_cohort.py
.venv\Scripts\python.exe scripts/audit_case_reviews.py
.venv\Scripts\python.exe scripts/plot_malware_sensitivity.py
.venv\Scripts\python.exe scripts/verify_sensitivity_outputs.py
```

類似度には、関数本体の長さを重みにし、同じ本体の個数も考慮したJaccard類似度を使う。閾値5通りに加え、同点の場合に辞書順の先頭・末尾へ割り当てる方法、個別に残す方法、20個の固定乱数シードを使う方法の結果を記録する。参照ファイルは自身のグループに残す。各グループで指標の平均を求め、それらを同じ重みで平均する。この値を元プログラム数や難読化率とは呼ばない。

カウンタは確認済みの参照関数と本体が完全一致した124種類について、WABTによる逆アセンブル結果からカウンタ処理を改めて数える。データ全体を検出する方法ではなく、選定したグループの確認である。命令数の比は実行時間の比ではない。getter/resetの厳密な構造条件に一致しないケースも命令列を保存する。図の入力CSVハッシュは`results/sensitivity/figures/generation.json`に残る。[結果と解釈](wasmmal-sensitivity-findings.md)

## 追加参照・失敗の偏り・解析の再開

```powershell
.venv\Scripts\python.exe scripts/audit_reference_additions.py
.venv\Scripts\python.exe scripts/analyze_malware_sensitivity.py --include-minesweeper
.venv\Scripts\python.exe scripts/audit_similarity_ties.py --include-minesweeper
.venv\Scripts\python.exe scripts/compare_reference_expansion.py
.venv\Scripts\python.exe scripts/plot_reference_expansion.py
.venv\Scripts\python.exe scripts/audit_wasmizer_failures.py
```

参照ファイルを追加した集計結果は`results/sensitivity-minesweeper/`へ別保存する。追加前の有効な参照56件と、追加後の60件を混ぜずに比較する。外部MineSweeper TARのプレビューは全件取得マニフェストに含めない。

`analyze_corpus.py`は`--executor processes`でPythonの命令解析を複数プロセスへ分けられる。解析アルゴリズム・キャッシュ版は変わらない。Wasm-R3をサイズ順に並べた5つの位置から選んだファイルについて、スレッド・プロセス両方式と保存済み結果の全測定値が一致した。除いたのは解析日時と所要時間のみ。`results/corpus/executor-equivalence.json`に対象SHAと比較結果を保存した。測定時の所要時間を一般的な速度向上のベンチマークとは扱わない。

全体の旧スレッド実行は、プロセス識別を確認して意図的に終了し、終了コードを取得した。結果キャッシュを保持して、新しい名前付き全体実行へ引き継いだ。中断記録は`results/corpus/runs/expanded-thread-interruption.json`。再開時は[チェックポイント](resume-checkpoint.md)と`results/active-runs.json`を読み、記載されたセッションの処理が実際に動いているかを確認する。出力が遅いだけで二重起動しない。

