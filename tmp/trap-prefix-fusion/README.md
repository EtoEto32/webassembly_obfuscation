# トラップ前のメモリ状態を保存する書き込み統合：正しさ試験

2026-10-12。新規性・解析耐性をまだ認めていない具体候補の試作記録。CSEC用論文とは別の研究。

## 今回進めたこと

直線SSA形式の小さな入力IRを、通常版・明示的検査版・遅延逐次commit版・遅延byte統合版へ変換する生成器を実装した。Wasmの任意バイナリを読み取る変換器ではないが、単一の決め打ち関数を手書きしたものでもなく、保存したprograms.jsonの各演算を規則に従って変換する。

意味保存の規則、範囲、事前の検証条件、既存研究との比較はprotocol.md。今回の実装はbyte統合が動くかを確認する段階であり、演算全体の融合や難読化の完成を報告しない。

## 実行結果

最新版experiment.cjsはartifacts-v2へ結果を書く。

- 13プログラム、4変換条件、raw/O2の2条件、計104本のWasm。
- 各224入力、計23,296実行。
- 正常終了9,600実行、trap13,696実行。
- 独立したBigInt・DataViewによる元IR解釈器と比較し、返り値、trapの種類（ゼロ除算/メモリ範囲外）、64KiBの全memoryで不一致0。

入力はアドレスの上下境界、非整列、部分的・完全な別名、ゼロ除算、複数faultを含む。先行storeで後の除数が変わる例に加え、先行storeからloadした値を後のstoreのアドレスにする例も確認した。後者は224件中12件が正常終了、212件がtrapした。正常・異常のいずれも比較対象に含めている。

初版は12プログラム・96本・21,504実行（trap12,000）で不一致0。そのコードをexperiment-v1.cjs、データをartifactsに保存した。v2はアドレスのforwarding例を追加し、各版で使用しないhelper関数を出力しないようにした。旧データを上書きしていない。v1/v2の重複試験を独立標本として合算して成果数を増やさない。

## 何を保存したか

対象は固定1ページの非共有memory、i32加算・乗算・XOR、unsigned除算、load32/store32（offset=0）、有限の直線領域。各storeをlocalのログへ保留し、loadには先行する有効storeをbyte単位でforwardする。最初のfault以降のstoreは無効になる。末尾で最後の有効writerのbyteだけをcommitし、faultがあれば元の不正operandを使って同じ種類のtrapを発生させる。

最初のfault以前のload値が一致すること、有効ログが元の実行prefixと一致すること、アドレスごとの最後のwriterだけで最終memoryが決まることが、意味保存の説明である。今回の有限試験はこの説明を実装が満たすかを検査したもので、任意のプログラムの形式的証明ではない。

import、共有memory、atomics、memory.grow、公開global、ループ・分岐・呼出しをこの試作は扱わない。途中の外部観測を許す環境では、そのままcommitを延期してはいけない。JavaScript例外のスタックトレースやPC、実行時間は保存しない。

## 新規性と有効性の現状

**採用判断は保留。正しさの一致だけでは新規性も難読化の強度も示さない。**

既知の投機実行・store buffer・例外延期と強い類似がある。BOSHの例外tagを使う制御変換とも比較が必要。Constantineにはdecoy経路の除算対策があるが、確認した記載では元のプログラムをerror-freeとしており、今回の正規のtrap前memory保存と同じ前提ではない。この違いだけで新しいアルゴリズムだとは判断しない。

特に、物理store列を変えても、localに保持したログやfault依存から元の効果が読める可能性が残る。これを確かめることが次の採用・不採用の判断である。先行storeを完全に上書きする冗長なコードが消えたことだけを、難読化の成功に数えない。通常のstore最適化で得られる差と区別する。

## 未完了事項と次の順序

1. Sentinel scheduling等の一次本文で、投機store・例外順序・commit規則を確認する。これらと同一の規則なら、今回の試作は意味保存実装として保存し、新規難読化としては棄却する。
2. 差が残る場合は、バイナリ内のログ・forwarding・commit依存を復元する解析を定義し、変換器の対応表を与えずに試す。観測対象の自動同定をしていないのに一般自動解除と報告しない。
3. 解析上の差が支持されて初めて、四条件の反復性能測定と規模拡大へ進む。今は性能・解析成功率を未測定。bytesは生成物の記録として残すが、効率や耐性の結論は出さない。

## 再現とファイル

Nodeでexperiment.cjsを実行する。保存済みのartifacts-v2を保つには、候補ディレクトリを別名へコピーしてから実行する。WASM_TOOLS_ROOT省略時は既存workspaceの.toolsを読み取り利用。Node v24.15.0、V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133。seed 0x3189defa。

- artifacts-v2/results.json: 104本のSHA-256、版、入力数、成功/異常数。
- artifacts-v2/programs.json: 13件の入力IR。
- artifacts-v2/inputs.json: 全入力とパラメータの対応。
- artifacts-v2/initial-memory.bin: 共通の初期memory。
- artifacts-v2/*.expected.json: 独立解釈器の出力、fault位置、最終memory SHA-256。
- artifacts-v2/*.observations.json: 各Wasmの実際の出力・trap種類・最終memory SHA-256。
- artifacts-v2/*.wat / *.wasm: 実行対象。

実行時にはhashだけでなく、64KiBの全byte列も直接比較している。元のCSEC原稿・実験は変更していない。研究目標は未完了。
