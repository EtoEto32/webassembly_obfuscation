# 難読化機構に基づくWasm解析支援の予備実験報告

2026-10-10。最終版の予備実験報告。静的比較、局所テスト、前処理時間の測定、固定検知器による比較を行った。加えて、新たに23バイナリを各6回、計138ブロック測定するハッシュ計算実験を完了し、全記録の監査でも問題がないことを確認した。単純変換は基準版と同じバイト列に戻せたが、一貫した速度向上や検知の改善は確認できなかった。今回の作業には論文・PDF・エディタの変更、申込・投稿・外部公開を含めない。

## 1. RQ1・RQ2から今回の実験へのつながり

RQ1では、公開されている採掘用Wasmの難読化の仕組みと適用箇所を確認し、通常の暗号処理と研究用の計測コードを区別する。RQ2では、対応するファイルのハッシュ出力、速度、命令数、サイズを比較する。以前のローカル環境での反復評価は、Proof-of-Theftの配布物10件、SWAMPEDの入力1件、今回生成した2件の計13バイナリを対象とした。この保存結果は、新しい対策実験の実測値として流用しない。

既存の結果には、静的な命令数の増加と速度低下の順序が一致しない例や、変換された箇所が測定入力では実行されない例があった。同じ条件のSWAMPED変換でも、速度差と測定値の変動が重なる例があった。そこで今回は、確認済みの変換を整理し、元の処理との対応を調べたときに、構造・出力・速度・解析上の扱いがどう変わるかを検証する。研究の主題を対策だけに置き換えるものではない。

仕組み・処理の流れ・適用条件・既存手法との関係は[手法の原理と仕組み](C:/Users/ettotto/Documents/webassembly_obfuscation/docs/countermeasure-method-principles.md)に記載した。元のRQ1/RQ2の根拠を確認する資料は[実測との対応表](C:/Users/ettotto/Documents/webassembly_obfuscation/results/runtime-mining/cross-dataset/rq1-rq2-runtime-evidence.json)、[根拠一覧](C:/Users/ettotto/Documents/webassembly_obfuscation/results/runtime-mining/cross-dataset/current-evidence-index.json)、[先行評価の比較](C:/Users/ettotto/Documents/webassembly_obfuscation/results/runtime-mining/cross-dataset/prior-work/evaluation-comparison.csv)である。これらの旧資料にある許可待ち・未実施の状態は記録時点の履歴であり、現在の状態と区別する。

## 2. 比較条件・対象・出自

未処理、NOP除去のみ、整数定数式の畳み込みのみ、両規則の併用、Binaryen局所pass、Binaryen O2の6条件を比較する。基準版にも同じ処理を適用し、一般的な最適化による変化と難読化を除去した効果を区別する。

| 群 | 対象と役割 | 条件数 | 解釈 |
|---|---|---:|---|
| 開発 | SWAMPED入力の基準・NOP挿入・整数定数分割 | 3入力×6=18 | 規則と機構の確認に使用 |
| 別プログラム等 | 通常・計測・平坦化・命令置換を含む12入力 | 12×6=72 | 適用範囲と通常処理への影響を確認。xmrは既存解析済みで完全な未見標本ではない |
| 別の乱数・変換量 | 同じ入力の基準と、2シード×2割合×2変換 | 9×6=54 | 規則を凍結して位置・量の変化を確認。別実装ではない |
| 整数式の適用 | Cryptic Bytesの10プログラム×3設定×2ビルド | 60 | 評価対象を事前固定。局所式の識別範囲を確認 |

静的比較は合計144条件である。このうち、各入力に専用規則を適用する3条件は計72条件となる。新しい採掘ハッシュ実験では、開発18条件と別乱数54条件の計72条件を、SHAが異なる23種類のバイナリにまとめて測定した。同じバイト列に付いた複数のラベルには同じ6回の測定値を対応付け、72種類の独立したバイナリとしては数えない。通常標本や別プログラムの静的評価は、今回のプログラム全体のハッシュ測定には含まれない。

元の入力のSHA-256は `046dc081076d9cea6831967619b862cc80fa8c2381346406ec639c899cda640f` である。生成方法・調整内容・乱数・変換位置は[開発対の出自](C:/Users/ettotto/Documents/webassembly_obfuscation/results/runtime-mining/cross-dataset/swamped/controlled-pair-manifest.json)と[別乱数の生成記録](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/seeded-normalization/generation.json)に記録した。23種類のSHAと72条件の対応、入力、順序は[固定測定計画](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-preparation/plan.json)に記載した。収集した標本と研究者が生成した変換版を区別し、比較できる既知の基準がない収集標本を「復元できた」とは扱わない。

## 3. 局所正規化の結果

専用規則では、基準版、ファイルSHA、関数番号、変換位置ログを判定に使わない。変更対象は、関数内の独立したNOPと、副作用のない連続した整数定数式に限る。浮動小数点、除算、シフトを含む式や、分岐・呼出し・メモリ操作を挟む式は変更しない。

| 開発入力 | 未処理サイズ（byte） | 未処理命令数 | 両規則後 |
|---|---:|---:|---|
| 基準版 | 74,099 | 31,783 | 基準と同じバイト列 |
| NOP挿入版 | 77,189 | 34,872 | 基準と同じバイト列 |
| 整数定数分割版 | 75,878 | 32,867 | 基準と同じバイト列 |

別の乱数を使い、変換割合を0.05／0.25とした8変換版も、両規則の適用後は基準版と同じバイト列になった。自作の整数テスト912関数では、局所規則に有限個の入力を与えた照合に合格した。ただし、これをすべての入力・モジュールで意味が保たれることの証明とはしない。

定数分割版はBinaryenでも、同じ処理を施した基準版と一致した。最適化したNOP版に残った差は、NOPの残存ではなく他の命令の違いだった。したがって、専用規則が一般的に優れているとも、既存最適化がNOPの除去に失敗したとも結論できない。

別標本のうち、A-Star・CreaturePackの通常版と計測版の計4件は、専用規則で変更されなかった。一方、通常のbase64-cli・seqtkにある定数式には規則を適用できた。規則を適用できたことを、難読化や悪性の判定根拠にはしない。平坦化版やxmrの複雑な命令置換版と基準版の大きな差は局所規則では残り、一般的な難読化の解除に適用できる条件は確認できなかった。

専用規則を適用した72条件で関数署名、メモリ・テーブルの型と上下限、globalの型と可変性が保持された。Wasm検証・型保持は、初期値、テーブル内容、ホストの全動作の同一性まで保証しない。O2でimportが減る条件は専用規則と別に記録した。

根拠：[開発比較](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/local-normalization/static-comparison.json)、[別標本比較](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/transfer/comparison.json)、[別乱数比較](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/seeded-normalization/comparison.json)、[局所テスト](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/local-normalization/synthetic-tests/result.json)、[署名監査](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/interface-signature-audit.json)、[リソース宣言監査](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/interface-resource-audit.json)。条件別events/WAT/Wasmに適用箇所・差分を保存した。

## 4. 複雑な式・平坦化への切替

局所正規化では変数を含む複雑な置換を扱えなかったため、コードを書き換えずに式を比較する方法を追加した。独立変数1個の各ビットをBoolean変数とする多項式を用い、左シフトと恒等的に一致するかを調べる。分岐・メモリ操作・呼出しを越えて依存関係を伝播させず、12～80ノードで展開上限内に収まる式だけを扱う。

xmrの仕組みを確認した標本で43件、Cryptic Bytesの未最適化LLVM版10件で140件の式を出力した。計183式に有限個の入力、計19,398件を与え、独立した整数評価器で結果の一致を確認した。複数の入力に依存するTigressの候補5,018件は対象外だった。最適化後に識別された式が0件でも、難読化が完全に除去されたとはいえない。短い式への変化、依存関係の表現の変化、未対応条件の切り分けはまだ済んでいない。この方法は式の対応を説明するために採用し、悪性の分類やコードの書き換えには使わない。

式抽出と多項式比較を1回実行した際の保存済みの処理時間は、別の12標本の未処理／O2の計24条件で55.4～1,153.6 ms、Cryptic Bytesの60条件で112.5～976.0 msだった。計時したのはextract(text)の実行だけで、WABTによる検証、逆アセンブル、ファイル書き込みは含まない。前処理時間の反復比較とは計時範囲が異なるため、繰り返し測定したときの安定性や他手法に対する速度上の優位性は示していない。対象Wasmを起動する必要はなく、WABTで取得した線形WATを入力に用いる。

平坦化については、事前に確認したXORの4状態モデルを使い、処理の役割と逐次的なメモリ更新を比較した。通常版と平坦化版から切り出した計4関数について、698ケース・1,396呼出しで、一時スタック32バイトを除くメモリと出力を照合した。一般的な状態値の推定や自動復元は実装していない。特定の標本だけに対応するモデルを難読化解除器として採用せず、限られた範囲で処理の対応を説明するための比較にとどめた。

根拠：[式比較](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/expression-analysis/comparison.json)、[別標本への式比較](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/cryptic-expression-transfer/comparison.json)、[有限個の入力の独立照合](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/expression-analysis/extracted-output-checks.json)、[XORの照合](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/flattening-xor/checks.json)、[状態モデルの照合](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/flattening-xor/state-model-checks.json)。

## 5. 処理時間・検知支援・失われる特徴

前処理時間は6入力×4処理について、1回ウォームアップしてから、順序を変えて各6回測定した。計時範囲には入力読み込み、起動、書き換え／最適化、出力書き込み、WABTによる検証を含む。24条件すべてで出力SHAが一致した。専用処理の中央値は120.1～781.1 ms、局所最適化は36.6～171.7 msで、今回の実装全体では専用処理の方が長かった。規則の計算自体の優劣やハッシュ計算速度を評価したものではない。すべての表と図は[処理時間報告](C:/Users/ettotto/Documents/webassembly_obfuscation/docs/countermeasure-processing-time.md)に掲載した。

MINOSの公開重みを固定し、144条件で静的推論を行った。公開ソースにある0～255と0～1の前処理経路を比較すると、21条件で予測が変わった。専用規則を適用した72条件では、どちらの尺度でも正規化前後でクラスが変わった条件は0件だった。通常コードもMALIGNと予測された。重みの学習時に用いた尺度と訓練データとの重複は未確定のため、一般的な適合率・再現率や検知の改善は主張しない。

専用規則を適用した72条件のうち10条件でNOPがなくなり、NOPの有無を表す特徴が失われた。36条件では命令総数が変わった。分岐・呼出し・メモリ操作の命令数が種類ごとに保たれていても、特徴の比率や制御構造全体が保たれるとは限らない。このため、原本、正規化結果、適用記録を併用する方針とする。分類精度を向上させる完成した手法としては採用しない。

根拠：[固定推論](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/detector-feasibility/normalization-inference.json)、[尺度比較](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/detector-feasibility/scale-sensitivity.json)、[特徴消失](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/feature-loss/comparison.json)。検討したMinerRay・WASim等の原理、依存関係、未実施の理由は[検知器調査](C:/Users/ettotto/Documents/webassembly_obfuscation/docs/countermeasure-detector-feasibility.md)。

## 6. 新しいハッシュ出力・速度実験（完了・監査済み）

教員の許可は、利用者の「許可はとれてる」という回答で確認した。隔離環境には、ネットワークnone、CPU1、メモリ・swap上限1GiB、pids64、非root、rootと入力の読み取り専用化、cap-drop ALL、no-new-privileges、実行上限2時間を実際に設定した。外部プールへの接続、shareの送信、報酬の取得、保護設定の変更は行わない。

実際に記録した環境は、Linux Node v18.20.4、V8 10.2.154.26-node.37、Intel Core i9-11900K、Dockerイメージ `sha256:a05286e66b0f1ca712671db5849229594c92e035bae253362cc8b6d0af4a70b6` である。ホスト処理と初期化時刻を固定し、1ワーカーで公表された5入力を巡回した。3秒以上ウォームアップした後、30秒以上の測定を6回繰り返し、巡回ごとに対象の順序をずらした。計138ブロックについて、完了計算数、実経過時間、最終出力、計測前後の照合結果を保存した。

SHAが異なる23種類すべてで、公表された5入力の期待値との照合、追加した12入力の新規コンテキストでの照合、同じ履歴で再利用したコンテキストでの順方向・逆方向の照合に合格した。全138速度ブロックでも、計測前後の公表入力に対する出力、最後に完了した計算の出力、計数・時間・速度計算の整合性、ウォームアップ、順序、UTCの時間間隔を照合した。実行時間はUTC 13:10:01～14:27:38（日本時間22:10:01～23:27:38）で、終了コードは0、OOMはなかった。正常終了ログ、凍結した入力・runner・host・許可記録のSHA、実際のコンテナ制限を監査してから集計した。追加した12入力は基準版との比較に用いたものであり、公表された期待値と同じく独立して正しさを裏付けるものではない。

### 6.1 開発条件の全比較

| 入力 | 処理 | サイズ（byte） | 命令数 | H/s中央値 | H/s最小～最大 | 同じ処理を施した基準版との中央値比 | 同じ入力の未処理版との中央値比 |
|---|---|---:|---:|---:|---:|---:|---:|
| 基準 | 未処理 | 74,099 | 31,783 | 31.4921 | 26.5502～32.0761 | 1.0000 | 1.0000 |
| 基準 | NOP除去 | 74,099 | 31,783 | 31.4921 | 26.5502～32.0761 | 1.0000 | 1.0000 |
| 基準 | 整数定数式 | 74,099 | 31,783 | 31.4921 | 26.5502～32.0761 | 1.0000 | 1.0000 |
| 基準 | 両規則 | 74,099 | 31,783 | 31.4921 | 26.5502～32.0761 | 1.0000 | 1.0000 |
| 基準 | Binaryen局所 | 70,119 | 31,783 | 31.7428 | 30.9506～32.4039 | 1.0000 | 1.0080 |
| 基準 | Binaryen O2 | 69,503 | 31,461 | 31.3623 | 30.5977～31.7299 | 1.0000 | 0.9959 |
| NOP挿入 | 未処理 | 77,189 | 34,872 | 30.6473 | 30.2297～31.9515 | 0.9732 | 1.0000 |
| NOP挿入 | NOP除去 | 74,099 | 31,783 | 31.4921 | 26.5502～32.0761 | 1.0000 | 1.0276 |
| NOP挿入 | 整数定数式 | 77,189 | 34,872 | 30.6473 | 30.2297～31.9515 | 0.9732 | 1.0000 |
| NOP挿入 | 両規則 | 74,099 | 31,783 | 31.4921 | 26.5502～32.0761 | 1.0000 | 1.0276 |
| NOP挿入 | Binaryen局所 | 78,082 | 35,283 | 31.4089 | 30.6492～32.5579 | 0.9895 | 1.0249 |
| NOP挿入 | Binaryen O2 | 69,505 | 31,462 | 31.0966 | 30.8843～31.5606 | 0.9915 | 1.0147 |
| 整数定数分割 | 未処理 | 75,878 | 32,867 | 31.6732 | 27.8392～32.0292 | 1.0058 | 1.0000 |
| 整数定数分割 | NOP除去 | 75,878 | 32,867 | 31.6732 | 27.8392～32.0292 | 1.0058 | 1.0000 |
| 整数定数分割 | 整数定数式 | 74,099 | 31,783 | 31.4921 | 26.5502～32.0761 | 1.0000 | 0.9943 |
| 整数定数分割 | 両規則 | 74,099 | 31,783 | 31.4921 | 26.5502～32.0761 | 1.0000 | 0.9943 |
| 整数定数分割 | Binaryen局所 | 70,119 | 31,783 | 31.7428 | 30.9506～32.4039 | 1.0000 | 1.0022 |
| 整数定数分割 | Binaryen O2 | 69,503 | 31,461 | 31.3623 | 30.5977～31.7299 | 1.0000 | 0.9902 |

各SHAのバイナリを6回測定した。表の比はそれぞれの中央値から求めたもので、同じ反復内で求めた比の中央値とは異なる。各反復内で求めた比と全72条件の結果は、summary.csvに別列で保存した。同じSHAのラベルには同じ6回の測定値を対応付けている。例えば、両規則を適用したNOP挿入版、整数定数分割版、基準版は同じバイト列になるため、正規化済みの標本をそれぞれ再測定して独立に再現した結果ではない。最小値～最大値の範囲は信頼区間ではない。

### 6.2 別乱数・変換量の未処理版

| 変換・シード・割合 | 命令数 | 命令数／未処理の基準版 | H/s中央値 | H/s最小～最大 | 速度／未処理の基準版 |
|---|---:|---:|---:|---:|---:|
| nop-seed20261011-ratio05 | 33,329 | 1.0486 | 31.5429 | 30.2620～31.7705 | 1.0016 |
| constsplit-seed20261011-ratio05 | 32,329 | 1.0172 | 32.0457 | 29.9914～32.3965 | 1.0176 |
| nop-seed20261011-ratio25 | 39,504 | 1.2429 | 31.4827 | 30.6238～31.9558 | 0.9997 |
| constsplit-seed20261011-ratio25 | 34,473 | 1.0846 | 31.1197 | 27.5313～32.1270 | 0.9882 |
| nop-seed20261012-ratio05 | 33,329 | 1.0486 | 31.6302 | 30.8980～32.4544 | 1.0044 |
| constsplit-seed20261012-ratio05 | 32,329 | 1.0172 | 31.3484 | 30.7519～32.3936 | 0.9954 |
| nop-seed20261012-ratio25 | 39,504 | 1.2429 | 31.6090 | 29.3641～32.2729 | 1.0037 |
| constsplit-seed20261012-ratio25 | 34,473 | 1.0846 | 31.7760 | 31.4904～32.6500 | 1.0090 |

8版すべてで、両規則の適用後は未処理の基準版と同じSHAになった。両規則の適用後の中央値を各版の未処理時の中央値で割った比は0.9827～1.0120で、増加と減少が混在した。Binaryen局所では同じ処理を施した基準版に対する比が0.9897～1.0106、O2では0.9844～1.0065だった。これらは同じ採掘実装の派生版であり、別の実装にも一般化できることを示してはいない。

### 6.3 速度・構造の関係と採用の判断

NOP挿入の開発版では命令数が9.72%増え、未処理時の速度の中央値は基準版の0.9732倍だった。両規則の適用後は、この未処理版に対して1.0276倍となった。一方、整数定数分割版では命令数が3.41%増えたものの、未処理時の速度は基準版の1.0058倍で、両規則の適用後は未処理版の0.9943倍となった。どちらも構造は元に戻ったが、そこから一律に高速化すると結論することはできない。

別の乱数を使ったNOP挿入版のうち、命令数が24.29%増えた2版の速度比は0.9997と1.0037だった。静的な命令数の増加率を、そのまま実行負荷や速度低下率とみなすことはできない。静的命令数は命令の実行回数を表さず、速度の測定結果も今回の入力に対する観測である。JITが生成した機械語、実行されたNOPの数、CPU動作周波数やホスト上の競合がそれぞれ速度に与えた影響は測っていない。

基準版自体の6回の速度は26.5502～32.0761 H/sの範囲にばらついた。変換前後の測定範囲は重なっている。また、同じ巡回内の比も逐次測定から求めたもので、同時刻に測ったペアの比ではない。今回のデータから、一貫した速度向上、統計的同等性、2.76%の確実な高速化は主張しない。基準版にも同じ既存最適化を施すと、定数分割版は同じSHAになり、NOP挿入版には他の命令の差が残った。この差を速度差の原因とは断定できず、専用正規化の優位性は確認できない。

以上から、単純変換に対する局所的な整理は、適用箇所を説明できる解析前処理として限定的に採用する。速度向上や検知手法の完成を理由とする採用はしない。複雑な式にはコードを書き換えない比較を併用し、平坦化は限定したモデルによる説明にとどめる。MINOSの固定モデルでクラスの改善が0件だったこと、前処理時間が増えること、元の特徴が失われることも併せて判断した。

### 6.4 図と監査済みデータ

下図は開発条件の全6反復と中央値を示す。異なるラベルが同じSHAに対応する場合、図中の点も同じ測定値を示す。

![開発条件の反復速度](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-runs/execute-120f528e37424ec6806047c933011eec/analysis/development-rates.png)

下図では、72ラベルの重複を除き、SHAが異なる23種類を1点ずつ表示した。静的なサイズ・命令数の比と速度比に単調な対応は見られない。回帰分析や因果関係の推定は行っていない。

![構造変化と速度比](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-runs/execute-120f528e37424ec6806047c933011eec/analysis/structure-versus-rate.png)

監査済みのデータは、[集計JSON](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-runs/execute-120f528e37424ec6806047c933011eec/summary.json)、[全72条件CSV](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-runs/execute-120f528e37424ec6806047c933011eec/summary.csv)、[構造との結合CSV](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-runs/execute-120f528e37424ec6806047c933011eec/analysis/structure-runtime.csv)、[生の測定記録](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-runs/execute-120f528e37424ec6806047c933011eec/outputs/measurement.json)、[正常終了記録](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-runs/execute-120f528e37424ec6806047c933011eec/completion.json)、[実際の隔離設定](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-runs/execute-120f528e37424ec6806047c933011eec/container-inspect.json)に保存した。図はPNGとSVGで保存した。生成スクリプトは[scripts/report_countermeasure_runtime.py](C:/Users/ettotto/Documents/webassembly_obfuscation/scripts/report_countermeasure_runtime.py)である。

静的処理にはWABT 1.0.42とBinaryen 133を使った。専用規則の実装は凍結したnormalize_wat_local.py（SHA-256 `01af604b04e54026c9b53c5b70e6cb89ee9e8e2424890c28305b5bd62cad58d9`）である。実際に使用したrunner・host・計画・入力・許可記録は、run/inputsとsummary.jsonで照合した。ローカル処理はPython 3.12.14で行った。図の生成時には対象Wasmを起動しない。


初回実行は、32バイトの追加入力を逆順で照合した際に停止し、速度測定は0ブロックだった。失敗した対象は別乱数NOP版に局所最適化を施した版であり、未処理の基準版ではない。その後、基準版だけを診断したところ、1／8／32バイト入力はコンテキストを再利用した履歴によって出力が異なった。一方、新規コンテキストで行った2回の結果は一致した。原因は未特定であり、正規化の誤変換があったとも、通常のCryptoNightにおける短入力の正しい出力が得られたとも断定できない。

追加入力は除外せず、新規コンテキスト同士の比較と、公表入力の履歴・追加入力の順序をそろえた基準版との比較を行うよう修正した。順方向・逆方向それぞれの基準出力を用い、公表入力の独立した期待値は変更しない。初回の失敗ログも残す。追加照合はあくまで基準版との差を確認するものである。

今回の実行記録は[execute-120f528e37424ec6806047c933011eec](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-runs/execute-120f528e37424ec6806047c933011eec)、初回の失敗記録は[execute-d50a31528b9b4608b2de1ba1222ce030](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-runs/execute-d50a31528b9b4608b2de1ba1222ce030)、基準版の診断結果は[input-order-diagnostic.json](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-preparation/input-order-diagnostic.json)に保存した。最新の進捗は[active-measurement.json](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/runtime-preparation/active-measurement.json)で確認できる。

## 7. 現時点の採用判断と主張できる範囲

先行評価の確認範囲では、Cryptic Bytesは100秒のハッシュ計算速度、WebAssembly Diversification for Malware Evasionはプール検証と設定上1000秒の速度を評価している。これらに対して「ハッシュを初めて測った」とは主張しない。SWAMPEDの74ファイルの時間評価は、何もしないimportと各export呼出しを使ったLiftoffの測定であり、今回の期待出力を伴う採掘ハッシュ全体の評価とは条件が異なる。Proof-of-Theftの配布物には速度測定コードがあるため、速度・出力の対応表を確認できなかったことを「過去に実行していない」と読み替えない。各論文の節・一次資料・確認限界は冒頭の先行評価比較表に保存している。

単純変換の局所正規化は、適用箇所を明示できる解析前処理として限定的に採用する。複雑な式には、コードを書き換えない比較を併用する。平坦化を一般的に解除できることや検知の改善は確認できず、限定的な比較と固定モデルによる推論の結果として報告する。定数分割は既存最適化でも整理できるため、その結果を専用手法だけの効果とはしない。

今回得られた知見は、変換の仕組みに応じてコードを整理できる条件と残る差、通常処理にも適用できる規則、複雑な変換を扱うために必要な別の情報、特徴の消失と固定モデルの反応との対応である。さらに、基準版とバイト列が一致し、有限個の入力で出力も一致していても、命令数の削減率に対応する速度向上は得られないことを、同じ処理を施した基準版との比較と反復測定で確認した。未評価の標本を測定したというだけで新規性を主張しない。既存の正規化・MBA簡約・検知器を超えるアルゴリズム上の優位性、実世界の普及率、すべての入力で意味が保たれることも主張しない。

## 8. 残作業と再現用のコード・資料

今回の実装、比較、実際のハッシュ測定、監査、図表作成、分析、説明書・報告書の作成は完了した。採用するのは、単純変換に対する限定的な解析前処理と、コードを書き換えない式比較である。包括的な難読化解除器や検知器が完成したわけではない。今後の課題には、未対応式や状態の自動推定、通常コードの負例に対するプログラム全体の出力確認、JITの確認、人間による独立した機構レビュー、別ランタイムでの外的妥当性の評価がある。新たなハッシュ実行が必要な場合は、今回と同じローカル制限と許可範囲を照合し、別runとして記録する。

作業ルートは `C:/Users/ettotto/Documents/webassembly_obfuscation` である。正常終了後に再解析するコマンドを以下に示す。対象Wasmを起動せず、保存結果だけを処理する。未完了、誤出力、欠測、隔離設定の不一致がある場合は集計を拒否する。

```powershell
& '.\.tools\runtime-analysis-py312\Scripts\python.exe' '.\scripts\report_countermeasure_runtime.py' '.\results\countermeasures\runtime-runs\execute-120f528e37424ec6806047c933011eec'
```

実装・全SHA・ツール設定・生ログ・events・WAT・図表をたどるための資料は[成果物一覧](C:/Users/ettotto/Documents/webassembly_obfuscation/docs/countermeasure-status-and-artifacts.md)。時系列の試行・採用・不採用の判断・方針変更は[実験進捗記録](C:/Users/ettotto/Documents/webassembly_obfuscation/docs/countermeasure-experiment-progress.md)。作業目標の変更に伴い、論文更新を今回の範囲から外した。

個別ファイルの絶対パス・サイズ・SHAは[機械可読の根拠一覧](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/deliverable-evidence-index.json)に、照合結果は[成果物の照合記録](C:/Users/ettotto/Documents/webassembly_obfuscation/results/countermeasures/deliverable-audit.json)に保存する。過去の失敗、模擬テスト、静的解析、今回の実測を分類し、模擬記録を実測に算入しない。説明書・報告書のローカル参照先と、論文3ファイルが目標変更時のSHAから変わっていないことも確認する。

未確認の事項には、すべての入力で意味が保たれること、初期値・テーブル内容を含む全体の監査、通常コードの負例に対するプログラム全体の出力、式解析時間の反復評価、複数入力に依存する式、最適化後に残る差の原因、状態の自動復元、JITの機械語、訓練データとの重複、一般的な検知精度、人間による独立した機構レビューがある。これらは今回の測定範囲外であり、有効な対策が完成したとはいえない。今回の予備比較に必要な実験と報告は完了したが、この限界を隠して研究全体が完結したとは扱わない。
