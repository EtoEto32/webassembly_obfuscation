# 異なる論理時刻を持つSIMDレーン：実装と反証

逐次cascadeの段ごとに実行時刻をずらし、異なる論理反復の状態を一つのWasm SIMD命令へ詰める試作。72条件の正当性検査は通過した。一方、段順と更新則を全36変換条件から回復でき、レーン混在の追加保護効果も確認できなかった。既知のretiming・software pipelining・SLPに対する独立した新規性が弱く、主特許候補には採用しない。

- [実装前の仮説](plan.md)
- [アルゴリズムと意味保存条件](algorithm.md)
- [実測・アブレーション・失敗原因](analysis.md)
- [先行論文・特許との比較](prior-art.md)
- [論文草稿への追補](paper-note.md)
- [主結果](../../results/invention-20261019/temporal-lanes-v4/summary.json)
- [位相値を使わない回復](../../results/invention-20261019/temporal-lanes-graph-v1/summary.json)
- [再現監査](../../results/invention-20261019/temporal-lanes-audit-v1/summary.json)

## 環境と再現

リポジトリのルートから実行する。Python 3.9.0、Node 24.15.0 / V8 13.6.233.17-node.48、Windows 10.0.26100、Intel Core i9-11900Kを使用。外部Pythonパッケージは不要。WABT 1.0.42を`.tools/wabt-1.0.42/bin`、Binaryen 133を`.tools/binaryen-version_133/bin`へ置く。共有のWAT読込みに`research/isotope-swizzle/prototype.py`と`research/connectivity-elimination/prototype.py`を使用し、依存ソースもsnapshotへ保存する。

各出力先は未存在のディレクトリを指定する。次は保存済み結果を上書きしない実行例。

```powershell
python research/temporal-lanes/run.py results/temporal-local
python research/temporal-lanes/verify.py results/temporal-local results/temporal-local-verify
python research/temporal-lanes/model.py results/temporal-local-model
python research/temporal-lanes/performance.py results/temporal-local results/temporal-local-performance
python research/temporal-lanes/report.py results/temporal-local results/temporal-local-performance results/temporal-local-report
python research/temporal-lanes/phase_graph.py results/temporal-local results/temporal-local-graph
python research/temporal-lanes/run.py results/temporal-local-replay
python research/temporal-lanes/audit.py results/temporal-local results/temporal-local-replay results/temporal-local-performance results/temporal-local-verify results/temporal-local-model results/temporal-local-report results/temporal-local-graph results/temporal-local-audit
```

性能測定中は他の重い処理を同時実行しない。タイミングはホスト依存であり、hash再現の対象ではない。監査は216本の対象・観測・回復バイナリの一致、差分結果、負例、測定手順、checksum、source snapshot、回復結果、リンクを検査する。`run.py --small`は試作確認用で、72条件を前提とする監査には渡さない。

変換CLIは実際の`.wasm`を読み込む。ただし[限定profile](algorithm.md)のみを受理する。

```powershell
python research/temporal-lanes/prototype.py transform results/temporal-local/n8-k1-source.wasm results/temporal-custom.wasm --mode mixed --seed 37
python research/temporal-lanes/prototype.py recover results/temporal-custom.wasm results/temporal-recovered.wasm
```

主正当性系列は`temporal-lanes-v4`。性能は`performance-v1`、別実行器は`verify-v1`、縮小モデルは`model-v1`、追加解析は`graph-v1`を参照する。途中中断のv1/v3と、後の検査強化前のv2は削除せず[分析](analysis.md)に区別して記録した。これらを独立した試行数へ足し合わせない。
