# 循環する共有演算の研究追補

## Abstract

Wasmの純粋な語演算を入力依存の順序で共有する試作を作り、通常の順序選択VMと比較した。循環版は正答したが、全12条件を公開binaryから直接的な関数合成へ回復でき、通常VMより約33–59%遅かった。既知の循環回路とschedule合成からの独立した新規性は確認できず、主方式には不採用とする。

## Introduction / Motivation

過去の固定順序に基づくfeedbackでは、その順序が回復手順になった。そこで条件によって順序が異なる共有回路を検査した。これは強い新規性を主張する完成論文ではなく、具体的な候補を反証した記録である。

## Related Work

Neiroukh, Edwards, Song (IEEE TCAD2008, DOI 10.1109/TCAD.2008.2003305)の条件別scheduleと合成、Riedel/Bruck (DAC2003)の循環合成が直接近い。[確認した本文と範囲](plan.md)、[追加読解](analysis.md)を参照。既知原理のWasmへの移植だけを発明と数えない。

## Threat Model

方式・binary・data・table・実行器を公開したwhite-box解析。元のsource、生成seed、生成manifestは回復器に渡さない。保護目標は同等な通常の関数合成の回復費用。暗号的な解析不能性は目標にしない。

## Proposed Method / Implementation

二つの関数合成順からpredecessor表と最短共通supersequenceを作る。固定scheduleで状態セルを更新し、関数は型の等しいtableで共有する。順序に関する帰納法により、任意初期セルから正答する。[CLIと疑似コード](README.md)。対象は2–16個の純粋な単引数i32関数を持つ限定Wasm profile。

## Evaluation

3fixture、主30条件、126,000通常呼出し、12,288任意初期状態probeで不一致0。96 helper同値SMT検査、24記号合成順、30 byte再現、WABT120呼出しを確認。方式既知の回復は12/12成功。O3回復6本は各元版とbyte一致した。

性能45fresh process・315batchでは循環版が元版の約7.83–8.23倍、通常VMの約1.33–1.59倍の時間を要した。通常VMより10–26bytes小さいが元版より大きい。[実測表とログ](../../results/invention-20261022/conditional-causality-report-v1/comparison.md)。

## Discussion / Limitations

語の和グラフに循環があっても、公開条件ごとの依存chainは容易に回復できる。今回の小さなサイズ効果は、独立した新規性や実用的な解析負担を支持しない。3つの合成fixture・1ホスト・限定ABIの結果であり、任意のWasm、複雑な条件計算、一般の循環回路へ結論を外挿しない。全Wasm実装の形式的同値証明や人的解析時間の評価は未実施。

## Conclusion

動作する変換と解除・費用評価を保存したが、新しい難読化発明の確立には至らなかった。条件数やscheduleのみの変更を独立発明として追加する方針は取らない。
