# 浮動小数点の零符号を遅延修復する変換

2026-10-21。有限環反復とは別原理の難読化候補を、実Wasm変換・方式既知解析・性能比較まで進めた。**非零の数値計算と、必要時だけの零符号の修復を分ける具体的な構成候補**である。符号反転自体の新規性や、主発明の確立は主張しない。

自作の各演算修復対照と比べ、通常値の3例で時間を約36–66%減らした。一方、公開Wasmから数値graphを抽出し、零の時だけ元処理を残す部分簡約は、通常値で未変換の約0.99–1.12倍の時間となった。費用改善の部品として保持し、特許を目指す主案としての採用は保留する。以前の有限環方式の構成的な限定採用は保持する。

- [アルゴリズム・意味保存の論拠・対象範囲](algorithm.md)
- [先行技術との具体比較・未読部分](prior-art.md)
- [事前計画](plan.md)、[追加検査計画](generalization-plan.md)、[修正履歴](revision.md)
- [結果の解釈と限界](analysis.md)、[論文追補](paper-note.md)、[再開記録](checkpoint.md)
- [性能比較表](../../results/invention-20261021/zero-sign-report-v1/comparison.md)、[主集計](../../results/invention-20261021/zero-sign-report-v1/summary.json)
- [主正当性検査](../../results/invention-20261021/zero-sign-v5/checks.json)、[適応解析の記録](../../results/invention-20261021/zero-sign-v5/attacks.json)
- [別実行器](../../results/invention-20261021/zero-sign-audit-v1/interpreter.json)、[88本のbyte再現](../../results/invention-20261021/zero-sign-audit-v1/replay.json)
- [共有DAG・引数数の追加検査](../../results/invention-20261021/zero-sign-generalization-v1/generalization.json)、[丸め順序の負例](../../results/invention-20261021/zero-sign-generalization-v1/rounding-controls.json)

## 検査結果の読み方

主実験は4例・88本・585,728呼出し。このうち正しさを要求する56本・372,736呼出しで不一致0。生成した回復candidateの16本中4本は零符号が不一致になり、元の零経路を残すresidual 16本は一致した。修復なしの負例は16本中10本で誤りを検出した。

追加の共有DAG6例は108本・136,512呼出し。正しさを要求する84本・106,176呼出しで不一致0、candidate 24本中8本に零符号の不一致。零fallback付きは全件一致。candidateを成功結果へ混ぜない。有限検査を全入力の機械証明とはしない。

性能は3例×4方式×2入力分布×5process=120process。各9batch、1024warmup、共通Wasm loop。12本の性能用バイナリも79,872呼出しで再照合した。通常値分布と全零分布を分ける。NaNやsubnormal主体の速度は測っていない。サイズは元コードを残す適応版も全量、メモリはlinear memoryとNode全体RSSを区別する。

## 環境・再現

Python3.9、PATH上のNode24.15.0、`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`。追加Python/Node package不要。WAT reader等を`research/isotope-swizzle/prototype.py`と`research/connectivity-elimination/prototype.py`から利用するため、その2ファイルも必要。実行器・optimizerの版は[環境記録](../../results/invention-20261021/zero-sign-audit-v1/environment.json)を参照。

rootから、全て未作成の出力先を指定する。生成器は既存Wasm/WATの上書きを拒否する。性能測定と重い別処理を同時に走らせない。

```powershell
python research/zero-sign-transport/run.py results/zero-sign-new/main
python research/zero-sign-transport/performance.py results/zero-sign-new/main results/zero-sign-new/runtime
python research/zero-sign-transport/audit.py results/zero-sign-new/main results/zero-sign-new/audit
python research/zero-sign-transport/report.py results/zero-sign-new/main results/zero-sign-new/runtime results/zero-sign-new/audit results/zero-sign-new/report
python research/zero-sign-transport/generalization.py results/zero-sign-new/generalization
python research/zero-sign-transport/finalize.py results/zero-sign-new/main results/zero-sign-new/runtime results/zero-sign-new/audit results/zero-sign-new/generalization results/zero-sign-new/report
```

単一入力を変換するCLI（対象profileは[algorithm.md](algorithm.md)）：

```powershell
python research/zero-sign-transport/prototype.py transform results/zero-sign-new/main/fma-source.wasm results/zero-sign-single/encoded.wasm --mode deferred --seed 37
python research/zero-sign-transport/prototype.py recover results/zero-sign-single/encoded.wasm results/zero-sign-single/candidate.wasm
```

`recover`単体は零符号を保存しない候補を出す。正しい置換として自動投入しない。零fallback版の生成と検査は`run.py`に含まれる。ソース入力のAPIにNaN正規化があることが必須で、任意のWasmへ適用するCLIではない。
