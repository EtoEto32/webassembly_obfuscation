# 結果と採否

## 判断

resourceの生成・破棄を介した計算移動は動作したが、**生成順と破棄順の分離を主発明として採用する根拠は得られなかった**。Jco/Binaryenの通常の内部core最適化後にもresource操作は残る。しかし、方式を知る解析では公開canon結線とhandle→slot対応を辿るだけで、順列探索なしに元の計算を回復できる。全件回復そのものではなく、追加の解析費用と技術的差が小さい点を採否の根拠とする。

## 正当性

主72条件（3族×8/24/64段×4方式×raw/O3）で318,240呼出し、追加32条件（1/3/13/128段、別payloadと演算順）で141,440呼出し、計459,680呼出しの不一致・trapは0。各条件につき81境界＋1,024 seed固定random入力を用い、元core、回復core、独立したcomponent 2 instanceを整数oracleと照合した。同じ入力が方式間・実装間で繰り返されるため、459,680個の異なる入力を意味しない。

主例の破棄順を誤らせた9負例すべてに不一致がある。非対応のmemory、division、x依存payload、追加export、129段の5例を拒否した。別実行器Binaryen wasm-shellは主例の元/回復core 81本×7入力=567照合を通過。これはcomponent全体を別runtimeで実行した結果ではない。

出力componentはJcoのparse/transpileを通り、内部coreと回復coreはWABTでvalidateした。全入力の機械的同値性証明、任意のresource runtime、外部副作用・再入・資源不足は未検証。

## 性能と解析費用

最終実行測定は[performance-v2](../../results/invention-20261019/resource-trigger-performance-v2/protocol.json)。O3後の36 component条件と元core 9条件、それぞれ3 fresh Node process、計135 process。50,000 warmup、componentは10,000呼出し×9 batch、coreは200,000×9 batch。順序seed 191019、各process中央値の中央値を比較する。process中央値の最大/最小は全条件で最大1.130。初回の短い測定区間は最大1.921だったため置き換え、旧データも保存した。

解析は全72条件×5回。reader（Jco起動・print、埋め込みcore抽出、WABT validation/disassembly、構文解析）と記号実行＋回復WAT生成を分けた。解析器が変わっていないことをSHAで確認し、performance-v1の360記録をv2へ引き継いだ。二重に720回とは数えない。本文生成までを含み、回復バイナリの再compile時間は解析本体へ含めない。

| 比較（O3、9プログラムの範囲） | 実行時間比 | 解析本体時間比 | reader込み解析時間比 |
|---|---:|---:|---:|
| deferred / plain component | 1.058–1.594 | 1.829–3.503 | 1.090–1.309 |
| deferred / direct helper＋buffer | 0.989–1.413 | 1.097–1.293 | 0.933–1.019 |
| deferred / immediate resource | 0.949–1.047 | 0.950–1.086 | 0.961–1.024 |

解析本体の絶対値はdeferredで0.247–1.644ms、readerは297.6–306.5ms。単なるreaderの起動費用を保護強度としない。deferredはdirectより解析本体が約10–29%増える一方、生成順を変えないimmediateに対して追加優位性は確認できない。人間の解析時間・解析器開発時間・汎用逆コンパイラへの効果は測っていない。

plain componentそのものが元coreより約95.5–497倍の時間を要した。JcoのJS側canonical呼出し処理が小さな算術kernelに対して大きい。この数値は短い関数をJSから繰り返し呼ぶ経路に限り、native Component Model runtimeへ一般化できない。componentとの比較だけで実用的な低負荷難読化を達成したとは言えない。WASMixer等の実装との費用を揃えた比較も実施していない。

componentバイナリのdeferred/plainサイズ比は2.288–4.352、deferred/directは1.223–1.283。JS+core配布物の比はそれぞれ1.043–1.051、1.035–1.038で、共通のJco生成JSが多くを占める。内部scratchはplainで0、他方式で64KiB確保・4Nbyte使用。handle生存ピークはimmediate=1、deferred=N（記号モデル値）。deferredのprocess peak RSS中央値は47,772–48,260KiB、GC後heapUsedは4,469,376–4,474,608byte。これらはruntime全体を含み、差分だけを難読化の正味memory量としない。native stack/spillは未測定。

deferred変換は237.6–280.2ms（reader・component生成・parseまで、各例一回測定）、O3後transpileは231.7–252.9ms。最適化時間は各条件のmanifestのopt_msに分けて保存した。単一機・合成プログラム13種という限界がある。[全比較表](../../results/invention-20261019/resource-trigger-report-v3/comparison.md)を参照。

## 失敗をどう扱ったか

v1のreaderはO3がhandleをoperand stackへ残した場合に失敗した。これは型arityに従うstack消費を実装して修正。v2のJco実行経路ではrepのbit30が失われ、74,392不一致を記録。小さなslot番号をrepにし、32bit値を内部bufferへ保存する設計へ1回修正した。通常の関数呼出し対照にも同じbufferを入れた。この失敗を解析耐性にも成功した正当性試験にも数えない。

## 新規性と次の判断

最も近い技術的基盤はresourceの標準destructor semanticsと、既知の計算分割・呼出し境界変更。今回の具体的規則は「独立payloadを保存し、own handleの生成順を変え、drop順で元計算を実行する」ものだが、その差を裏付ける追加保護効果は未確認。検索で同一構成が見つからなかったことは独立新規性の根拠にしない。公報中のdestructor atomを同一技術とも断定しない。

Rejectの最大理由は、明示的なcallback結線と定数slotの対応が一つの記号実行を与え、生成順変更という提案部分をほぼ無費用で除去できること。通常最適化で残ることと、方式既知の解析費用を増すことは別である。今後は、実装前の段階で「公開型・結線をinlineすると既知の単純な状態更新へ戻るか」を早期に検査する。研究全体の独自で有効な難読化・特許候補の確立は未達で、主目標は継続する。
