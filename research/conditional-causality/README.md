# 入力条件によって順序が変わる循環する共有演算

2026-10-22。**主発明には不採用。** 実Wasm変換器と公開binaryだけを読む回復器を作り、正当性・性能・先行技術を比較した。原理が既知のcyclic combinational circuitとschedule合成に近く、回復費用に見合う保護上の効果を示せなかった。研究全体の目標は未達であり、新しい発明数へ加算しない。

[事前計画・文献](plan.md)、[結果と採否](analysis.md)、[論文追補](paper-note.md)、[再開地点](checkpoint.md)。主結果は[比較表](../../results/invention-20261022/conditional-causality-report-v1/comparison.md)と[集計JSON](../../results/invention-20261022/conditional-causality-report-v1/facts.json)。

## 対象とアルゴリズム

入力は実`.wasm`。2–16個の純粋な単引数i32関数と、`run(x:i32,s:i32)->i32`を持つ。runはsの最下位bitで二つの関数合成順を選ぶ。各順序は全関数を1回ずつ使う。関数はadd/sub/mul/and/or/xor/shifts/rotatesと定数・localだけの全域計算。memory、imports、例外、source loop、浮動小数、divisionは非対応として拒否する。一般のC/C++アプリ変換器ではない。

各関数を一つの型の等しいtable entryへ置き、対応するprivate memoryの状態セルを作る。二つの合成順からpredecessor表を生成し、どちらの順も部分列として含む最短共通supersequenceを固定scheduleとする。

```text
orders = parse_two_compositions(source_wasm)
for selector in {0,1}:
    predecessors[selector] = predecessors_of(orders[selector])
schedule = shortest_common_supersequence(orders[0], orders[1])

run(x, selector):
    selector &= 1
    for node in schedule:
        predecessor = predecessors[selector][node]
        argument = x if predecessor == INPUT else state[predecessor]
        state[node] = function_table[node](argument)
    return state[last_node[selector]]
```

語単位の依存グラフは入力条件を合わせると循環する。しかし選んだ順序のprefixがscheduleの部分列として実行された後、そのprefixの状態は正しい。以後それらを再実行しても正しい。従って任意の初期stateから最後の出力が一致する。状態セルの初期化や0へのresetは不要。関数の余分な実行を許すため、全域・副作用なしが必須である。

private memoryは固定1page、tableはn要素。追加リソースの確保失敗・実行時間・資源制限を含む任意のホスト文脈での同値性は主張しない。呼出し中のホストcallback、再入、並行呼出しはこの閉じたprofileに存在しない。

## 攻撃モデルと回復

解析者は方式、全binary、実行器を知り、改変・計測を行える。生成seed、元Wasm、生成manifest、元の合成順は回復器に与えない。保護目標は、循環する実行器から元と同等な通常の関数合成へ戻すための費用である。暗号化や秘密鍵による保護は使わない。

回復器は公開dataとtable上の実関数を読み、既知の実行器を再生成する。rawまたはO3のbyte一致を要求し、dataだけが同じ別コードを拒否する。条件ごとにpredecessor表を終点から辿り、全関数を一度ずつ含む非循環chainであることと、固定scheduleに含まれることを確認し、通常のif/callへ戻す。任意のWasmを扱う汎用逆コンパイラではない。

## 実行と再現

Python3.9、Node24.15.0/V8 13.6、WABT1.0.42、Binaryen133、Windows x64。監査だけZ3 solver4.13.3（distribution z3-solver4.13.3.0）を用いる。既存の`.tools/encoding-synthesis-python`を`audit.py`が読み込む。変換・回復は標準Pythonのみ。WABT/Binaryenは`.tools/`に配置し、親pathは`WASM_TOOLS_ROOT`で変更可能。

全commandはrepository rootで、未存在の出力先を使う。

```powershell
python -X utf8 research/conditional-causality/prototype.py transform input.wasm protected.wasm
python -X utf8 research/conditional-causality/prototype.py transform input.wasm ordered.wasm --mode ordered
python -X utf8 research/conditional-causality/prototype.py recover protected.wasm recovered.wasm

python -X utf8 research/conditional-causality/run.py results/causal-new/main
python -X utf8 research/conditional-causality/performance.py results/causal-new/main results/causal-new/performance
python -X utf8 research/conditional-causality/audit.py results/causal-new/main results/causal-new/performance results/causal-new/audit
python -X utf8 research/conditional-causality/report.py results/causal-new/main results/causal-new/performance results/causal-new/audit results/causal-new/report
```

`run.py`は入力fixtureと原版を生成し、30主条件、診断版12本、負の対照を検査する。source snapshots、hash、raw/O3、回復binary、ログを保存する。`performance.py`は同じhelper・predecessor表を持つ通常の順序選択VMを対照にする。性能測定中に重い監査を並列実行しない。

## 確認したこと

- 主30条件（異なるbinary21本）、通常126,000呼出し、任意初期状態probe12,288呼出し、不一致0。
- 12/12保護条件を回復。96個の32bit helper同値SMT検査は全てunsat、24条件の任意初期値に対する記号的な合成順一致を確認。これらは同じ24個のhelperを条件別に検査した数で、96個の独立benchmarkではない。
- 主30本のbyte再生成一致、別WABTの120呼出し一致。短すぎるschedule3件は実行不一致となり回復器も拒否。dataを保って実行器を変更した3件と、trapし得るhelper1件も拒否。
- O3の循環版は元版の約7.83–8.23倍、通常VMの約1.33–1.59倍の実行時間。元版は極小カーネルでありアプリ全体の倍率ではない。
- 循環版は通常VMより10–26bytes小さいが元版より大きい。回復後O3の6本は各元版O3とbyte一致。復元の人的開発費用は未測定。

「循環を含むので解析困難」とは結論できない。今回の2条件への分解は公開表から容易で、一般の循環回路の困難性をこの生成物へ移す根拠がなかった。
