# コピーの情報損失に適合する現状態修復

2026-10-22。**入口保存をなくす構成と、一部の正常出口での費用改善を確認した。追加の解析耐性は示せず、主難読化方式には採用しない。** 既存prefix-repairの拡張であり、独立した新原理の候補数には加えない。

コピーで失われる情報をまだ必要な情報へ混ぜない行列を生成し、出口のmemoryを使って表現を修復する。保存した入口の値を持ち回る必要がなくなる。出口修復中の一時値は残り、総メモリ使用量0という意味ではない。

- [事前計画](plan.md)、[アルゴリズム・証明条件・攻撃モデル](algorithm.md)、[先行資料と差分](prior-art.md)、[論文追補](paper-note.md)
- [実測比較表](../../results/invention-20261022/loss-flag-report-v1/comparison.md)、[集計・環境](../../results/invention-20261022/loss-flag-report-v1/facts.json)
- [主manifest](../../results/invention-20261022/loss-flag-v1/manifest.json)、[正当性](../../results/invention-20261022/loss-flag-v1/checks.json)、[binary-only回復](../../results/invention-20261022/loss-flag-v1/analysis.json)
- [小モデルと情報損失反例](../../results/invention-20261022/loss-flag-model-v1.json)、[再生成・別実行器・負例・反復回復](../../results/invention-20261022/loss-flag-audit-v1/audit.json)
- [最終性能記録](../../results/invention-20261022/loss-flag-performance-v2/runtime.json)、[初回harnessの参考値](../../results/invention-20261022/loss-flag-performance-v1/runtime.json)

## 結果

3種類の固定copy構造、2seeds、raw/O3を使用。実アプリ3個ではない。正の54実行条件（42 unique positive binary）・83,196呼出し、期待trap42,588で値・trap・全64KiB physical memoryが一致。回復版と未変換版に同一byte列があり、条件数を異なるプログラム数とは扱わない。意図的なtrap修復欠落12条件は全て反例を検出。別WABT interpreterは360呼出し、198trap、1,404 memory probeを照合し、66本の再生成はbyte一致した。

3byte小モデルは全168可逆行列×3構造、107,520状態対を調べた。適合する行列は8/24/24個で、各copyとの可換性を要求する各1個より広い。ただし一般nの意味保存は[行列の導出](algorithm.md)に依存し、有限試験だけを全入力の証明としない。

O3、seed221001、別module importによる正常runの結果。時間は各3 fresh processの中央値、各processはwarmup32,768回、校正後7batch。全252batchが10ms以上。入力failはloop内で変化するが全て正常経路で、memoryは反復で変化・安定し得る。

| copy構造 | plain ns/run | eager ns/run | basis ns/run | current ns/run | current/basis | 入口保存値 basis→current |
|---|---:|---:|---:|---:|---:|---:|
| swap16 | 2.351 | 8.304 | 4.812 | 4.948 | 1.028 | 3→0 |
| cascade32 | 4.022 | 55.543 | 15.327 | 11.297 | 0.737 | 21→0 |
| overlap24 | 11.845 | 59.073 | 27.021 | 19.517 | 0.722 | 20→0 |

same Bのbasisに対し2構造で約26～28%短縮、1構造で約2.8%悪化。current/plainは約1.65～2.81倍。コードはbasisの815/2639/3271bytesからcurrentの948/2788/3498bytesへ増加。全modeの線形memoryは64KiB、whole Node最大RSSは36,076～36,444KiB。currentの変換時間は6構成で約79.4～88.6ms（各1回、読取・構築・WABT compile/validate込み）。修復一時値は3～20個のi32 localで、実CPUのregister/stack量は未測定。

初回の同module・定数failのharnessではplainが約0.58～0.63ns/runの構造があり、JITによるinlining・loop内最適化と呼出し境界の影響を分けられなかった。初回を捨てず記録し、別moduleのimportと変化するsafe failを用いたv2を主比較にした。両harnessで2構造の改善とswapの悪化という方向は同じ。実アプリ、trap経路、動的copyで同率の改善を保証しない。

既存prefix-repair回復器を未変更で適用し、currentの12/12条件を元sourceとbyte一致するWasmへ戻せた。元source・manifestは回復後の採点だけに使う。oracle queryは0。basis/currentの各5反復による計60回の回復も成功し、currentの読取・出力込み中央値は約42～53ms、basis比は約0.916～1.029、解析本体比は約0.693～0.980。追加保護効果の根拠にはならない。

## 再現

Python3.9、Node24.15.0/V8 13.6、WABT1.0.42、Binaryen133。Windowsの`.tools/wabt-1.0.42/bin`と`.tools/binaryen-version_133/bin`を使用する。Python/Node追加package不要。共有する既存prototypeと回復器も必要で、主結果のsourcesに当時の依存ソースを保存した。全てrepository rootから実行し、出力先には未作成の名前を指定する。

```powershell
python research/loss-flag/model.py results/loss-flag-new-model.json
python research/loss-flag/run.py results/loss-flag-new-main
python research/loss-flag/performance.py results/loss-flag-new-main results/loss-flag-new-runtime --imported
python research/loss-flag/audit.py results/loss-flag-new-main results/loss-flag-new-runtime results/loss-flag-new-audit
python research/loss-flag/report.py results/loss-flag-new-main results/loss-flag-new-runtime results/loss-flag-new-audit results/loss-flag-new-report
```

単独変換は `python research/loss-flag/prototype.py input.wasm output.wasm --mode current --seed 221001`。対応sourceはrun.pyが生成する実wasmを参照。任意Wasmへ適用できると主張しない。`--mode basis`と`--mode eager`は同じseedで同じBを使う対照。各測定のraw JSON、stderr、ハッシュ、ソースを保存し、出力上書きを拒否する。性能実行中に他の重い処理を並列実行しない。
