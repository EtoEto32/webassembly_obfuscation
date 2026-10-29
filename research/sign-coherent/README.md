# 有限整数領域で同符号となる係数の混合

2026-10-22。非線形演算の前後の係数を書き換え、明示decoderを置かない変換を実Wasmで試した。構成と実装は成立したが、同じactivation patternに基づく既存研究との距離が小さく、追加の解析耐性も確認できなかった。**主発明には採用しない。** 以前の[有限環残差フィードバックの構成的提案](../repository-assessment-20261021.md)の限定採用は、この結果によって取り消さない。

- [事前仮説](plan.md)、[アルゴリズム・意味保存・攻撃](algorithm.md)、[先行研究との対応](prior-art.md)、[判断の修正](revision.md)、[チェックポイント](checkpoint.md)
- [実測比較表](../../results/invention-20261022/sign-coherent-report-v1/comparison.md)、[集計JSON](../../results/invention-20261022/sign-coherent-report-v1/report.json)
- [正当性検査](../../results/invention-20261022/sign-coherent-v2/checks.json)、[方式既知解析](../../results/invention-20261022/sign-coherent-v2/analysis.json)、[再生成・別実行器・対象外入力](../../results/invention-20261022/sign-coherent-audit-v1/audit.json)

対象は2引数の低8bitをsigned8へ写す、4 channelの整数閾値計算。学習済みモデルや任意のWasmへの変換ではない。全65,536入力で正負の切替えが一致するchannelを混合し、後段の重みで補償する。非比例の係数でも同じ符号になる有限格子を使ったが、有限データ上のactivation coneは既存研究の対象でもある。

3合成関数・1混合seed。正36条件の2,377,728呼出しは不一致0、負6条件は全て反例あり。方式既知の回復では18条件がfixtureごとに同じ短い等価binaryへ戻った。元の係数列の一意復元ではない。WABT別実行器の288呼出しも一致し、42本のbyte再生成と4対象外profileの拒否を確認した。

36 fresh processの実行計測で、O3通常版の中央値は約2.40–2.46 ns、混合版は約2.35–2.37 ns、回復版は約1.78–1.96 nsだった。共通の入力更新・loop・checksumを含む極小処理の値であり、数%の差を高速化の確証としない。process間の範囲、変換単回時間、サイズ、RSS、測定限界は比較表・JSONに保存した。

## 再現

Python 3.9、PATH上のNode 24.15.0、`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`を使用。追加Python/Node package不要。既存の`prefix-repair/prototype.py`、`copy-centralizer/model.py`、`isotope-swizzle/prototype.py`、`connectivity-elimination/prototype.py`の工具に依存するため、このフォルダだけを抜き出さない。主実験には当時の依存sourceとhashを保存してある。

rootから実行し、出力は未作成のパスを指定する。性能測定中は別の重い処理を並列に動かさない。

```powershell
python research/sign-coherent/run.py results/sign-coherent-new/main
python research/sign-coherent/performance.py results/sign-coherent-new/main results/sign-coherent-new/runtime
python research/sign-coherent/audit.py results/sign-coherent-new/main results/sign-coherent-new/runtime results/sign-coherent-new/audit
python research/sign-coherent/report.py results/sign-coherent-new/main results/sign-coherent-new/runtime results/sign-coherent-new/audit results/sign-coherent-new/report
```

個別CLIは、上記で生成するprofileに対して次のとおり使う。profile照合は閉じたraw/O3コード形を再生成して比較するため、任意の同値Wasmを受理するものではない。

```powershell
python research/sign-coherent/prototype.py transform results/sign-coherent-new/main/axis.source.wasm results/sign-coherent-new/axis-mixed.wasm --mode mix
python research/sign-coherent/prototype.py recover results/sign-coherent-new/axis-mixed.wasm results/sign-coherent-new/axis-recovered.wasm
```

全入力列挙は、この小さいreduced domainについての検査である。Wasmコンパイラや実行器を含む数学的な機械証明ではない。トラップを生じない固定memory・純粋計算のprofileで、memory副作用や浮動小数点の意味保存は対象外。resource exhaustionによるインスタンス生成失敗の一致も対象外とする。未対応、クラッシュ、タイムアウトを解析困難性として加算していない。
