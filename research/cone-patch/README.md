# 可逆混合レコードの局所更新：実装と反証

read/write依存を区別して、Wasmの符号化レコード更新に不要な前後処理を除く試作。局所更新は高速化できたが、配布バイナリから全36条件のメモリ状態を回復でき、独立した新規性も未確認。特許候補として成立したとは扱わない。

- [実装前の仮説](plan.md)
- [アルゴリズム・対象範囲・意味保存条件](algorithm.md)
- [先行論文・特許との比較](prior-art.md)
- [実測・アブレーション・失敗原因](analysis.md)
- [論文草稿への追補](paper-note.md)
- [主結果](../../results/invention-20261019/cone-patch-v1/summary.json)
- [再現監査](../../results/invention-20261019/cone-patch-audit-v1/summary.json)

## 環境と実行

リポジトリのルートから実行する。Python3.9以上とNode24.15.0を使用。外部Pythonパッケージは不要。WABT1.0.42を`.tools/wabt-1.0.42/bin`、Binaryen133を`.tools/binaryen-version_133/bin`に置く。共有のWAT読込み/ツール呼出しに`research/isotope-swizzle/prototype.py`と`research/connectivity-elimination/prototype.py`を使用する。実行環境と依存ソースのhashを結果へ保存する。

各outputは未存在のディレクトリにする。次は保存済み結果を上書きしない新しい実行例。

```powershell
python research/cone-patch/run.py results/cone-patch-local
python research/cone-patch/verify.py results/cone-patch-local results/cone-patch-local-verify
python research/cone-patch/model.py results/cone-patch-local-model
python research/cone-patch/exposure.py results/cone-patch-local results/cone-patch-local-exposure
python research/cone-patch/performance.py results/cone-patch-local results/cone-patch-local-performance
python research/cone-patch/report.py results/cone-patch-local results/cone-patch-local-performance results/cone-patch-local-exposure results/cone-patch-local-report
python research/cone-patch/run.py results/cone-patch-local-replay
python research/cone-patch/audit.py results/cone-patch-local results/cone-patch-local-replay results/cone-patch-local-performance results/cone-patch-local-verify results/cone-patch-local-model results/cone-patch-local-exposure results/cone-patch-local-report results/cone-patch-local-audit
```

性能測定中は他の重い作業を同時実行しない。性能値はホスト依存であり、hash再現の対象ではない。監査は出力バイナリの一致、返り値/trap/メモリ検査結果、負例、測定手順、checksum、ソースsnapshotとリンクを検査する。`run.py --small`はprobe用で、48条件を前提とする監査の入力には使わない。

変換CLIは実際の`.wasm`を入力にする。対象は[限定profile](algorithm.md)であり、任意のC/C++プログラムを受理するものではない。

```powershell
python research/cone-patch/prototype.py transform results/cone-patch-local/n32-source.wasm results/cone-patch-custom.wasm --chunks 32 --records 4 --depth 6 --seed 29 --mode patch
python research/cone-patch/prototype.py extract results/cone-patch-custom.wasm
```

保存結果では`cone-patch-v1`が主正当性系列、`performance-v2`と`report-v2`が主性能系列。初期probe-v1の負例不足とperformance-v1の短い測定も削除せず記録した。トラップした負例や未対応を保護効果に数えない。
