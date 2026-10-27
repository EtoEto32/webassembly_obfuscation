# 値から配置を決めるメモリ表現と差分移送

2026-10-22。**同じ動的表現の全体復号方式に対する約12～19%の実行時間削減を確認した。独立した新規難読化としての優位は未確立で、主発明には採用しない。**

4語の値から回転に不変な統計量を求め、その値でフィールドの保存位置を決める。配置表を別に保持せず、更新した語の統計量の差分だけブロックを回転する。回転に不変な統計量から、解析者も配置を安く復元できることが限界だった。暗号的な秘匿や解析不能性を目標にしていない。

- [事前計画](plan.md)、[算法・疑似コード・意味保存・攻撃](algorithm.md)、[先行研究との対応](prior-art.md)
- [実測集計](../../results/invention-20261022/invariant-layout-report-v1/report.md)、[数値JSON](../../results/invention-20261022/invariant-layout-report-v1/facts.json)
- [正当性](../../results/invention-20261022/invariant-layout-v3/checks.json)、[回復候補](../../results/invention-20261022/invariant-layout-v3/analysis.json)、[小語長モデル](../../results/invention-20261022/invariant-layout-model-v1/model.json)
- [別実行器](../../results/invention-20261022/invariant-layout-audit-v2/interpreter.json)、[追加ページ](../../results/invention-20261022/invariant-layout-audit-v2/pages/checks.json)、[再生成](../../results/invention-20261022/invariant-layout-audit-v2/replay.json)
- [性能条件](../../results/invention-20261022/invariant-layout-runtime-v1/protocol.json)、[証拠照合](../../results/invention-20261022/invariant-layout-report-v1/verification.json)

## 結果の範囲

3種類の小さな状態更新kernelをplain、fixed、full、transportでraw/O3比較し、回復版も含む正42条件で共通468入力列を使った。19,656呼出し（期待trap 5,040件）の戻り値、trap有無、復号後の全64KiBメモリが一致した。更新後の配置修復を省く負6条件は全て不一致を検出した。同じ入力の再実行を独立ケースとして加算しない。

方式既知攻撃は公開binaryだけから18/18条件に通常配置の候補を生成した。固定・動的配置とも1,024 helper問い合わせを使う。候補同定は有限試験であり、任意の改変binaryへの全入力同値性を証明するものではない。回復候補を主実験へ含めて別に検査した。

42本のbyte一致再生成と、WABT interpreterで値168呼出し、trap42呼出し、物理メモリ840 probeの照合を行った。0/2ページの8条件520呼出しも一致。小語長135,296更新の全探索、32bit乱数4,096更新も確認した。有限試験を変換器全体の形式検証とはしない。

45 fresh Node process・405batchで、transport/fullは約0.812～0.876、transport/plainは約12.48～18.22。主測定はWasm内部loopで入力更新と1～8回の元更新を含む。O3の回復処理を7回ずつ測ると、transport/fixedの中央値比は約1.017～1.055、process範囲は重なった。回復時間にはWABT・Node起動・候補コンパイルを含む。追加の保護効果が実行負担に見合うとは示せていない。

全条件のlinear memoryは64KiBで配置表の追加はない。CPU・V8一組の測定であり、実アプリ、同コスト調整、汎用逆コンパイラ、人間の分析時間は未評価。既存ツールそのものとの性能比較でもない。動的な配置・データ依存符号化は先行公報にあり、今回の具体規則の独立性も未確立である。

## 再現

Windows、Python3.9、Node24.15、WABT1.0.42、Binaryen133。追加package不要。既存のpage-block-codec/isotope-swizzle/connectivity-eliminationのWAT reader・writer・tool helperを使う。`.tools`の同版を用意し、リポジトリrootから未作成の出力先へ実行する。性能測定は他の実験と同時に走らせない。

```powershell
python -X utf8 research/invariant-layout/model.py results/layout-new/model
python -X utf8 research/invariant-layout/run.py results/layout-new/main
python -X utf8 research/invariant-layout/audit.py results/layout-new/main results/layout-new/audit
python -X utf8 research/invariant-layout/performance.py results/layout-new/main results/layout-new/runtime
python -X utf8 research/invariant-layout/analysis_bench.py results/layout-new/main results/layout-new/analysis
python -X utf8 research/invariant-layout/report.py results/layout-new/main results/layout-new/audit results/layout-new/runtime results/layout-new/analysis results/layout-new/model results/layout-new/report
```

実際の入力Wasmを変換・回復するCLIもある。対応profileは[algorithm.md](algorithm.md)を参照。

```powershell
python -X utf8 research/invariant-layout/prototype.py source.wasm results/new-layout.wasm --mode transport
python -X utf8 research/invariant-layout/attack.py results/new-layout.wasm results/new-recovered.wasm results/new-identification
```

main-v1はSIMD flag不足で中断。v2は主試験を完了し、checkerに0/2ページ用の入力と空メモリ対応を加えたv3を主記録にした。audit-v1はO3で削除された0ページmemoryへの計測用exportで中断したため、計測wrapperだけに空memoryを足したv2で完了した。どちらも解析耐性や変換効果の証拠には数えない。失敗した出力も保持する。
