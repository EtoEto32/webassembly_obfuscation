# 追加評価の再現手順

2026年10月16日。性能測定・監査・構造集計・呼出し箇所診断、正規化77条件の出力照合と対応付け課題、図5点の目視確認が完了した。本書は確定した入力・手順と結果の読み方を記録する。統合した結果は [研究報告](followup-research-report-20261016.md)、詳細は [性能評価](followup-performance-results-20261016.md)・[正規化比較](followup-normalization-results-20261016.md)、原稿への接続は [論文反映案](paper-followup-reflection-20261016.md) に分ける。

## 保存と実行環境

今回の追加物の保存先は `results/followup-evaluation-20261016/`。過去の `results/countermeasures/`、公開データの `data/`、`paper/main.tex` は保持する。失敗したコンテナ起動、最初のWAT生成、予備測定のコンパイラ条件不一致も削除しない。

今回実際に使用する環境はWindows上のDocker Desktop、固定Linuxイメージ `sha256:a05286e66b0f1ca712671db5849229594c92e035bae253362cc8b6d0af4a70b6`、コンテナ内Node18.20.4／V8 10.2.154.26-node.37、Intel Core i9-11900Kである。ホスト側のPythonは `.tools/runtime-analysis-py312/Scripts/python.exe`、WABTは1.0.42、Binaryenは133を用いる。図にはmatplotlibとWindowsのMeiryoを用いる。ホスト側Nodeの版をコンテナ内Nodeの版と混同しない。

イメージの元のDockerfileは `experiments/runtime-reference/Dockerfile` にある。ただしaptパッケージの版をすべて固定していないため、新しくbuildするだけで同じイメージIDやNode版になるとは保証できない。完全に同じ実行環境を別ホストへ持ち出す場合は、既存イメージを `docker image save` で保存して `docker image load` で取り込み、上記IDを確認する。異なるイメージでの実行は条件の異なる追試として記録する。

実行前の資産照合と実際のコンテナ設定の確認は `scripts/run_followup_isolated.py` が行う。ネットワークnone、CPU上限1、ゲストCPU0、メモリとswapの合計上限1GiB、pids64、非root、読み取り専用root・入力、cap-drop ALL、no-new-privilegesを指定する。許可は既存の `results/countermeasures/runtime-preparation/professor-permission.json` をそのまま保持し、新しい計画はそのSHAと今回のユーザー指示を参照する。古い許可記録が新しい計画へ直接発行されたように書き換えない。

## 入力・生成物・計画

1. `plan.json` は固定76バイト読取りの診断計画で、3変換条件と別配布の参照実装を含む。
2. `runtime-pilot-plan.json` は2巡回・72ブロックの予備測定である。Liftoff指定は実際には混在しており、純粋なLiftoffの比較には使わない。
3. `compiler-probe-plan.json` は修正した設定の短い確認実行で、主測定の反復に加えない。
4. `path-plan.json` は関数入口の計数と手動のXOR部位復元の出力確認、`callsite-plan.json` は関数118への呼出し箇所の診断である。診断版の速度を原版の速度とみなさない。
5. `controlled-generation-v2.json` は同じ変換・乱数20261016・割合0.1で作成した3実装×3条件を記録する。`controlled-check-plan.json` は333件の出力照合に用いる。
6. `confirmatory-plans.json` は3セッションの計画SHAを固定する。対応する `confirmatory-session-1-plan.json` ～ `confirmatory-session-3-plan.json` が13バイナリ、2コンパイラ条件、6巡回、計272ブロックを定義する。

計画中の各assetのSHA、runnerのSHA、生成物のSHAを実行時に照合する。上流の変換関数は保持し、関数末尾の閉じ括弧を分けるWATアダプタの修正と最初の失敗を区別して記録する。

## 再実行

以下はPowerShellで実行する。実行中の研究用ディレクトリで別の測定を同時起動しない。まず既存のexecハンドルまたはDockerコンテナの稼働状態を確認する。保存された `running` とPIDだけから再起動を判断しない。

```powershell
$researchRoot = 'C:\Users\ettotto\Documents\webassembly_obfuscation'
Set-Location -LiteralPath $researchRoot
$researchPython = Join-Path $researchRoot '.tools\runtime-analysis-py312\Scripts\python.exe'
```

既に固定した計画を再利用する個別の再実行は、次の形式で行う。ランチャーは新しいUUIDのrunディレクトリを作り、既存の結果を上書きしない。`--plan` と `--runner` は対応させる。

```powershell
& $researchPython scripts/run_followup_isolated.py --plan results/followup-evaluation-20261016/plan.json --runner input-diagnostic.cjs --mode input-diagnostic
& $researchPython scripts/run_followup_isolated.py --plan results/followup-evaluation-20261016/controlled-check-plan.json --runner controlled.cjs --mode input-diagnostic
& $researchPython scripts/run_followup_isolated.py --plan results/followup-evaluation-20261016/path-plan.json --runner paths.cjs --mode input-diagnostic
```

本測定の3セッションをまとめて再現する場合は、元の成果を残した別の実験用コピーを使う。固定計画と、そのasset一覧が指すファイル・スクリプト・必要なツール・許可記録を同じ相対配置でコピーする。その新しいコピーには、再実行によって作る `confirmatory-execution/`、`post-performance/`、`confirmatory-summary.json`・CSV、`confirmatory-structure.json`、`callsite-summary.json`、`figures/confirmatory-*` 等の出力を持ち込まない。既存ファイルがあると保存ガードで停止する。元の研究用ディレクトリの記録を削除してガードを回避しない。

```powershell
& $researchPython scripts/run_followup_confirmatory_sessions.py
```

このコマンドは各セッションを順番に実行し、直後に厳密監査する。測定または監査が失敗した場合は停止する。各ブロックは新規子プロセス、ウォームアップ5秒以上、計時30秒以上である。計時とウォームアップだけで全体約159分となり、初期化・出力照合等が加わる。各コンテナの上限は2時間であり、全体2時間ではない。

計測後の処理は以下のコマンドで直列化する。`<execution-directory>` は当該コピーで新しく作成された `confirmatory-execution/<UUID>` の実在パスに置き換える。測定プロセスが開始してstatusファイルが作成された後に、別ターミナルから起動できる。3セッションすべての完了を待ち、静的集計、性能集計、呼出し箇所の実測・監査を順に実行する。

```powershell
& $researchPython scripts/after_followup_performance.py --after '<execution-directory>'
```

図は最終集計から作る。完了していない測定値や仮の値を図に補わない。描画後にPNGを開き、凡例・軸・文字・区間・ラベルを目視確認する。

```powershell
& $researchPython scripts/plot_followup_confirmatory.py
```

## 監査と解釈

新しく完了したrunの監査は `audit_followup_input.py`、`audit_followup_checks.py`、`audit_followup_confirmatory.py` が対応する。これらは既存の監査成果物を上書きしないため、既に監査済みのrunに対して同じコマンドを再発行して成功扱いにしない。監査記録と参照SHAを確認するか、新しいrunを監査する。

本測定では出力・nonce・入力76バイト、計数とH/s、時刻とブロックの非重複、計時条件、入力SHA、コンテナ設定、CPU統計を照合する。全コンパイル記録が指定した種類であることと、計時開始・終了マーカーの間にコンパイルがないことを確認する。フラグの名前だけで条件成立とは判断しない。

コンパイルの監査対象はWasmである。JavaScriptホストのJITとその他すべてのランタイム処理を追跡しているわけではないため、Wasmの記録が0件でも計時区間から全種類のJITを排除したとは主張しない。

速度比は前後の近接基準を計時中点で線形補間して求める。全18種類×6巡回の108比較を保持する。探索的な95%区間は3セッションの平均対数比を単位とし、自由度2のt分布を用いる。3連続セッションだけでは独立性等を検証できず、実用的同等性や一般環境での効果を保証しない。後から遅いブロックを除外しない。

静的命令数、関数入口の回数、呼出し箇所の回数、時間割合は別の量である。部位復元は同じ公開平坦化版内の関数本体だけを手で戻した対照であり、自動正規化の実装ではない。有限入力の一致を全入力の同値性証明としない。

## 既存成果との照合

`inherited-evidence-index.json` は既存の正規化144静的条件等を保存済みの記録とSHAで照合した索引である。全条件を今回再実行したことは意味しない。`prior-method-audit.json` は保存された先行研究のソースを取得元treeのGit blob SHAと照合する。先行研究のO3指定と過去のBinaryenコミットを尊重し、今回のBinaryen133の比較を完全再現とは呼ばない。

## 正規化の生成・照合・対応付けの再実行

上記の入力原本・固定ツール・既存の出力検証計画に加え、既存の `results/countermeasures/flattening-xor/` の抽出関数・698ケース・manifestを保持する。固定した正規化計画のrequired_sourcesとinputsが指すファイルがすべて必要である。原本は別コピーに保持し、新しい生成・集計先の `normalization-artifacts/`、`normalization-static.json`、`normalization-helper-truth/`、`normalization-function-features.json`、`normalization-matching-results.json`、正規化図の出力は未作成の作業コピーを使う。固定計画を再利用する場合は、以下の最初の生成コマンドを省略する。

```powershell
& $researchPython scripts/prepare_followup_normalization.py
& $researchPython scripts/evaluate_followup_normalization.py
```

この処理はWasmをインスタンス化しない。表示アダプタの前後一致、77条件のWABT検証、APIと資源型、適用ログ、標準WAT、入力・出力SHAを保存する。規則のソースは既存のままで、計画中のSHAと照合する。

出力の追試には次の再実行用スクリプトを使う。引数なしは資産を照合して11個の7条件バッチの計画を固定するだけで、`--execute` が実際の隔離実行である。同時に複数起動しない。元の大きいバッチでのOOMを繰り返す必要はない。Windowsのパス長に対処するため、実行用計画は浅い出力階層へ置く。既存の結果は上書きしない。

```powershell
& $researchPython scripts/replay_followup_normalization.py
& $researchPython scripts/replay_followup_normalization.py --execute
```

新しい結果は `normalization-replays/<UUID>/status.json` と各runの `controlled-audit.json` に保存する。全77ラベルと2,793照合を確認する。これは元の77条件の主評価とは別の再実行であり、独立した実装数や標本数に加えない。最初の主評価のOOMと9バッチへの改訂、再実行用スクリプトの最初のパス長による失敗も記録として保持する。

複雑な補助関数の採点根拠を確認し、名前だけを付けた補助コピーから関数の由来を追って照合課題を再現する。補助関数の検証はホスト側Node v24.19.0を使用し、memory 1ページ・importsなしの抽出モジュールだけを実行した。採掘本体のNode18コンテナ実行と区別する。既存の生成済みCJSがある場合は、同じ内容であることを確認して保持する。

```powershell
& $researchPython scripts/prepare_followup_helper_truth.py
$researchNode = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
& $researchNode --max-old-space-size=256 scripts/check_followup_helper_truth.cjs
& $researchPython scripts/prepare_followup_function_task.py
& $researchPython scripts/score_followup_normalization.py
& $researchPython scripts/plot_followup_normalization.py
```

関数の指紋は実際の処理結果から作る。補助コピーに付けた採点用の名前を指紋へ混ぜず、全77条件で非カスタムセクションが実際の結果と一致することを確認する。関数4,508問い合わせ・モジュール56問い合わせをすべて報告し、削除・統合等で由来を追跡できない関数も固定分母に残す。図を開いて表示を確認する。前処理・指紋抽出・辞書参照・採点の時間の範囲は別であり、同一の解析時間として比較しない。

## 成果物の入口

- [統合報告](followup-research-report-20261016.md)：目的、既存研究との関係、追加結果と正規化の開発課題。
- [性能評価報告](followup-performance-results-20261016.md)：272ブロック、静的構造、生成コード、実行箇所と図3点。
- [正規化比較報告](followup-normalization-results-20261016.md)：77条件、42SHA、2,793照合、対応付けと図2点。
- [論文反映案](paper-followup-reflection-20261016.md)：既存RQと結果を保持した配置、追記文、アブストラクト・まとめの文案。
- `results/followup-evaluation-20261016/`：固定計画、原本を参照するSHA、生成物、実測、監査、失敗・修正履歴。
