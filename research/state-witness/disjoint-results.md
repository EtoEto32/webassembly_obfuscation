# moduleを分けた分類範囲の評価

2026-10-24。[実行前の範囲・後続計画](disjoint-plan.md)。解析器のhashを固定し、cut開発に使った14元moduleを除いて測った。

## 結果

対象は公式test由来45 module、非空passive segmentごとにfresh/dropを対にした67状態対。SHA-256で異なるbinaryは39本、binary hashとsegment indexを組にすると61状態対だった。同じテストファイル内の重複と、同一moduleの複数segmentを独立した不具合に数えない。

|方法|全67状態対|重複除去後61状態対|
|---|---:|---:|
|元WASTのAPI列で反例あり|14|14|
|保守的なdef-useの十分条件|24|24|
|上記二つでも保留|29|23|
|有限APIモデルで同じ観測|41|41|
|有限APIモデルで反例|14|14|
|有限APIモデルの対象外|12|6|

各方法の行は重なっており、合計する表ではない。保留29の理由はread-before-dropが17、loopが6、call_indirectが6。固定済み有限モデルは最初の17も同一観測へ分類した。規則をこの結果に合わせて拡張していない。

[Nodeで元API列を実行](../../results/state-witness/disjoint-v1/results.json)し、合計1,314呼出し・commandスキップ0だった。[Wasmtime](../../results/state-witness/disjoint-cross-v1/results.json)で返却値/成功/trapの全列が一致した。この追試は全memory/table identityの再検査とは区別する。

[有限モデル](../../results/state-witness/disjoint-closure-v1/results.json)も[独立Wasmtime host](../../results/state-witness/disjoint-closure-cross-v2/results.json)で再構成し、全対象のedgeと分類が一致した。table参照は、この受理集合で構文確認した相異なるi32定数を返す関数に限って照合した。任意のfuncref同値をWasmtimeで解いた結果ではない。追試初回は差の種類の列挙順序だけで比較が失敗したため、集合を両側でsortするよう修正し、[失敗記録](../../results/state-witness/disjoint-closure-cross-v1/failure.json)を保存した。

## 意味と限界

Kの状態観測は67対すべての寿命差を識別した。しかし関数exportの結果列を観測契約にすると、その差が必ずAPI相違につながるわけではなかった。有限profileの41対では状態対の遷移閉包を確認した。これは全state復元契約の不一致を取り消すものではない。

今回は**人工的にdrop差を入れた感度・分類範囲の実験**で、67個の実製品bugを発見したわけではない。元WASTのAPI列で証拠を見つけられなかっただけのものは保留し、静的条件や有限モデルが受理したものと混ぜない。未対応12対も失敗や正常へ換算しない。

開発用moduleとは分けたが、この公式corpusは以前のinstrumentation検査で既に使っている。完全に未知の独立test setとは呼ばない。規則を固定した適用範囲の確認であり、実アプリでの汎化性能や既存fuzzerへの優越を示していない。

## 再現

```powershell
python research/state-witness/disjoint.py results/state-witness/spec-v4 results/state-witness/cut-inputs-v1 results/state-witness/local-disjoint
python research/state-witness/disjoint-cross.py results/state-witness/local-disjoint results/state-witness/local-disjoint-cross
python research/state-witness/disjoint-closure.py results/state-witness/spec-v4 results/state-witness/local-disjoint results/state-witness/local-disjoint-closure
python research/state-witness/disjoint-closure-cross.py results/state-witness/spec-v4 results/state-witness/local-disjoint results/state-witness/local-disjoint-closure results/state-witness/local-disjoint-closure-cross
```

出力先は新しいdirectoryを使う。closure生成器は元の分類実験に保存した解析器hashと現行解析器が一致することを検査する。
