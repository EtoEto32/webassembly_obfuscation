# 観測状態の自動閉包：実装・反証結果

2026-10-23。**主特許候補には不採用。** 非線形状態を元のwordのまま保存せず更新する生成器を実装したが、少数の公開API呼出しから同等の小さなWasmへ戻せた。単に可逆符号化を外すだけでは足りないことを実証した。

- [事前計画](plan.md)、[アルゴリズム・成立条件・攻撃](algorithm.md)、[先行研究との比較](prior-art.md)
- [実測報告](../../results/invention-20261023/observer-closure-report-v1/report.md)
- [主実験](../../results/invention-20261023/observer-closure-v1/checks.json)、[小幅全列挙・係数証明・別エンジン](../../results/invention-20261023/observer-closure-audit-v1/audit.json)
- [reset/peek削除後の追試](../../results/invention-20261023/observer-closure-fresh-v1/checks.json)

3つの人工多項式更新をraw/O3で検査。主30正条件の780,090 API呼出し（374,430 step、390,060 peek、15,600 reset）で不一致・trapは0。不正に一次座標の寄与を落とす負対照6条件は全て反例あり。主回復12条件は各10step+10reset、reset/peek削除後も12条件を各22step・12instanceで回復。追試30条件491,520 stepも一致した。raw/O3は独立プログラムではない。

小幅2..8bitの42閉包で524,256状態・入力対を全列挙。主12と追試12の回復多項式は、元との関数差がmod2^31で0になることをNewton係数で確認。WABTでは主30条件の計360stepと90最終観測を確認した。これらは任意Wasm全体の形式同値証明ではない。

O3実行中央値（1step相当、loop・入力更新・checksumを含む）は元1.39/2.02/2.80ns、quotient13.57/20.26/14.48nsで約5.18–10.05倍。full対照との差は小さくばらつきが重なる。元stateを残さない利点は保護費用にも性能にも確認できなかった。36 fresh process・252batch、20ms校正、16,384step warmup。全batch10ms以上。CPU固定・OSノイズ制御はしていない。

## 再現

Python3.9以上、Node24.15.0、WABT1.0.42、Binaryen133。追加Python package不要。既存共通helperをimportするので本ディレクトリ単独ではなくリポジトリを用いる。`.tools/wabt-1.0.42/bin` と `.tools/binaryen-version_133/bin` の配置を使用。以下はrepository rootから実行し、出力先は未作成の名前を選ぶ。

```powershell
python research/observer-closure/run.py results/observer-new/main
python research/observer-closure/audit.py results/observer-new/main results/observer-new/audit
python research/observer-closure/performance.py results/observer-new/main results/observer-new/runtime
python research/observer-closure/fresh.py results/observer-new/main results/observer-new/fresh
python research/observer-closure/report.py results/observer-new/main results/observer-new/audit results/observer-new/runtime results/observer-new/fresh results/observer-new/report
```

個別CLI：

```powershell
python research/observer-closure/prototype.py transform input.wasm transformed.wasm --mode quotient
python research/observer-closure/prototype.py recover transformed.wasm recovered.wasm
python research/observer-closure/prototype.py recover step-only.wasm recovered-step-only.wasm --fresh
```

`--mode full`が元stateを残す対照、`--mode bad`は正当性を故意に破る負対照。任意Wasm用の変換器ではなくcanonical profile以外を拒否する。回復器は公開profileを仮定する選択入力学習であり、任意binaryの意味を有限クエリで証明するものではない。`candidate_recovered` と別途の係数証明・実行検査を分けて保存する。

結果のファイル数や検査回数を発明の数に数えない。生成規則、費用、解除理由を第三者が追える形に保存したが、主発明の研究は未完了。
