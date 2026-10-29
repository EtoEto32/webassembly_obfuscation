# 位置依存表現のコピー後補正：実装・比較

2026-10-21。privateなbyteメモリを位置に依存して符号化し、標準memory.copyの後に移動先だけを補正する変換を実装した。**正当性とコードサイズの利点は確認したが、直接SIMDコピーに対する速度改善はなく、主発明には採用しない。** この結果は10月12日に限定採用した[有限環残差方式](../../experiments/sha256-fixedpoint/research-checkpoint-ja.md)を撤回するものではない。

- [規則・意味保存条件・攻撃モデル](algorithm.md)
- [先行技術の読解範囲と比較](prior-art.md)
- [評価と採否](analysis.md)
- [測定前の計画](plan.md)・[変更と失敗履歴](revision.md)
- [全条件の比較表](../../results/invention-20261021/bulk-rebase-report-v1/comparison.md)

## 再現

Python3.9.0、Node24.15.0/V8 13.6、WABT1.0.42、Binaryen133。Windows、Intel Core i9-11900Kの単一環境。WABTは`.tools/wabt-1.0.42/bin`、Binaryenは`.tools/binaryen-version_133/bin`に置く。Python/npmの追加packageなし。共通readerは`research/isotope-swizzle/prototype.py`と`research/connectivity-elimination/prototype.py`。rootから、存在しない出力先を指定する。

```powershell
python research/bulk-rebase/run.py results/bulk-main
python research/bulk-rebase/controls.py results/bulk-main results/bulk-controls
python research/bulk-rebase/verify.py results/bulk-main results/bulk-verify
python research/bulk-rebase/recover.py results/bulk-main results/bulk-recovery
python research/bulk-rebase/benchmark.py results/bulk-main results/bulk-runtime
python research/bulk-rebase/report.py results/bulk-main results/bulk-runtime results/bulk-recovery results/bulk-controls results/bulk-verify results/bulk-report
```

性能測定中は他の重い処理を同時に実行しない。benchmarkは6方式×3長さ×3配置×5processを順番に実行し、途中結果も保存する。reportは保存値を集計し、44本を再生成してbyte同一性を検査し、同じcompiler設定の診断とソースsnapshotを保存する。性能値の同一再現を要求するものではない。

単独変換：

```powershell
python research/bulk-rebase/prototype.py source.wasm transformed.wasm --mode bulk-simd --seed 7
```

入力の制限はalgorithm.md参照。二つのmemoryサイズを持つ同系統fixtureであり、複数の独立した実アプリ評価ではない。主結果は`bulk-rebase-v2`、対照は`bulk-rebase-controls-v2`。v1の正当性結果と対照の未完了試行も保持している。

## 実測の要点

44target、34,144呼出し、11,220メモリ状態照合、2,640期待trapで不一致0。byte照合総数約11億は反復した全memory比較の合計であり、11億の独立入力ではない。別実行器WABTでは12target・120呼出し（48trap）が一致。小モデル112,130件、4誤変換の検出、7CLI拒否と1shared profile拒否を保存した。

方式既知の解析は各target31問い合わせで等価decoderを学習し、全44targetの操作後memoryを復号した。学習に生成seed・P・Kを渡していない。追加の各4,096書込み照合は学習後の検証であり、学習問い合わせへ混ぜていない。

主要270 fresh processでは、コピー後補正SIMD/直接SIMDの中央値比は1.000–1.752。9条件中8条件で後補正が遅く、process中央値の範囲も分離。残る4KiB前進は同程度で範囲が重なる。O3 binaryは直接SIMD 1,509 bytesに対し後補正1,155 bytes、354 bytes（約23.5%）小さい。線形memory増加なし。サイズと時間のトレードオフを示す実装成果として保持する。
