# 範囲コピーを観測位置へ引き戻す初期検査

**主特許候補としては不採用。** 値の可逆符号化から離れた候補を実Wasmで検査した。copyの実行を最後のloadの位置計算へ変えると、この限定負荷では高速化する。しかしlazy copy/read forwardingは既知であり、公開条件式から元copy列を戻せた。新しい保護原理を確立したとは扱わない。

- [事前計画](plan.md)、[意味保存・回復・採否](algorithm.md)、[先行技術](prior-art.md)
- [実測レポート](../../results/invention-20261023/range-pullback-report-v1/report.md)

Python3.9、Node24.15、WABT1.0.42、Binaryen133。追加Pythonパッケージ不要。既存.toolsを使用し、ネット接続不要。共通helperはmutation-quotient/prototype.py、isotope-swizzle/prototype.py、connectivity-elimination/prototype.py。性能runnerはspan-mask/bench.cjs。結果先は未作成の別名を指定する。

```powershell
python research/range-pullback/run.py results/range-repro-main
python research/range-pullback/model.py results/range-repro-model
python research/range-pullback/audit.py results/range-repro-main results/range-repro-audit
python research/range-pullback/performance.py results/range-repro-main results/range-repro-runtime
python research/range-pullback/report.py results/range-repro-main results/range-repro-model results/range-repro-audit results/range-repro-runtime results/range-repro-report
```

単独CLI：

```powershell
python research/range-pullback/prototype.py transform results/invention-20261023/range-pullback-main-v2/c2-v0-plain-raw.wasm tmp/range-demo.wasm
python research/range-pullback/prototype.py recover tmp/range-demo.wasm tmp/range-restored.wasm
```

sourceとprotectedの両方について、全moduleが許可profileと一致することを検査する。一般のWasm変換器ではない。原版と変換版はどちらもprivate memoryを持ち、公開APIはrunのみ。途中の物理memoryの一致は契約に含めず、値とtrapを比較する。

主はmain-v2。main-v1は最適化後のoperand stackへの対応不足で中断し、耐性に数えなかった。smoke-v1も同じ改善前後の検査であり、主件数へ加算しない。
