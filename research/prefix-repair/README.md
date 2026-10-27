# 符号化したコピー列の共有修復

2026-10-22。正常終了と途中trap後のmemory状態を保ち、修復をまとめる限定Wasm変換を実装した。
同じcodecで各copyを即修復する版に対し、3種×2seedの中央値では実行時間が約28～48%減った。
一方、未変換版の約10.9～16.4倍を要し、方式既知の回復器で全正条件を元形式へ戻せた。
独立した新規性と追加の保護効果は未確立。主発明には採用せず、費用削減の部品として保存する。

- [事前計画](plan.md)、[アルゴリズム・証明条件・攻撃モデル](algorithm.md)、[先行研究](prior-art.md)、[修正履歴](revision.md)
- [実測比較表](../../results/invention-20261021/prefix-repair-report-v1/comparison.md)、[集計JSON](../../results/invention-20261021/prefix-repair-report-v1/report.json)
- [主正当性結果](../../results/invention-20261021/prefix-repair-v2/checks.json)、[方式既知の回復](../../results/invention-20261021/prefix-repair-analysis-v4/analysis.json)
- [再生成・別実行器・拒否対照](../../results/invention-20261021/prefix-repair-audit-v1/audit.json)

## 実験の範囲

3個の固定copy列、2行列seed、plain/eager/full/basis/bad、raw/O3の60条件。
48正条件で42,496呼出し、期待trap21,888、不一致0。各呼出し後の全64KiBとdigestを独立JSモデルと比較した。
入口状態はuniform境界値6個、N個のbyte基底、乱数64個。乱数seedは固定だが条件間で同じ乱数状態ではない。
同一instanceに正常・各位置のtrap・正常を繰り返し、trap後の継続も確認した。
badはtrap修復を省く対照で、全12条件で反例を検出した。全入力の数学的同値証明とは扱わない。

回復48条件は元sourceとbyte一致し、重複を除く3出力を2,656呼出しで再検査。
最終回復器では正常48成功、誤変換12拒否、unsupported/crash/timeoutは0。
初期実装の未対応や旧checkerの過大受理は履歴に分け、保護効果に加算しない。
WABT interpreterでは48正条件336呼出しのtrapと後続digestを別途確認した。
主binary60本と診断用memory export版60本を再生成してbyte一致を確認した。

性能はO3へ共通Wasm loopを追加した後に測定。3 fresh process×9batch、warmup65,536回。
Node flagsは`--no-liftoff --no-wasm-lazy-compilation`。順序を固定seedでshuffle。
正常pathのみ、末尾digestはbatchごとに1回。compilationは計測外、CPU固定はしていない。
648batch中79は5ms未満で、短いplain実行では計測粒度に注意が必要。
追加linear memoryは0だが保存localは増える。RSSはNode全体の値で、Wasm専用の資源量ではない。
transform_msと解析読取時間は各条件の単回計測であり、反復測定した実行時間と区別する。

## 再現

Windows、Python3.9、Node24.15.0 / V8 13.6.233.17-node.48、
`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`を使用。
Python/Nodeの追加packageは不要。rootから実行し、未作成の出力directoryを指定する。

```powershell
python research/prefix-repair/run.py results/prefix-repair-new/main
python research/prefix-repair/evaluate.py results/prefix-repair-new/main results/prefix-repair-new/analysis
python research/prefix-repair/performance.py results/prefix-repair-new/main results/prefix-repair-new/runtime
python research/prefix-repair/audit.py results/prefix-repair-new/main results/prefix-repair-new/analysis results/prefix-repair-new/runtime results/prefix-repair-new/audit
python research/prefix-repair/report.py results/prefix-repair-new/main results/prefix-repair-new/analysis results/prefix-repair-new/runtime results/prefix-repair-new/audit results/prefix-repair-new/report
```

単体変換は次のCLI。対応profile以外は拒否する。

```powershell
python research/prefix-repair/prototype.py results/prefix-repair-new/main/swap16.source.wasm results/prefix-repair-new/custom.wasm --mode basis --seed 211070
```

共通helperは`isotope-swizzle/prototype.py`、`connectivity-elimination/prototype.py`、
`copy-centralizer/model.py`を参照し、main結果にsource snapshotを保存する。
最終回復器はanalysis-v4のsnapshot、旧版の反例はauditに保存。
監査は旧analysis-v3が存在するときだけ旧checkerの過大受理も再現する。
