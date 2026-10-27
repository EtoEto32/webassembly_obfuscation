# 違反量の下降で計算する候補の実装と反証

2026-10-22追加：[符号付き相互作用を合成する最終改良](interactions-analysis.md)。同値energyの選択も考慮して2引数の局所規則を排除したが、消去本体を変えず全12条件を回復できた。修正版30条件61,860呼出し一致、実行は元版比約210–245倍。初期版と修正版を別発明に数えず、このenergy方向は3設計段階で不採用とした。研究全体は継続する。

2026-10-22追加：[優越条件を外す改良](relaxed-analysis.md)を実装。局所更新が元ゲートと逆でも全体が正答する例を得たが、最小化消去で全28条件を回復した。通常180,420呼出し・全初期値probe2,922,496呼出し一致。改良例は元版比約172倍の実行費用で、主発明には不採用。同じ方式の修正であり独立案には数えない。

2026-10-22。**動く試作は得たが、主発明には採用しない。** 全初期値での正答を保証する重み付けから、逆に元の局所更新を回復できた。独立した新規性と有効な保護費用比は未確立。既存の有限環残差方式とは異なる正当性原理だが、新しい発明数へ加算しない。

[事前計画](plan.md)、[アルゴリズム・正答と回復の論証](algorithm.md)、[先行技術と読んだ範囲](prior-art.md)、[実測比較](../../results/invention-20261022/energy-descent-report-v1/comparison.md)、[集計JSON](../../results/invention-20261022/energy-descent-report-v1/facts.json)、[論文追補](paper-note.md)。

## 実験結果

実.wasmのBoolean DAGを整数多項式の違反量へ変換した。内部bitを一つずつ反転し、違反量が下がる時だけ採用する。元ゲート別の区切り・順番・生成seedは配布binaryへ保存しない。配置・極性変更、直接の子に基づく重みと全後続に基づく重みを比較した。

- 3小回路×raw/O3×対照・変換・回復で正42条件（byte異なる30本）、136,444呼出し、不一致0/予期しないtrap0。3回路はchain/diamond/fanoutの合成例で実アプリではない。
- 全18保護条件をbinaryだけから一回評価のDAGへ回復。public I/O queryは使わない。差分のsupportは最大4/6/10変数、116/244/1,156行を列挙すると、すべて2入力の局所規則に縮約。未対応・クラッシュ・timeoutは主条件で0。
- 回復本体11回中央値は約0.26–3.00ms。reader・実行器再生成・O3照合・compile込みの単発総時間は約61–83ms。解析器開発の人間時間は未測定。
- 等重み6条件はすべて誤答を検出。小3ゲート例の全入力×全内部初期値32組では、優越重み4設定128組は一致し、等重みは配置変更有無それぞれ7/32組で誤り。
- 別WABTで168呼出し一致、48本のbyte再生成、回復規則と元ゲートの336局所真理値照合、対象外source3拒否、改変した実行器の拒否を確認。

O3、共通Wasm計測loop中のns/call：

|回路|元版|子重み・自然配置|子重み・配置極性変更|全後続重み・配置極性変更|回復後O3|
|---|---:|---:|---:|---:|---:|
|chain|1.786|1810.873|1773.194|1822.733|5.383|
|diamond|1.920|3222.781|3257.928|3256.714|5.602|
|fanout|1.800|3180.340|3257.758|3265.624|5.378|

配置極性変更版は元版比約993–1,810倍、回復版比約329–606倍。回復版は短い真理値lookupであり、元と同じ命令列ではなく元版より遅い。これらは短いカーネルの測定で、アプリ全体の倍率でもenergy方式一般の下界でもない。現在の汎用評価器は反転ごとに全energyを読み直すため重い。疎な差分評価など改善余地はあるが、回復可能性の理由は変わらない。

性能は15対象×3 fresh Node process×7batch=315batch。16,384呼出しwarmup、20ms目標calibration、全batch10ms以上。固定seedでprocess順shuffle、計測中に別の重い検査は走らせていない。Node `--no-liftoff --no-wasm-lazy-compilation`、CPU affinity/周波数固定なし。process中央値の範囲は比較表に記録。独立のJS oracleで性能用最適化版とwrapper checksumも確認したが、同じ入力領域の再確認で独立コーパスとは数えない。

生成時間は12単発で約36.7–39.9ms（WABT込み）。変換版はprivate線形memory 65,536B、元・回復版は0B。O3 byteサイズは元112–124B、変換730–831B、回復186–217B。process maxRSS 37,796–38,336KiBはNode等を含み、Wasm単独のheap量ではない。

## 再現

Python3.9、Node24.15.0/V8 13.6、WABT1.0.42、Binaryen133。標準ライブラリのみ。ツールは`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`。別rootは`WASM_TOOLS_ROOT`で指定する。共有WAT parser/CLI helperは`research/connectivity-elimination/prototype.py`。生成・読取・回復sourceと結果hashを各出力へ保存する。全コマンドはrepo rootから、新しい出力先へ実行する。

```powershell
python -X utf8 research/energy-descent/run.py results/energy-new/main
python -X utf8 research/energy-descent/performance.py results/energy-new/main results/energy-new/performance
python -X utf8 research/energy-descent/audit.py results/energy-new/main results/energy-new/audit
python -X utf8 research/energy-descent/report.py results/energy-new/main results/energy-new/performance results/energy-new/audit results/energy-new/report
```

単独CLI：

```powershell
python research/energy-descent/prototype.py transform input.wasm output.wasm --mode dag --gauge
python research/energy-descent/prototype.py recover output.wasm recovered.wasm
```

対象範囲と資源条件はalgorithm.mdを参照。全般的なC/Rust出力、メモリ副作用、浮動小数点、共有メモリは扱わない。攻撃の20変数列挙上限を超えた入力や一致しない実行器は拒否し、その未対応を解析耐性に数えない。有限テストだけから全入力の実装同値性を証明したとはしない。

reportの初回実行はPython3.9のsource encodingエラーで停止した。UTF-8宣言を明示して再実行しexit0を確認した。これは実験失敗や保護効果ではなく、結果生成スクリプトの起動修正である。
