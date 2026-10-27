# 条件packetの生成・共有・解除

## 変換

入力はWABTでvalidate/disassembleする実`.wasm`。単一定義関数、1個のi32結果、1–16個のi32引数、i32 localのみ。totalな整数演算とselectの直線列を扱う。SSA表現へ変換する際にlocal.set/local.teeと引数の更新を追う。各selectのconditionは、その時点の値を表す式で同定する。構文上のlocal番号だけでは同定しない。

```text
validate source and parse its straight-line instructions
symbolically execute local updates into a shared expression DAG
topologically emit scalar instructions
for each live select(a,b,c):
    if shared and c already has a packet:
        packet = earlier_packet[c]
    otherwise:
        packet = capture(c)
        remember packet for c
    emit force0(packet,a,b) or force1(packet,b,a)
return final scalar result

capture(c):
    try: if c != 0: throw tagT else: throw tagF
    catch_all_ref: return caught exception reference

force0(packet,a,b):
    try: throw_ref packet
    catch tagT: return a
    catch tagF: return b
force1 reverses the two tag interpretations
```

タグpayloadは空。初期案の「値もpacketへ持たせる」方向は採用せず、今回の検証対象は条件のtransportに固定した。実値a,bはconsumer引数として保持する。したがってデータ型・値そのものの不可視化を実現したとは主張しない。元の条件評価はcaptureで明示的に現れる。

## 意味保存条件

captureは返るなら必ず非nullのtagT/tagF参照を返す。再送は参照を消費・変更しない。force0(capture(c),a,b)はselect(a,b,c)と同値で、force1の引数交換でも同じ。条件のSSA式が同じなら再評価結果は同じであり、packet共有は各forceの結果を変えない。元localが途中更新されればSSA式が変わり、別packetになる。

対象命令はtotalで外部副作用がないため、DAG再構成、dead code除去、共通式化による順序・回数の変化は値に影響しない。この限定があるのでmemory、import、既存EH、call、loop、branch、div/remなどのtrap可能な命令、浮動小数点・SIMDは入力として拒否する。メモリ副作用や任意trap順序を保存した一般変換器ではない。

参照生成による資源不足、native stack枯渇、実行時間、デバッグ情報は同値契約に含まない。十分な実行資源の下で値が一致し、内部例外は公開APIに漏れないという条件付き説明。有限試験もSMTのscalarモデル比較も、全変換実装とエンジンの形式証明ではない。

## 適応的解除

方式を知る解析者はBinaryenのprintでバイナリの命令を読み、構造化block/catch/callを記号実行する。関数ごとのsummaryを作り、参照はタグの有限和として表す。型がexnrefだからといって未知整数や未知メモリ全体へ拡大しない。二タグのどちらかという条件を各catchへ伝え、合流点で通常selectに戻す。捕捉対象の探索は構造化ラベルによる。

内部helperの参照仮引数は二タグdomainでsummary化する。呼出し側で実引数が既知のpacketであることを検査し、nullや未知参照を拒否する。exportはi32のみ、importはなし、tagは空payload二種類なのでclosed-worldのdomainが成り立つ。再帰call、未知命令、flow数上限、非空payloadは未対応で明示拒否する。

実装は全envのコピーを含むため、実測解析時間を理想的な線形時間と断言しない。原理上は構成規則ごとの局所summaryが得られ、参照の全生成履歴やidentityを探索する必要がない。全主例で同時に保持するcontrol outcomeは最大2だった。最初のDAG展開不備による遅さは実装の問題として修正した。

## 費用

select数K、異なるcondition式数Uなら、freshはK回、sharedはU回の例外生成。どちらもK回の再送を行う（最適化前の構成からの数）。例外生成削減は解析者の式生成も減らし得る。追加linear memoryは0だが、VM管理heap上の例外オブジェクトの割当て・保持・GC負担がある。RSSはプロセス全体の指標であり、個々のpacketの実byte量は測定していない。
