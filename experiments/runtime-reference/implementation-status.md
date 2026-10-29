# 実装状況

## 確認できたこと

- Cryptic Bytesの通常版・個別手法の変換版340件のSHA-256と既存静的解析メタデータを照合した。
- 元の論文の通常版6本のオブジェクトを照合した。
- 配布WAT61件（通常版5件、variants枝49件、MCMC枝7件）をWABT 1.0.42で再構成した。名前に記されたハッシュとの完全一致は通常版3件だけであり、他の再構成物を元のバイナリと同一とは扱わない。MCMC枝のファイル名には元バイナリのSHA-256がないため、完全一致の判定対象外とした。詳細はreference-reconstruction.csvを参照する。MCMCのsigma=0.3は2件であり、本文の全比較対象は揃っていない。
- 元の論文の収集コードと同じ1,001件取得・先頭10件除外を実装し、人工カウンタで動作を確認した。これは採掘結果ではない。
- 通常版cn-0のブラウザ初期化に成功した。外部通信なし、ハッシュ計算なし。配布元のcn-0.jsは配布Wasmの要求する関数を提供せず、そのままは使えなかったため、公開CコードのABIに沿うアダプタを作成した。
- coin-hive-stratum 2.6.11を固定して取得した。元の論文の実際のパッケージ版とは未照合。寄付は明示的に無効化し、接続先をローカルxmrig-proxyに固定するbridge.cjsを実装した。プール応答を記録するが、未接続。
- 元実装同梱のxmrig-proxyはmacOS版6.18.0と確認した。同じ6.18.0の公式Linux版を取得し、公式SHA256SUMSとの一致を確認した。必要なmuslローダーをDockerfileに追加し、外部通信なしで版表示の起動に成功した。proxy-version.logとproxy-provenance.jsonに保存した。版は同じだが、OS、コンパイラ、libuv、OpenSSLは元同梱物と異なる。
- 中継の提出ログを、send呼び出しから実際のローカルproxyソケットへの書き込み時点へ変更した。未認証で取り消された要求は提出件数に入れない。人工メッセージで受理・拒否ログと送信失敗を確認した（bridge-software-check.log）。このテストはプール受理やハッシュの正しさの証拠ではない。
- MoneroOceanの運営元公開APIの保存データでは、対象に関係するcn/rとcn/halfはinactive、他の対象8種は未掲載だった。確認日2026-10-07。pool-compatibility-audit.jsonに根拠と保存元のハッシュを記録した。他のプールも存在しないとは結論しない。
- musl追加後の初期化チェックでは、Chromium起動前のMODULE.read_bytes()でOSError errno 12となった（最新readiness-attempt.log）。以前の初期化成功を新イメージの成功と読み替えない。ハッシュ計算未到達であり、採掘アルゴリズムの正誤や性能については判断できない。
- 当初Cryptic Bytes cn-0用としてmining-worker.js、mining-client.js、serve_mining.pyを実装した。ローカル中継のみ接続し、開始ボタン、停止ボタン、累積ハッシュ数、share送信、ジョブ切り替え、アルゴリズム不一致時の停止を扱う。元の論文のCoinHiveランタイムそのものではない。配布元workerのnonce位置・エンコード・target判定を基準とし、1ハッシュごとのworker通信を使うため、そのオーバーヘッドを含む環境差がある。元の論文と同じ速度条件と称さない。その後、後述する10種類のソースに合わせて入出力条件を切り替える実装に拡張した。
- ブラウザclientの通信処理を人工メッセージで確認した。自動開始しないこと、古いジョブのshareを送らないこと、累積数の保持、アルゴリズム不一致時の停止を確認した。Wasmとハッシュ計算、外部プールはこの確認では使用していない。
- collectorに実行停止時の中断とcollection-failure.jsonの保存を追加した。すべて0のカウンタから採掘成功を主張しないよう、集計にも計算観測の有無を記録する。
- target-pairing-audit.jsonで別データセットの通常版20組と変換版320件の対応をマニフェスト上で照合した。組はプログラムと最適化の有無で分ける。元論文のbaseline/MCMCとは別の対象であり、実行可能性は未確認。
- 元公開collect_mcmc.shには、proxy引数の-0、通常版サーバ引数のfbdd1e固定、sigmaごとのログ上書きがある。plot_distributions.pyには不足分布を乱数で補う処理がある。これらを無検査で実行しない。生ログを保持し、測定していない分布は作成しない。根拠ファイルのSHA-256と差異をtarget-pairing-audit.jsonに保存した。
- 別データセットの10プログラムすべての固定コミットのmain.cを取得し、hash_cn内部で上書きされるlite/variantをalgorithm-contracts.jsonに記録した。アダプタ、worker、client、サーバをこの入出力条件に合わせて切り替える実装に拡張した。サーバは入力SHA-256と宣言プログラムの対応を既存マニフェストで照合し、cn/rでは実ジョブのheightを必須とする。実際の10種類の初期化・ハッシュ計算の成功は未確認。CoinHive用ABIは引き続き別対応が必要。
- 既存静的解析のimport/export名と種別を照合した範囲では、別データセット340件すべてがアダプタの提供名と必要exportに一致した。adapter-abi-audit.jsonに保存した。関数型の照合、実行互換性、日時・タイムゾーン関数が呼ばれた場合の対応は未確認であり、この一致から採掘可能とは結論しない。
- 既存paper/main.texを編集し、参照論文のMetric 3・4に沿う検証設計、対象と環境の差、実装状況と未測定事項を追加した。静的結果の数値は保持し、タイトル・日英要旨・導入・限界・まとめを当時の「静的解析と実行評価の設計」という範囲に更新した。references.bibに参照論文と固定コミットの公開実装を追加した。実測結果の反映は未完了。
- 内蔵compile_latex_documentはプラットフォームの標準ディレクトリを見つけられず停止した（Unable to find standard directories for platform）。この記録時点ではコンパイル成功は未確認。ソースと現在のエディタを保持し、別文書や別PDFを作成していない。
- analyze_reference.pyに公開get_table.v2.pyと同じ平均±2母標準偏差の開区間による集計を追加した。未加工の990差分を保持し、一定値でフィルタ後が空となる場合は中央値をnullにする。compare_reference.pyは宣言した通常版と同じプログラム・最適化条件の変換版を比較する。実測ログのないグループは欠測として残し、人工データを拒否する。速度分布は未加工の実測差分によるバイオリン図とし、一定値は実値の印で示す。実測図表は未作成。
- 人工データを拒否することと、欠測を補完しないことをcheck_comparison.pyで確認した（comparison-software-check.log）。専用Python 3.12環境.tools/runtime-analysis-py312にMatplotlib 3.10.6を準備し、依存版と取得元をanalysis-requirements.lock.txt、analysis-install-report.jsonに保存した。これは採掘結果ではない。
- SumokoinのFairhash候補の現在の公開ページはHTTP 200だがHTMLタイトルが404 - Page Not Foundだった。プールの設定やアルゴリズムを確認できず、対応先として採用していない。取得ページとfairhash-candidate-check.jsonを保存した。
- 現環境の初期化確認を再実行したが、同じMODULE.read_bytes()のerrno 12で停止した。時刻付きreadiness-2026*.logに保存した。直近3時間のDefender検出ログを読み取り専用で調べ、元HTMLとREADMEの検出を確認したが、対象cn-0オブジェクトの一致は見つからなかった。readiness-defender-log-check.jsonに照合範囲を保存した。これだけではファイル読み込み失敗の原因を断定できない。保護機能の設定変更、隔離ファイルの復元は行っていない。
- 完了条件をgoal-completion-audit.jsonに照合した。実測、実測図表、論文への実測反映、内蔵コンパイルの成功は未達成。利用許可のある別Linux環境があるかを利用者に確認中。ゴールを完了扱いにしていない。

## 未完了

### この記録時点の再開条件

追加ランナーとDocker起動手順を実装した後に再監査した。この記録時点では本人アドレスを含む設定はなく、operator_verifiedもfalseのまま。実測用コンテナは稼働しておらず、hash-samples.csv、collection.json、run-metadata.jsonを持つ実測ディレクトリはない。直前のターンではDockerで設定検査まで到達するという進捗があったが、その確認は実測の代わりにならない。最新の再開後も同じ外部条件の不足が3回以上継続しているため、未達成のままブロックとして記録する。利用者に必要な作業は本人用XKR公開アドレスの準備であり、プールの条件確認や実装を利用者の担当に移すものではない。アドレスが届いても、未確認の運営者条件を自動的に確認済みにしない。

### 実測ランナーの実装（外部実行は未確認）

run-mining-docker.ps1を追加した。既存イメージを使い、必要な入力・コード・設定・検証記録だけを読み取り専用でマウントし、実測出力だけを書き込み可能にする。ポート公開なし、非root、cap-drop ALL、no-new-privileges、2 CPU・2 GiB・256 PID上限で実行する。既定は--network noneの設定検査であり、-Executeを明示した場合だけ外部接続を可能にする。Python側でも未確認設定を拒否する。Chromiumは到達不能なローカルHTTPプロキシを指定し、127.0.0.1/localhostだけを直接通信の対象にする。外部プール通信はxmrig-proxyに担当させる。これらの実測時の連携動作は未確認。

最初のDocker設定検査はPythonのスクリプトディレクトリ探索時のerrno 12で停止した（docker-runner-validation.log）。不要なスクリプトディレクトリ探索を省くPython 3.11標準の-Pを追加した後、同じ未確認exampleは設定検査まで進み、運営者条件の未確認を理由に外部プロセス起動前に拒否された（docker-runner-safe-path-validation.log）。この結果はその探索失敗への対処であり、Wasm本体の読み取りや採掘実行の安定性を示さない。-PはPython 3.11の既存Docker環境用で、Python 3.9環境での実測起動は対象外。

Dockerからの設定検査コマンドは以下。実行時の値は参照論文と同一とは主張せず、入力、スレッド数、CPU・メモリ制限、ソフトウェア版とともに保存する。設定検査でのThreads=1は採掘実験条件の選定ではない。採掘を行っていない。

```powershell
./experiments/runtime-reference/run-mining-docker.ps1 -PoolConfig <確認済み設定.json> -ModuleSha256 <対象のSHA-256> -Threads <明示したスレッド数> -RunId <新しい識別名>
# 実測は接続条件・本人情報が揃った後に、同じ引数へ -Execute を追加する。
```

run_mining.pyを追加した。確認済み運営者情報・確認日、本人の公開識別情報、対象と一致するアルゴリズム、入力と公式proxyのSHA-256を確認してから、Linux上でproxy、中継、ローカルサーバ、収集処理を起動する。通常版と各変換版は別々の新規ディレクトリへ保存する。設定は単一外部プール、寄付0、ローカル待受、HTTP API無効、proxyのsimple modeを指定した。simple modeは現在のアダプタ用の設定案で、元の論文と同一条件とは未確認。コード、設定、コマンド、入力、プロセスの生ログを残す。プロセス終了時はこのランナーが起動した子プロセスだけを停止する。

collectorはランナーが先に保存したログと同じディレクトリを利用できるようにしたが、hash-samples.csvは排他的新規作成とし、既存の収集結果・失敗記録があれば開始しない。人工カウンタのcheck_collector.pyは変更後も1001件の取得・991件の保持・990個の差分を確認できた。verified-pool.example.jsonの未確認設定では、--validate-onlyが運営者条件の未確認を理由に起動前に拒否した。これは設定検査の証拠で、採掘機能・プール受理・速度の実測ではない。完全なDocker起動手順とエンドツーエンドの動作確認は残っている。

再開時には運営元情報と本人アドレスを実際に確認してから設定ファイルを作る。以下はLinux環境内の未実行コマンド例であり、exampleの確認フラグを根拠なくtrueに変更しない。

```sh
python3 experiments/runtime-reference/run_mining.py --pool-config <確認済み設定.json> --sha256 <対象のSHA-256> --threads <明示したスレッド数> --output <新規実測ディレクトリ> --validate-only
python3 experiments/runtime-reference/run_mining.py --pool-config <確認済み設定.json> --sha256 <対象のSHA-256> --threads <明示したスレッド数> --output <新規実測ディレクトリ>
```

### プール候補の追加選定

後続確認でFastPoolの公式掲載ポートfastpool.xyz:10092へのTCP接続は成功した。ログイン、ジョブ要求、share提出は行わず、fastpool-endpoint-reachability.jsonへ保存した。HTTPS公開ページの取得失敗と採掘用ポートの到達性を区別する。公開HTTP案内の取得は503だったため、利用条件と現在のStratum動作は引き続き未確認。保存済みtechy.ddns.net.htmlはHome Assistantであり、プール案内ではなかったため候補から除外した。

2026-10-07、Kryptokrona公式FAQのcn-pico/trtl指定と、現行公式設定生成コードのfastpool.xyz:10092、swepool.org:3333、techy.ddns.net:3333を確認した。運営者の公開ページでXKR/CryptoNight Picoを掲載するFastPoolを最初に検証する候補として選定した。既存cn-pico-trtlの候補であり、他9種や元の論文6本への対応を意味しない。現在の端末からFastPoolのHTTPS公開ページはPowerShell・curl・ブラウザで接続切断となり、残り候補も公開案内を取得できなかった。公式掲載だけで稼働・利用条件・採掘受理を確認済みにはしない。根拠と制約はresults/runtime-mining/pool-sources/kryptokrona-selection.jsonに保存した。プール調査はエージェント側の作業であり、対応先が確定するまでは利用者へウォレット作成を要求しない。

### 2026-10-07 20:23以降の再確認

後続の同一コンテナ内読み取り比較では、read-allとread-4096がともに310,503 bytesを取得し、SHA-256も元cn-0と一致した（input-read-strategies.log）。今回の比較ではエラーは再現せず、読み方の違いが解決策だという証拠は得られていない。実験サーバの読み取り方法は変更していない。

利用者が保護を一時解除したと報告した後、こちらでは保護設定を変更せず、既存Docker環境を再確認した。cn-0の単独初期化は成功した。その後、マニフェスト上の通常版20件を各1回初期化し、8件成功・12件ファイル読み込み失敗だった。ログはresults/runtime-mining/baseline-readiness-20261007-202404/に保存した。同じcn-0も後続確認では失敗しており、読み込みは安定していない。初期化成功はハッシュ計算やプール受理の成功を示さない。

失敗した初期化コンテナ自体の診断では、対象ファイルは310,503 bytes、memory.max=2,147,483,648 bytes、memory.current=37,650,432 bytes、memory.eventsのmax/oom/oom_killはすべて0だった（readiness-diagnostic-2026*.log）。少なくともこの失敗時にはコンテナのメモリ上限到達は記録されていない。別の読み取り専用診断では先頭4KBの読み込みに成功した（input-read-diagnostic.log）。これらからWindows保護機能、Docker共有ファイル、ホストの状態のどれが原因かを断定しない。

check-baseline-readiness.ps1はこの20件の初期化確認を再実行し、各入力の生ログとsummary.jsonを保存する。追加の研究評価項目ではなく、対象の実行互換性を確認する準備作業である。採掘速度測定と外部プール接続は未実施。利用枠の確認値は使用16%、残り84%だった。

- 対応プールの運営元情報・現行アルゴリズムと利用条件の確認。
- ご本人の接続識別情報（受取アドレス等）の準備。ご本人はまだ所有していない。
- xmrig-proxyの採掘用設定と接続、ブラウザ採掘workerと中継の接続。版表示だけの起動は確認済み。
- 配布元の本文の全比較対象と各10本の生成条件の確定。配布ツリー上のvariants枝とMCMC枝は収集・作図コードを根拠に区別したが、本文の全群は未確認。
- アダプタのハッシュ処理の実行とプール受理確認。日時・タイムゾーンのホスト関数は未実装で、呼ばれた場合は停止する。
- 約1,000秒の測定、比較図表、既存原稿への実測結果の反映。

## 再開コマンド

```powershell
python experiments/runtime-reference/inventory_inputs.py
python experiments/runtime-reference/reconstruct_reference.py
python experiments/runtime-reference/audit_target_pairing.py
python experiments/runtime-reference/audit_algorithm_contracts.py
python experiments/runtime-reference/check_collector.py
./.tools/runtime-analysis-py312/Scripts/python.exe experiments/runtime-reference/check_comparison.py
node experiments/runtime-reference/check_bridge.cjs
node experiments/runtime-reference/check_client_wire.cjs
python experiments/runtime-reference/record_pool_audit.py
./experiments/runtime-reference/check-proxy-version.ps1
./experiments/runtime-reference/run-readiness.ps1
```

外部採掘の再開コマンドは、接続先と利用者の識別情報が確定していないため未提供。pool-config.example.jsonのaddress=nullでは中継は起動しない。

実測後の比較コマンドは、run-metadata.jsonを持つ実測ディレクトリをrun_id,run_directory,input_sha256,baseline_sha256,program,release,method列のCSVへ記録した上で、以下を使う。この記録時点では、収集を完了した実測がなく、このCSVに記載できる結果はない。

```powershell
./.tools/runtime-analysis-py312/Scripts/python.exe experiments/runtime-reference/compare_reference.py --manifest <実測ラン一覧.csv> --output <新しい比較出力ディレクトリ>
```

serve_mining.pyも、運営元の確認が済んだ対象アルゴリズムのプールと明示的なスレッド数がなければ起動しない。--programで対象を指定し、--operator-confirmed-algorithmは実際に運営元の対応確認が済んだ場合だけ使用する。この記録時点では確認済みプールがない。スレッド数について、元CoinHiveコードの既定はnavigator.hardwareConcurrencyまたは4だが、論文の実際のページ指定は未確認。独自値を元の論文の値とは記載しない。現段階でのclientテストは採掘測定ではない。
# 2026-10-07 22:32 JST：外部プールでの測定を再開

この更新により、利用者の識別情報や、正常にログインできるプールがないとした以前の記録を更新する。利用者から本人の公開された旧形式（legacy）のXKR受取アドレスが提供された。秘密鍵やシードの提供は求めておらず、使用もしていない。`fastpool-user.json`にはFastPoolの`fastpool.xyz:10092`、cn-pico/trtl、運営元とプロジェクトの情報源を記録した。`fastpool-user-login.json`には通常のログイン成功と実際のcn-picoジョブを保存した。ただし、認証に成功しただけで採掘処理が正しいとは判断しない。

実行`cn-pico-normal-binaries-20261007-222952`では、未最適化の通常版cn-pico-trtlモジュール（SHA-256 901261197937a313a98998317eec77029abc1932187c8bbd45359bbc6b1b6d55）を2つのworkerで測定している。この更新時点では、提出した2件のshareが`shares.jsonl`でstatus OKとなり、`proxy.log`にも対応する接続先の受理記録がある。1001件の収集はまだ完了しておらず、性能比較の完了や難読化版の成功は確認していない。ランナーは収集完了時または収集失敗時に、自分が起動したプロセスを停止する。この時点のシェル実行セッションは13444である。収集・分析結果は`results/runtime-mining/runs/<run-id>/`に保存する。

互換性を確保するため、Wasmのバイト列を変えずに次の修正を行った。

- 起動直後のDockerで全体を一度に読むとerrno 12になったが、4096バイトずつ読むと、同じ320988バイトのファイルを取得でき、期待するSHA-256とも一致した。入力と関連ファイルは、サイズを限定したブロックに分けて読むようにした。根本原因を特定したわけではなく、Windowsの保護設定も変更していない。根拠は`cn-pico-input-read-strategies.log`である。
- Windowsのバインドマウント経由ではNodeの依存パッケージを解決できなかった。既存のロックファイルで固定したcoin-hive-stratum 2.6.11の依存パッケージをイメージ内へコピーし、NODE_PATHを設定した。接続の記録処理は実際のProxyのエントリポイントと同じ場所から読み込み、実行中に使われるクラスへ変更を適用する。
- ポインタを受け取るインポート関数`_tzset_js`と`_gmtime_js`は、例外を投げる仮実装から、公式Emscripten 3.1.26ライブラリとデータセットのCコードの`struct tm`に沿った実装へ変更した。公式ソースは`results/runtime-mining/emscripten-3.1.26-library.js`に保存した。
- xmrig-proxy 6.18.0の`Miner::sendJob`はジョブ更新通知にparams.idを含めないが、coin-hive-stratumは通知の振り分けにこの値を必要とする。中継は元の通知を記録し、ローカルで認証済みの単一セッションIDだけを追加する。blob、target、algorithm、height、ジョブIDは変更しない。公式ソースは`results/runtime-mining/xmrig-proxy-6.18.0-Miner.cpp`である。オフラインで通知の振り分けとshareログを確認したが、採掘の成功を示す検査ではない。
- 使用しないローカルTLS証明書の生成を明示的に無効にした。選んだ公開プールのポートは、暗号化しないStratumを使用する。proxyの寄付設定は0とし、明示した単一の接続先を使う。ローカルサービスはすべてループバックで待ち受ける。中継のログに加え、実際のproxyログも保存する。

以前の失敗した実行ディレクトリは、途中までのカウンタ値や拒否応答も含めて保持する。これらは1001件の収集を完了した実行ではない。現在のイメージの識別情報は`image-evidence.json`に保存した。以後の起動では、確認済みのイメージIDを指定し、実行メタデータにも記録する。

この通常版の収集が完了したら、`collection.json`、`summary.json`、`shares.jsonl`、`proxy.log`と失敗時の記録を確認してから、対応する変換版を開始する。対象はcn-pico-trtlに限り、このプールで他の9プログラムも動くことは確認していない。通常版と難読化版の比較、図、原稿への結果反映、ローカルでのコンパイルは、この記録時点では未完了である。アカウントの利用枠は使用17%、残り83%だった。

