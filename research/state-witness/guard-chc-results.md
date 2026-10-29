# 汎用CHC/Spacerとの具体状態比較

2026-10-24。[事前計画](guard-chc-plan.md)、[実装](guard-chc.py)、[Whiskのソース比較](whisk-review.md)。ここで実行したのは自作の標準的CHC符号化をZ3 Spacer4.13.3へ渡す比較であり、Whisk/WasmVerifierの著者実装を実行したものではない。

## 課題

同じ具体初期storeと左右segment寿命から、選んだ観測契約で異なるAPI列が存在するかを解く。左右寿命のBoolean vectorと左右cellの整数vectorを関係Stateの引数にする。各APIの効果は、条件合成器のcopy写像を使わず、別のBoolean/array式から作った。観測差ならBadへ、差なしなら継続可能なときだけ次状態へ送る。SATは反例存在、UNSATはこのmodelでの不存在である。任意初期storeの一致条件や最短反例はこのbaselineの出力ではない。

## 実測

|run|SAT|UNSAT|footprintで除外|timeout/unknown/error|
|---|---:|---:|---:|---:|
|[reenter 初回](../../results/state-witness/guard-chc-reenter-v1/results.json)|18|48|12|0|
|[terminal 初回](../../results/state-witness/guard-chc-terminal-v1/results.json)|11|55|12|0|
|[reenter 除外分追試](../../results/state-witness/guard-chc-reenter-wide-v1/results.json)|3|9|0|0|
|[terminal 除外分追試](../../results/state-witness/guard-chc-terminal-wide-v1/results.json)|2|10|0|0|

初回は32cellまで。全132受理queryが判定できた後、除外された24queryだけを64cell上限で追加した。query予算5秒は変更していない。追試の二つのprocessは並行実行したため、時間値を単独実行の性能比較へ使わない。全156queryがKの分類と一致した。これは78初期storeを二つのprotocolで調べた結果で、156独立programではない。

各queryの`.smt2`を保存した。SAT/UNSATと最も深い受理public反例から選んだ[5 queryの再parse](../../results/state-witness/guard-chc-replay-v1/results.json)も同じ答えだった。再parseはencoderを通さず保存したSMTを直接読む。SMT命題とWasmの関係は共有parser/限定modelに依存しており、公式意味論からの機械化証明ではない。

## 新規性への反証

この集合について「Kだけが解ける」「既存の汎用モデル検査は失敗する」という主張は支持されない。Spacerも全て解けた。Kの対象差候補は、共通初期storeの条件を等式として自動生成し、不成立時にはその契約で最短のAPI列を返す限定手法である。それ自体も既知のWP・等式抽象・反例抽出に基づき、独立した新しい一般原理を主張できない。実行時間は一回の診断値であり、ここから一般的な速度優位を結論しない。

```powershell
python research/state-witness/guard-chc.py results/state-witness/guard-contract-v1 results/state-witness/local-chc-reenter
python research/state-witness/guard-chc.py results/state-witness/guard-protocol-v1 results/state-witness/local-chc-terminal
python research/state-witness/guard-chc.py results/state-witness/guard-contract-v1 results/state-witness/local-chc-wide --max-cells 64 --only-unsupported results/state-witness/local-chc-reenter/results.json
python research/state-witness/guard-chc-replay.py results/state-witness/local-chc-replay results/state-witness/local-chc-reenter results/state-witness/local-chc-terminal
```
