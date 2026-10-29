# 商と余りの小数部融合：構成と限界

2026-10-22。u32の商・余りを一つのu64除算へ融合し、入力依存の値を加えても両結果を保つ許容範囲を求めた。実.wasm変換器、方式既知の回復器、数学モデル、差分・性能実験を保存した。**正当性は支持されたが、独立した新規性と追加の保護効果は未確立。主発明には採用しない。** 以前の有限環方式の構成的提案は保持する。

- [事前計画](plan.md)、[アルゴリズム・許容範囲の論証・攻撃モデル](algorithm.md)、[先行技術との対応](prior-art.md)、[判断と修正履歴](checkpoint.md)
- [実測比較](../../results/invention-20261022/fractional-pair-report-v1/comparison.md)、[集計値](../../results/invention-20261022/fractional-pair-report-v1/report.json)
- [正当性・trap・負例](../../results/invention-20261022/fractional-pair-v2/checks.json)、[入力](../../results/invention-20261022/fractional-pair-v2/inputs.json)、[許容範囲モデル](../../results/invention-20261022/fractional-pair-v2/model.json)
- [方式既知の回復](../../results/invention-20261022/fractional-pair-v2/analysis.json)、[再生成・別実行器・拒否対照](../../results/invention-20261022/fractional-pair-audit-v1/audit.json)

3合成consumerの36正条件、951,540呼出し（trap3,528件を含む）で不一致0。幅2..6の全x,d,t 294,128組と、32bitの30,000組で許容範囲を検査した。6誤変換に反例、42本のbyte再生成一致、別WABT実行288呼出し一致、6対象外・不正構成の拒否を確認した。有限テストは全2^64入力の形式証明ではない。

O3後も広い除算は残るが、raw/O3の12変換条件すべてを公開binaryだけから通常div/remへ回復した。回復本体の単回診断値は約0.27–1.06ms、読取約15.7–17.7ms。人間の開発時間や統計的な攻撃費用とは区別する。

90 fresh process、810 batchの性能測定で、fractionは商から余りを減算する通常のqsub対照より約1.58–1.81倍遅かった。pairだけならplainのdiv+remより少し速いが、より良い通常実装との比較で優位ではない。線形memoryは全版0、Node全processの最大RSSは36,204–36,704KiB。190 batchは10ms未満、CPU affinity/frequency未固定、変換器固有のpeak memoryは未測定。

## 再現

Python3.9.0、Node24.15.0 / V8 13.6、WABT1.0.42、Binaryen133、Windows、Intel Core i9-11900K。追加Python/Node package不要。`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`、既存の`research/isotope-swizzle/prototype.py`と`research/connectivity-elimination/prototype.py`を使用。実験時sourceとhashを保存する。

rootから実行し、出力先には未作成の名前を指定する。性能測定中は他の重い処理を実行しない。

```powershell
python research/fractional-pair/run.py results/fraction-new/main
python research/fractional-pair/audit.py results/fraction-new/main results/fraction-new/audit
python research/fractional-pair/performance.py results/fraction-new/main results/fraction-new/runtime
python research/fractional-pair/report.py results/fraction-new/main results/fraction-new/runtime results/fraction-new/audit results/fraction-new/report
```

個別変換と回復：

```powershell
python research/fractional-pair/prototype.py transform input.wasm output.wasm --mode fraction
python research/fractional-pair/prototype.py recover output.wasm recovered.wasm
```

入力はpure i32/i64 module内の、同じlocalまたは定数をoperandとするpacked unsigned div/rem式に限る。loop/if内も対象にする。memory/import/global/table、signed div、float/SIMD等は拒否する。一般のC/Rustコードの全除算に対応するものではない。custom sectionと資源枯渇時の動作は保持契約外。

plain、qsub、zero、fraction、badは同じ原理の比較・アブレーション・負例であり、五つの発明ではない。既存難読化ツールや汎用逆コンパイラとの実測比較、実製品での有効性は未確認。主結果はv2、初回v1の呼出し数は加算しない。
