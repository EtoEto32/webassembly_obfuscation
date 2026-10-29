# 状態付き切替グラフの全体合成とWasm実験

2026-10-23。前候補の残差補正から原理を変え、元の演算DAGを直接埋め込まず、関数の入出力から状態付き切替グラフを合成した。実Wasm変換、直接命令化、反復削減、公開binaryのみの回復まで実装した。**今回の限定方式は主特許候補に不採用。** 既知rotor-routingと有限仕様合成を超える新規性は未確立で、最良版も安く回復できる。

- [実験前の仮説](plan.md)、[先行技術の読了範囲](prior-art.md)
- [比較表・保存証拠](../../results/invention-20261023/rotor-synthesis-report-v1/report.md)

## 生成規則と意味保存

各switchは二つの後続と1bitの方向状態を持つ。tokenは現在の方向へ進み、使ったswitchのbitを反転する。入力bitを最初のn switchの初期値、他のswitchを0とし、頂点0から出発する。sink0/1が出力bitである。

```
truth = evaluate_every_Boolean_input(source_expression)
unknowns = two_successors_per_switch
for each input x:
  pc = 0; rotor = x
  unroll B steps of move-then-toggle
  constrain pc == sink(truth[x])
constrain each switch is visited by some input
solve; reject unsat or unknown
check every input with a separate concrete simulator
lower graph to Wasm
```

Wasmではi32の32 bitを独立laneとし、各頂点にtoken所在maskを持つ。次の所在をA_v AND NOT R_v、A_v AND R_vへ分け、後続maskへORし、R_vをR_v XOR A_vへ変える。各laneに常にtokenは1個で、二つのmaskは互いに素。sinkは吸収点として保持する。したがって各laneのWasm更新はBooleanモデルの1stepに対応し、B時点の終点が元式のbitと一致する。lane間の加算carry・rotateを含む入力は対応しない。対象は1〜3個のi32引数、単一run、AND/OR/XOR、0/-1定数のpure式。import、元memory、trap、一般CFGは未対応。資源枯渇と実行時間を保存する意味の同値性ではない。

合成はZ3で全Boolean入力を展開して行う。探索の失敗は保護成功ではない。最初のxor3、5switch、10stepではInt版が20秒timeout、BitVec版が同じ制約で約14.64秒UNSAT。これはこの有限制約内での結果で、任意サイズでのXOR不可能性を証明しない。主試験はxor3をand3へ変更したand3/majority3/mux3、4switch、10step。and3だけに構造上のringを追加制約としたので、関数間の解析費用差からring効果を比較しない。三つともSAT。

補助全数検査は2入力、3switch、1個の0初期補助switch、origin0、sink2個に限定。全15,625グラフのうち2,071は少なくとも一つの入力で停止せず、停止するものは14種類の真理値表を実現した（XOR/XNORなし）。状態数24を超える追跡での非停止は決定的状態の反復から判断できる。この有限分類を一般定理と表現しない。

## 実装段階と攻撃

1. rotor：公開の後続表を読む共通Wasm評価器。1ページの私有memory。
2. native：同じグラフをlocalとbitwise命令へ直接下ろす。metadata・後続表・memoryはない。
3. tight：nativeの反復上限を全Boolean入力の最大到達回数へ削減。今回5/8/5回。

これらは同一候補の改善とアブレーションで、独立した3発明ではない。nativeは共通評価器の費用で不当に棄却しないための対照でもある。

rotor回復はbinaryから後続表を読むが、raw/O3評価器のbyte再生成照合を必須にする。真理値表の全8入力追跡と、入力を列挙しないBDD記号追跡の両方で回復した。native/tightは実際のWasm命令を読んで、local代入と定数回loopをBDDで記号実行する。source、graph、合成時metadataを受け取らない。laneを混ぜるrotate、任意bitmask、記号値の加算を拒否する。対応外を解析成功/失敗と混同しない。

## 主結果

|検査|実測|
|---|---|
|共通評価器と未変換・回復版|24binary、115,992呼出し、不一致0|
|直接命令化・上限削減と回復版|24binary、115,992呼出し、不一致0|
|共通評価器の別BDD回復版|6binary、28,998呼出し、不一致0|
|公開binary回復|rotor6/6、native/tight12/12。追加BDDも同じrotor6/6|
|byte一致再生成|rotor6本、native/tight12本|
|別実行器WABT|rotor24、native/tight48呼出しが独立JS相当式と一致|
|拒否対照|短すぎる上限2解析、偽造評価器1、lane前提違反3を拒否|

各binaryの4,833入力は729境界組、8Boolean組、4,096乱数で、重複を含む。同じ入力を方式間で再使用し、呼出し数を独立入力数として合算しない。WABTのnative検査は1 wordに8Boolean組全てを詰めた入力も含む。有限テストは全変換器・実行器の形式証明ではない。

同時期の45process測定で、未変換/rotor/native/tightはand3で1.046/96.401/12.272/6.330ns、majority3で1.167/97.306/14.186/11.010ns、mux3で1.108/95.778/10.255/6.009ns。tightは元の約5.4〜9.4倍。O3 sizeは未変換45/54/51bytes、tight183/179/190bytes。tightの追加linear memoryは0。メモリ割当削減・高速化は確認したが、O3のtightを実際の命令から0.464〜0.714msで回復できる（読取り・コンパイルを除く単回値）。

測定は共通Wasm wrapper、入力更新とloop込み、ウォームアップ16,384回、20ms校正、3fresh process×7batch、固定seedで順序を混ぜた。全315batchが10ms以上。V8のLiftoff/lazy compilationを無効化し、coreのO3後にwrapperを足して二度目の全体最適化はしない。相関するLCG/rotate入力であり独立一様入力ではない。RSSはNode全体。CPU・エンジン一組の小例で、実アプリや同費用の商用製品との優劣は未検証。

## 不採用理由

全体合成で元のgate割当を消しても、終点を短い上限で計算できることが解析側の記号実行にも使える。今回の規模ではBDDが小さく、直接命令化して表を消しても簡潔な等価式へ戻った。既知のrotor計算と一般のSMT合成の組合せ以上の技術的差も未確立。一般ARRIVALの計算量、循環の存在、最適化後にloopが残ることだけで解析耐性を主張しない。

## 再現

Python3.9、Node24.15/V8 13.6.233.17-node.48、WABT1.0.42、Binaryen133、Z3 4.13.3。Windows x64、Core i9-11900K。`.tools/encoding-synthesis-python`にz3-solver、`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`にツールが必要。後二つの親配置はWASM_TOOLS_ROOTで変更可能。共通のWAT readerとBDDはresearch/connectivity-elimination、性能wrapperはresearch/span-maskから使う。

```powershell
python -X utf8 research/rotor-synthesis/run.py results/rotor-main
python -X utf8 research/rotor-synthesis/audit.py results/rotor-main results/rotor-audit
python -X utf8 research/rotor-synthesis/native-run.py results/rotor-main results/rotor-native
python -X utf8 research/rotor-synthesis/native-audit.py results/rotor-main results/rotor-native results/rotor-native-audit
python -X utf8 research/rotor-synthesis/performance.py results/rotor-native results/rotor-runtime plain rotor native tight recovered
python -X utf8 research/rotor-synthesis/enumerate.py results/rotor-enumeration
python -X utf8 research/rotor-synthesis/prototype.py transform input.wasm rotor.wasm --nodes 4 --bound 10
python -X utf8 research/rotor-synthesis/native.py lower rotor.wasm native.wasm --tight
python -X utf8 research/rotor-synthesis/native.py recover native.wasm recovered.wasm
```

新しい出力先を指定する。SMT solver版変更によるgraph選択の一致は保証しないが、保存graphからの18binaryのbyte再現は監査した。push・外部公開・出願は行っていない。研究全体は継続中。
