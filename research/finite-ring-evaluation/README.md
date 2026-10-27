# 有限環残差フィードバック方式の追加評価

2026-10-21。10月12日に採用した[構成的提案](../../experiments/sha256-fixedpoint/research-checkpoint-ja.md)の、未測定だった方式既知解析・実行費用を検査した。構成上の差分を持つ提案が存在することと、難読化性能が優れていることを分ける。本評価で採用済みの生成規則や元のWasmを変更していない。

**現在の381座標の実装から、通常最適化の前後とも反復を除いた回路を復元できた。** 元回路・circuit.json・他ラウンドの通常T2を回復器へ与えていない。メモリ副作用を再構築した版も、既存531入力で全SHA-256の値・状態を保存した。単に復元可能だから難読化でないと判定するのではなく、機械的回復の費用に対し実行費用が非常に大きい点を限界とする。

- [事前計画](plan.md)、[修正履歴](revision.md)、[機構・解釈・限界](analysis.md)、[論文追補](paper-note.md)
- [実測比較表](../../results/invention-20261021/finite-ring-report-v1/comparison.md)、[集計JSON](../../results/invention-20261021/finite-ring-report-v1/report.json)
- [値・メモリ・ハッシュ・trap検査](../../results/invention-20261021/finite-ring-main-v2/checks.json)
- [負の対照](../../results/invention-20261021/finite-ring-controls-v1/controls.json)、[証明条件の拒否](../../results/invention-20261021/finite-ring-controls-v1/rejections.json)
- [再生成・byte一致](../../results/invention-20261021/finite-ring-audit-v1/replay.json)、[別実行器](../../results/invention-20261021/finite-ring-audit-v1/interpreter.json)、[環境](../../results/invention-20261021/finite-ring-audit-v1/environment.json)

## 結果の範囲

対象はSHA-256最終ブロック最終ラウンドのT2に使われた一つの回路。raw/O3は同じ回路の2形態であり、2つの独立ベンチマークではない。局所256組×10版の2,560呼出し、全ハッシュ531入力×6版の3,186呼出しで不一致0。状態の有無、返り値、counter、トラップを別途確認した。全入力での機械検証ではない。

O3原型はhelper 1回約832µs、十分な129反復へ短縮すると約50.3µs、全scratchを再構築する回復版は約0.257µsだった。5 fresh process×9 batch、共通Wasm loop、入力を変えてchecksumを観測。原型/回復版は約3,243倍だが、SHA-256全体の加速率ではない。

回復器は残差ミキサーの条件と依存順を検査し、最終版再実行の読取約44–51ms、回復本体11反復中央値約80–83ms。読取は1回、回復本体は同一process内の反復であり、25 fresh processの実行費用測定とは方法が違う。解析器を開発する人間の時間は測っていない。

## 再現

Python 3.9、PATH上のNode 24.15.0、リポジトリの`.tools/wabt-1.0.42/bin`および`.tools/binaryen-version_133/bin`を使用。Python/Node追加package不要。比較用の既存SHAバイナリと`experiments/sha256-research-baseline/artifacts/inputs.{json,bin}`を使用し、元資産のライセンスを維持する。全てrootから実行し、出力先は未作成の別名を選ぶ。各段階は既存出力への上書きを拒否する。

```powershell
python research/finite-ring-evaluation/isolate.py experiments/sha256-fixedpoint/artifacts/fixedpoint.wasm results/finite-ring-new/isolation
python research/finite-ring-evaluation/recover.py results/finite-ring-new/isolation/isolated-raw.wasm results/finite-ring-new/raw
python research/finite-ring-evaluation/recover.py results/finite-ring-new/isolation/isolated-O3.wasm results/finite-ring-new/O3
python research/finite-ring-evaluation/prepare.py results/finite-ring-new/isolation results/finite-ring-new/raw results/finite-ring-new/O3 results/finite-ring-new/main
python research/finite-ring-evaluation/controls.py results/finite-ring-new/main results/finite-ring-new/controls
python research/finite-ring-evaluation/benchmark.py results/finite-ring-new/main results/finite-ring-new/runtime
python research/finite-ring-evaluation/audit.py results/finite-ring-new/isolation results/finite-ring-new/raw results/finite-ring-new/O3 results/finite-ring-new/main results/finite-ring-new/audit
python research/finite-ring-evaluation/report.py results/finite-ring-new/main results/finite-ring-new/runtime results/finite-ring-new/audit results/finite-ring-new/controls results/finite-ring-new/report
```

測定中に別の重い処理を並列実行しない。全ハッシュの入力は以前と同じ531個であり、新たな独立コーパスと数えない。WABTによる別実行器の確認は1入力×10版だけでありNodeの検査範囲と混同しない。

初期のO3-v1/raw-v2は入力bit抽出の未対応で停止した。main-v1のtrap時memory snapshotにはviewを使う不備があり、修正したmain-v2を主結果とする。これらの不成功記録は保持し、解析耐性や検査成功に加算しない。
