# 隣接cellの重複符号化：実装と反証

2026-10-19。実際のcore Wasmを変換し、隣接pairを持つ符号化表と、公開binaryのみを使う回復器を実装した。主・追加120条件、754,992呼出しで不一致0。独立VMで1,197照合、180本の再生成byte一致。独立cell表に対する解析本体の費用増加は確認したが、偽値・再符号化の追加効果と独立した新規性は未確認で、**主特許候補には未採用**。

[方式・攻撃モデルと意味保存](algorithm.md)、[先行研究](prior-art.md)、[評価・限界](analysis.md)、[論文追補](paper-note.md)、[計測修正](revision-1.md)、[事前計画](plan.md)を参照。汎用プログラム変換器ではなく、4値cellの純粋な更新計算profileが対象。

## 環境とソース

Python3.9.0、Node24.15.0、WABT1.0.42を`.tools/wabt-1.0.42/bin`、Binaryen133を`.tools/binaryen-version_133/bin`に置く。追加Python/npm依存はない。共通readerの`research/isotope-swizzle/prototype.py`と`research/connectivity-elimination/prototype.py`も必要なのでリポジトリ一式を用いる。ツールはそれぞれの公式releaseを同じ版で用意する。

- `prototype.py`：入力profile検査、表生成、bit由来reader、supportによる回復、CLI。
- `run.py`, `check.cjs`：主/小規模の生成、差分・oracle・負例・拒否対照。
- `verify.py`：Python oracleとBinaryen wasm-shellで別実行器による検査。
- `performance.py`, `bench.cjs`：内部loopのruntime・memoryと解析時間。
- `report.py`, `replay.py`, `audit.py`：集計・byte再現・証拠監査。

## 再現

リポジトリrootから実行する。生成スクリプトの出力directoryは新しい名前を指定する。

```powershell
python research/overlap-cells/run.py results/overlap-cells-reproduce
python research/overlap-cells/run.py results/overlap-cells-small-reproduce --small
python research/overlap-cells/verify.py results/overlap-cells-reproduce results/overlap-cells-verify-reproduce
python research/overlap-cells/performance.py results/overlap-cells-reproduce results/overlap-cells-performance-reproduce
python research/overlap-cells/report.py results/overlap-cells-reproduce results/overlap-cells-performance-reproduce results/overlap-cells-report-reproduce
python research/overlap-cells/replay.py results/overlap-cells-reproduce results/overlap-cells-replay-reproduce
```

単独変換と回復は次のCLI。sourceには[algorithm.md](algorithm.md)のprofileが必要。

```powershell
python research/overlap-cells/prototype.py transform source.wasm protected.wasm --mode pair-recode --seed 37
python research/overlap-cells/prototype.py recover protected.wasm recovered.wasm
```

主結果は`results/invention-20261019/overlap-cells-v1`、小規模は`overlap-cells-controls-v1`、別VMは`overlap-cells-verify-v1`、再現は`overlap-cells-replay-v1`。性能は`overlap-cells-performance-v2`、比較は[report-v2](../../results/invention-20261019/overlap-cells-report-v2/table.md)が最終。v2のruntimeは同一binaryを確認したv1の再利用であり、解析のみ再測定した。v1の過大な解析費用を最終結果には使わない。監査は`python research/overlap-cells/audit.py results/新しい監査directory`で既定の保存済み証拠を照合する。
