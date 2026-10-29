# 対策実験の実施状況と根拠ファイル

2026-10-10。変更後の作業目標に対する実施結果と適用限界をまとめた。教員の許可を確認後、SHAが異なる23種類のバイナリを各6回、計138ブロック測定し、正常に終了した。全記録の監査、公表された5入力の照合、追加した12入力の新規コンテキストと同じ順序で再利用したコンテキストでの照合、全速度ブロックの計測前後・最終出力の照合にも合格した。過去のハッシュ測定は、新しい対策実験の結果として扱わない。

手法の説明は[対策手法の原理と仕組み](C:/Users/ettotto/Documents/webassembly_obfuscation/docs/countermeasure-method-principles.md)に、最終結果と判断は[実験報告](C:/Users/ettotto/Documents/webassembly_obfuscation/docs/countermeasure-experiment-report.md)にまとめた。速度と構造の比較表・図も追加済みである。論文更新は現在の作業範囲に含めない。

## 要求と確認範囲

| 要求 | 現在の根拠・状態 |
|---|---|
| 現行RQ1・RQ2を維持し、対策を発展として扱う | main.texのRQと6.1節。主題は変換の仕組み・実行経路・出力・速度の対応で、対策だけに置き換えていない |
| 既存の正規化・式簡約との関係 | Binaryen 133の局所pass・O2を実行して比較した。MBA-Blastの一次資料と公開実装は確認したが、MBA-Blast自体との実行比較は未実施 |
| NOP・整数定数式の局所規則 | normalize_wat_local.pyに実装した。基準版・SHA・関数番号・変換ログを使って復元する規則ではない |
| 規則の個別適用・併用と、同じ処理を施した基準版との比較 | 開発3入力×6条件、別12入力×6条件、新9入力×6条件の静的結果を保存した。条件数は独立標本数として扱わない |
| 意味の確認と安全条件 | 自作整数912関数、抽出183式への19,398入力、XORの698ケースを確認した。有限個の入力での確認であり、全入力・全モジュールについての証明ではない |
| 別の乱数・変換量への適用 | 新しい8変換版は互いにSHAが異なる。すべて両規則の適用後に基準版とバイト列が一致した。同じ実装の派生版であり、独立した実装ではない |
| 通常コード・計測コードとの区別 | A-Star・CreaturePackの通常版と計測版は局所規則で変更されなかった。通常のbase64・seqtkにも定数の畳み込みが成立した。規則の適用を悪性の判定には使わない |
| 複雑な算術置換 | コードを書き換えない式解析を、xmrの開発標本とCryptic Bytes 60件に適用した。複数入力に依存する式等の対象外条件も記録した |
| 平坦化の限定的な確認 | 既知の4状態XORモデルで処理の役割を比較し、切り出した4関数で採掘を伴わないテストを行った。自動復元は未実装で、一般的な解除規則には組み込まない |
| import/exportと呼出し条件 | 144条件の関数型と関数以外のリソース宣言を解決して比較した。専用規則を適用した72条件では、関数署名、メモリ・テーブルの型と上下限、グローバルの型と可変性が保たれた。初期値・テーブル内容・ホスト全体の動作は未確認 |
| 構造・命令数・サイズ・残差 | 比較JSON/CSVに保存した。NOP版の最適化後に残った差は、NOPの残存ではなく他の命令の違いだった。原因となったpassと、最適化後の式が識別されない理由は未確認 |
| 正規化・解析の処理時間 | 入出力、ツール起動、最終検証を含め、6入力×4処理×6反復を追加測定した。24条件で出力SHAが一致した。専用処理は局所最適化より時間を要した。実装全体の時間であり、アルゴリズム自体の優劣には一般化しない。式解析時間は以前の単回の測定記録のみ |
| 対策後の公表ハッシュ入力・追加入力・速度 | 教員の許可を確認後に測定を完了し、監査に合格した。23種類のSHA、公表された5入力の期待値、追加した12入力の新規コンテキストと同じ順序で再利用したコンテキストでの比較、全138ブロックの出力・時間・順序・環境を照合した。summary.json/CSVとanalysisに確定結果を保存した |
| 測定の反復・順序・条件の統一 | 新しい測定は入力、ホスト、Linux Node/V8、1ワーカーを固定し、3秒ウォームアップしてから30秒以上の測定を6回繰り返した。反復ごとに対象の順序をずらし、実経過時間を記録した。旧測定の速度は新結果に流用しない |
| 代替手法と切替理由 | 単純な正規化では複雑な置換・平坦化が残ったため、式比較と限定状態モデルを追加した。一般的な検知手法として採用したものではない |
| 既存検知器の利用可能性・改善・通常コードへの影響 | MINOSの重みを固定し、独立環境で静的推論を準備した。8画像の独立計算と4条件の前処理を照合し、144条件を推論した。専用規則を適用した72条件ではクラスが変わった条件は0件だった。通常コードもMALIGNと予測され、スコアの飽和も見られた。訓練データとの重複・互換性は未確定で、一般的な分類精度や検知の改善は主張しない |
| 正規化による検知根拠の消失 | 専用規則を適用した72条件のうち10条件でNOPがなくなり、有無を表す特徴が失われた。36条件で命令総数が変化した。分岐・呼出し・メモリ操作の命令数は種類ごとに保たれた。MINOSの固定モデルでは専用条件でのクラス変化は0件だったが、一般的な検知の改善や構造全体の保持は未確認である。原本と変換記録の併用を考察に反映した |
| 手法の原理と仕組みの説明 | countermeasure-method-principles.mdに、局所正規化、既存最適化、式比較、限定状態モデル、実行経路、固定検知器の原理、適用条件、再現用のコード・資料、判断を整理した。一貫した速度向上はなく、限定的な解析前処理として採用した |
| 原稿の扱い | 変更後の作業範囲では編集しない。以前の原稿更新と8ページの確認は過去の記録であり、今回の納品条件ではない。新しい実験結果はMarkdown報告に記録する |
| 実施ログ・方針・パス一覧 | この文書、countermeasure-experiment-progress.md、各JSON/CSV・WAT・Wasmに保存した。人間による独立した機構レビューは必要 |
| 実行制約 | 教員の許可を確認し、ネットワークnone・CPU1・メモリ1GiB・最大2時間の隔離環境で、新しいハッシュ計算を完了した。外部プールへの接続、shareの送信、報酬の取得、攻撃、保護設定の変更、投稿は行わない。制限の根拠は実行ディレクトリのcontainer-inspect.jsonに保存した |

## 実装と再現用のコード・資料

パスはすべてリポジトリルートを基準とする。Pythonには `.tools/runtime-analysis-py312/Scripts/python.exe`、XORの実行には既存のNodeを使う。静的比較コマンドは採掘用Wasmを起動しない。

- `scripts/normalize_wat_local.py`：凍結した局所規則。
- `scripts/evaluate_local_normalization.py`：開発対の個別規則・併用・Binaryen比較。
- `scripts/test_local_normalization.py`：自作整数Wasmのみの採掘を伴わないテスト。
- `scripts/evaluate_normalization_transfer.py`：別プログラム・通常・計測コードへの比較。
- `scripts/evaluate_seeded_normalization.py`：新しい乱数・量の生成と静的比較。
- `scripts/review_seeded_optimizer_residuals.py`：保存したopcode残差の確認。
- `scripts/audit_normalization_signatures.py`：関数型番号を解決した静的署名照合。
- `scripts/audit_normalization_resources.py`：非関数import/export・定義リソースの型／上下限／可変性の静的照合。
- `scripts/test_normalization_resources.py`：7個の小さな非実行Wasmによる監査の確認。
- `scripts/analyze_normalization_feature_loss.py`：正規化で消えるNOP特徴・命令比率への影響と保持した命令個数の集計。
- `scripts/collect_detector_sources.py`・`scripts/audit_detector_feasibility.py`：固定公開ソースの取得／照合と読み取り専用の適用可能性確認。
- `scripts/inspect_minos_model.py`・`scripts/minos_static_inference.py`・`scripts/test_minos_static_inference.py`・`scripts/evaluate_minos_normalization.py`：重みの構造の確認、静的CNN推論、独立計算照合、固定条件比較。実行環境は`.tf/Scripts/python.exe`で対象Wasmは起動しない。
- `scripts/analyze_integer_expressions.py`：コードを書き換えない整数式解析。
- `scripts/test_integer_expression_analysis.py`：整数恒等式、改名、依存関係の伝播を止める命令の確認。
- `scripts/evaluate_integer_expression_analysis.py`：12標本・最適化前後の式解析。
- `scripts/evaluate_cryptic_expression_transfer.py`：固定選定60件への式解析。
- `scripts/check_extracted_expression_outputs.py`：抽出式の独立した整数照合。
- `scripts/prepare_isolated_xor_controls.py`：確認済みXOR4関数だけの切り出し・組み立て。
- `scripts/check_isolated_xor_controls.cjs`：小さなXORモジュールだけの採掘を伴わない実行。
- `scripts/check_reviewed_state_models.py`：事前に解析したモデルのコードを書き換えない比較。
- `scripts/prepare_countermeasure_runtime.py`・`scripts/check_countermeasure_runtime_plan.py`：条件・入力・順序の凍結と静的照合。
- `scripts/run_countermeasure_isolated.py`・`experiments/runtime-reference/countermeasure-benchmark.cjs`：許可記録の照合、隔離・資源制限、公表／追加出力の確認、実速度の測定。
- `experiments/runtime-reference/countermeasure-input-diagnostic.cjs`：基準版に対する新規コンテキストと、順方向・逆方向に再利用したコンテキストの限られた入力での診断。
- `scripts/summarize_countermeasure_runtime.py`：正常終了・全出力・138ブロックの監査を通過したログのみ集計する。
- `scripts/report_countermeasure_runtime.py`：監査済み実測と静的記録をSHAで結合し、CSV/JSON・比較図を生成する。
- `scripts/audit_countermeasure_deliverables.py`：根拠ファイルの絶対パス・サイズ・SHA一覧、報告リンク、実測との結合、論文に変更がないことを照合する。Wasmを起動しない。
- `paper/build.ps1`、`scripts/audit_mining_paper.py`：現行原稿のコンパイルと選択的整合チェック。

## 結果・出自・原稿

- `results/countermeasures/deliverable-evidence-index.json`：対策結果一式・説明書・報告書・参照実装・先行根拠のファイルごとの絶対パス、サイズ、SHAと分類。
- `results/countermeasures/deliverable-audit.json`：現在の報告参照、測定・集計・図の対応、論文3ファイル未変更の照合結果。全入力での同値性や検知改善の証明ではない。
- `results/countermeasures/local-normalization/static-comparison.json`
- `results/countermeasures/local-normalization/synthetic-tests/result.json`
- `results/countermeasures/transfer/comparison.json`・`comparison.csv`
- `results/countermeasures/seeded-normalization/generation.json`・`comparison.json`・`comparison.csv`・`optimizer-residual-review.json`
- `results/countermeasures/interface-signature-audit.json`
- `results/countermeasures/interface-resource-audit.json`・`resource-audit-tests/checks.json`
- `results/countermeasures/feature-loss/comparison.json`・`comparison.csv`
- `results/countermeasures/detector-feasibility/source-manifest.json`・`assessment.json`、`docs/countermeasure-detector-feasibility.md`
- `results/countermeasures/detector-feasibility/model-inspection.json`・`inference-adapter-checks.json`・`evaluation-selection.json`・`normalization-inference.json`・`inference-requirements.txt`
- `results/countermeasures/detector-feasibility/scale-sensitivity-selection.json`・`scale-sensitivity.json`：公開ソースにある2つの前処理尺度を固定して比較した結果。144条件中21条件で予測が異なった。専用規則を適用した72条件では、どちらの尺度でも正規化前後でクラスが変わった条件は0件だった。論文に反映済み。
- `results/countermeasures/expression-analysis/comparison.json`・`comparison.csv`・`tests.json`・`extracted-output-checks.json`
- `results/countermeasures/cryptic-expression-transfer/selection.json`・`comparison.json`・`comparison.csv`
- `results/countermeasures/flattening-xor/manifest.json`・`cases.json`・`checks.json`・`state-model-checks.json`
- `results/countermeasures/runtime-preparation/plan.json`・`professor-permission.json`・`active-measurement.json`：固定計画、利用者の許可確認記録、実行セッションと進捗。
- `results/countermeasures/runtime-preparation/input-order-diagnostic.json`：短い追加入力で確認した基準版の順序依存。原因や全入力の正しさを確定する資料ではない。
- `results/countermeasures/runtime-runs/execute-d50a31528b9b4608b2de1ba1222ce030`：初回の照合失敗と速度測定0の生ログ。正常に測定できた速度へ算入しない。
- `results/countermeasures/runtime-runs/execute-120f528e37424ec6806047c933011eec`：正常終了・監査済みの今回の実測。inputs、container-inspect.json、outputs/measurement.json、completion.json、summary.json/CSV、analysis/structure-runtime.json/CSVとPNG/SVG。
- 各結果ディレクトリの `*.events.json`、条件別JSON、WAT、Wasm：命令・差分・入力・出力の詳細。
- `results/runtime-mining/cross-dataset/swamped/controlled-pair-manifest.json`：開発対の出自。
- `results/provenance/cryptic-bytes-parents.csv`：Cryptic Bytesの配布パス・設定・基準対応。
- `results/runtime-mining/cross-dataset/proof-of-theft/xmr-helper-flattening-review.json`・`xmr-helper-path-review.json`：限定状態モデルの根拠。
- `paper/main.tex`・`paper/references.bib`・`paper/main.pdf`：既存研究を確認する資料。今回の作業では変更しない。current-objective-scope.jsonのSHAで未変更を確認する。
- `results/mining-methods/current-compilation.json`：現行のsource/PDF/logのSHAとページ・表示確認。
- `docs/countermeasure-experiment-progress.md`：方針変更、結果、採用・不採用の判断、留保の詳細。

## 次の作業と再開条件

今回の実測、監査、集計、図表作成、説明書・報告書の作成は完了した。再解析ではreport_countermeasure_runtime.pyに保存済みrunを指定し、Wasmは再実行しない。人間による独立レビュー、初期値・テーブル内容の確認、JIT、未対応式や状態の自動復元は今後の研究課題として残る。変更後の作業範囲では論文・PDF・エディタを変更しない。

新規の実行を追加するときは許可範囲とネットワーク無効・CPU・メモリ・時間制限を照合し、別runとして生ログを残す。論文反映は今回とは別の作業である。

## 前処理時間の追加比較

以下の準備・実装の各節は時系列の記録である。「未実行」「未確認」等は記録当時の状態であり、現在の実行状況は冒頭の表と末尾を参照する。

前処理時間は `docs/countermeasure-processing-time.md` に報告し、根拠を `results/countermeasures/processing-timing/{selection.json,results.json,summary.csv,processing-times.png,processing-times.svg}` に保存した。測定の実装は`scripts/benchmark_normalization_processing.py`、集計は`scripts/report_normalization_processing.py`である。原稿6.1節に反映した。この時点では対策後のハッシュ実測は引き続き未実施である。

## ハッシュ実測の準備（未実行）

開発18条件と別乱数54条件の計72条件を、SHAが異なる23種類にまとめた。公表された5入力、追加入力12件、6反復・138ブロックの予定を固定した。候補ファイルのSHA、重複する条件の対応、各反復で全対象を1回ずつ測定すること、入力長を静的に照合した。既存Dockerイメージの存在はinspectで確認したが、コンテナは起動していない。根拠はdocs/countermeasure-runtime-plan.mdとresults/countermeasures/runtime-preparation/plan.json・preparation-checks.json・plan-audit.jsonに保存した。この時点ではランチャーを実装しておらず、教員の許可も未確認で、新しいハッシュ結果はない。

## 2026-10-10：隔離ランチャーと採掘を行わない事前確認（probe）

隔離ランチャーと測定runnerを実装した。最終probeで実際のNode/V8、23種類のSHA、ホストSHA、Dockerの制限を照合し、正常終了を確認した。対象Wasmは構築も実行もしていない。教員許可の記録がないexecuteは、コンテナ作成前に拒否された。まだ許可を確認していないため、許可記録は作成していない。根拠はruntime-preparation/isolation-probe.json、詳細はcountermeasure-runtime-plan.mdに保存した。この時点では実際のハッシュ計算、138ブロックの測定、タイムアウト動作は未検証で、論文にも新しいハッシュ結果を追加していない。

## 2026-10-10：測定runnerの異常系確認

採掘を行わない模擬ホストで7項目を確認した。許可なし、不正な許可、SHA不一致をホストの読み込み前に拒否し、正常時の計数・速度計算・順序の確認に合格した。不一致や例外では、途中までの失敗ログを保存する。不一致時の実際値、期待値、対象フェーズを残すようrunnerを修正し、runner-mock-checks.jsonにコードSHAと確認範囲を保存した。WebAssembly APIは使わず、実際の許可記録も作成せず、新しいハッシュ計算も実行していない。実際のWasmとタイムアウト処理は未検証である。詳細はcountermeasure-runtime-plan.mdに記載した。

## 2026-10-10：集計の欠測・誤出力拒否と比較基準

集計コードsummarize_countermeasure_runtime.pyを追加した。138ブロック、公表入力・追加入力の出力、順序、ウォームアップ、環境、出自を確認してから、23種類のSHAの結果を72条件に対応付ける。未処理の基準版、同じ処理を施した基準版、同じ入力の未処理版は、それぞれ比較する。summary-mock-checks.jsonの20項目は人工ログでの確認であり、実際の速度結果ではない。probeを実測として集計することは拒否された。runnerにウォームアップの実記録を追加し、模擬確認の7項目を再実行した。この時点では実際のWasmを実行しておらず、許可も未確認で、速度比較表はまだ作成していない。詳細はcountermeasure-runtime-plan.mdに記載した。

## 2026-10-10：実際のコンテナの時間上限確認と再開条件

WasmをマウントせずNodeが待機するだけのコンテナで、共通ランチャーの2秒の時間上限、attachの打ち切り、この実行専用のIDの削除を確認した。deadline-checks.jsonと対応する生ログを保存した。採掘実行前の準備は、静的照合、probe、模擬確認、集計確認、時間上限の確認まで進んだ。次に必要なのは、許可を確認して新しいハッシュ計算を実測し、論文に反映することである。旧ログや形式的な追加確認では代替しない。目標はまだ達成しておらず、実験も稼働していない。

## 2026-10-10：教員許可確認後の実行と短入力の順序依存

教員の許可について利用者が「許可はとれてる」と回答したため、固定したローカル計画に対応するprofessor-permission.jsonを保存し、実行を開始した。外部通信、プール接続、報酬の取得は行わない。初回のexecute-d50a31528b9b4608b2de1ba1222ce030は、公表入力の後に追加入力を順方向・逆方向で照合した際、32バイト入力で停止した。速度測定は0ブロックだった。失敗した対象は別乱数NOP版にBinaryen局所処理を施した版（SHA02a5eaea…）であり、未処理の基準版ではない。失敗ログは残す。

基準版を限られた入力で診断したところ、公表された5入力、追加の76／128／255バイト入力、nonceを変更した6入力は、新規コンテキストと順方向・逆方向に再利用したコンテキストで出力が一致した。一方、1／8／32バイト入力は、再利用時の順序によって出力が異なった。新規コンテキストで行った2反復は一致した。原因がバッファ末尾や内部状態などのどれにあるかは未確定である。この結果だけでは、難読化によって意味が保たれなかったとも、通常のCryptoNightの正しい出力が得られたとも断定できない。根拠はinput-order-diagnostic.jsonと対応する生ログに保存した。

短入力は除外せず、すべての追加入力について、新規コンテキスト同士で基準版と出力を比較する照合を追加した。再利用時は、基準版と変換版で公表入力による初期状態と追加入力の順序をそろえ、順方向・逆方向それぞれの基準出力を使う。公表入力の独立した期待出力は変更しない。追加入力は、あくまで基準版との差を確認するために用いる。修正したrunnerの模擬7項目と、人工ログによる集計の20項目を確認し、execute-120f528e37424ec6806047c933011eecで再実行中である。目標はまだ達成していない。

## 2026-10-10：新しい実際のハッシュ測定と分析の完了

execute-120f528e37424ec6806047c933011eecは、SHAが異なる23種類を各6回、計138ブロック測定して正常に終了した（終了コード0、OOMなし）。公表された5入力の照合、追加した12入力の新規コンテキストと同じ履歴で再利用したコンテキストでの順方向・逆方向の比較、計測前後・最終出力、SHA、隔離設定、順序、ウォームアップ、時間、速度計算の監査に合格した。ランチャーのセッション90237も終了コード0を返した。実行用コンテナIDに対するDocker inspectがno such objectを返すことも確認した。

summary.json/CSVには、72ラベルを23種類のSHAの各6反復に対応付けて保存した。analysis/structure-runtime.json/CSVで静的記録をSHAにより結合し、development-ratesとstructure-versus-rateのPNG/SVGを生成して表示を確認した。中央値と各反復内で求めた比は区別し、最小値～最大値の範囲を信頼区間とは扱わない。速度の中央値は、基準版31.4921 H/s（26.5502～32.0761）、開発NOP版30.6473、整数定数分割版31.6732だった。両規則の適用後は同じ基準SHAの測定値を共有する。各未処理版に対する中央値の比は1.0276／0.9943、別乱数8版では0.9827～1.0120だった。一貫した高速化は確認できず、構造を整理できたことと、速度・検知が改善することは区別した。

countermeasure-method-principles.mdとcountermeasure-experiment-report.mdに、仕組み、全開発条件の表、別乱数の表、図、先行評価との関係、採用・不採用の判断、限界をまとめた。単純変換に対する限定的な解析前処理と、コードを書き換えない式比較を採用した。平坦化の自動解除、速度・検知の改善、全入力で意味が保たれることは達成していないと明記する。変更後の作業範囲に従い、論文・PDF・エディタの変更、投稿・外部公開は行わない。人間による機構レビュー等は、今回の実験で確認できていない課題として残す。
