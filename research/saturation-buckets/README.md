# 飽和演算を広いレーンの商として実行する

2026-10-22。狭い範囲のカウンタを広いレーンの上位bitで表し、下位bitを一つにそろえずnative SIMDで更新する実Wasm変換を実装した。**正規化の費用は減ったが、追加の解析耐性は確認できず、主発明には採用しない。** 以前の[有限環方式の構成的提案](../repository-assessment-20261021.md)は保持する。

- [事前仮説と比較方針](plan.md)、[構成・意味保存・解析](algorithm.md)、[先行資料と新規性の限界](prior-art.md)、[修正と次の判断](checkpoint.md)
- [実測比較表](../../results/invention-20261022/saturation-buckets-report-v1/comparison.md)、[集計JSON](../../results/invention-20261022/saturation-buckets-report-v1/report.json)
- [正当性](../../results/invention-20261022/saturation-buckets-v2/checks.json)、[入出力学習](../../results/invention-20261022/saturation-buckets-v2/analysis.json)、[再生成・別実行器・反例](../../results/invention-20261022/saturation-buckets-audit-v1/audit.json)

3合成関数の60正条件、3,962,880呼出しで不一致0。各条件の65,536入力は同じbyte対を全レーンに入れる試験で、全2^128入力の検査ではない。別途512個の独立packed入力を使った。誤変換6条件すべてに反例があり、66本のbyte再生成、WABT別実行器480呼出し、4対象外入力の拒否も確認した。

方式既知の学習は30/30条件で短い等価候補を生成し、上記の差分検査が一致した。元の更新順序を取り戻す必要はなく、固定したdelta入力ごとにclamp式を得れば足りた。通常版・変換版とも同じ2,528–2,558問い合わせだった。一般のレーン間依存がある関数には、この学習法を適用できないという反例も保存した。

補正を残す表現に対し約14–26%の時間削減を確認。一方、通常の8bit SIMD版に対しては約12–33%遅かった。単に16bitで書いた元版と比較して性能優位を主張するのは不適切だった。実行時間・ばらつき・サイズ・変換時間・memory/RSS・測定限界は比較表にある。

## 再現

Python 3.9、Node 24.15.0、WABT 1.0.42、Binaryen 133、Windowsで実行。追加Python/Node package不要。`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`を使用する。`research/isotope-swizzle/prototype.py`と`research/connectivity-elimination/prototype.py`の既存工具に依存し、実験時のsource snapshotとhashも保存した。

rootから実行し、全出力先は未作成の名前を使う。性能測定中は他の重い処理を並列実行しない。

```powershell
python research/saturation-buckets/run.py results/buckets-new/main
python research/saturation-buckets/performance.py results/buckets-new/main results/buckets-new/runtime
python research/saturation-buckets/audit.py results/buckets-new/main results/buckets-new/runtime results/buckets-new/audit
python research/saturation-buckets/report.py results/buckets-new/main results/buckets-new/runtime results/buckets-new/audit results/buckets-new/report
```

個別のバイナリ変換CLI：

```powershell
python research/saturation-buckets/prototype.py results/buckets-new/main/mixed48.source.wasm results/buckets-new/transformed.wasm --mode bucket
node research/saturation-buckets/learn.cjs results/buckets-new/transformed.wasm results/buckets-new/learned.json
```

`learn.cjs`は検証済みの対象族という事前知識に基づいて候補表を出す学習器であり、未知コードの同値性を保証するものではない。一括runはその表をWasmへ再生成し、別oracleと照合する。

入力profileは、2個のi64を各8byteへ分けたレーン独立の飽和更新列。8個の上限は2^b−1、1<=b<=8、更新1..256段。唯一の`run(i64,i64)->i64`があり、import・memory・追加関数・外部副作用・任意の分岐を持たない閉じたrawコード形だけを受け入れる。任意のC/Rust/Wasm、signed整数、任意上限、2つの非正規化状態の加算には非対応。

主結果はmain/runtimeともv2。v1は補正対照の改善とnative8追加前の予備結果で、主集計へ足さない。全実装・全実行環境の形式証明、NotDec等の汎用逆コンパイラによる比較、実アプリでの実用性評価は未実施。
