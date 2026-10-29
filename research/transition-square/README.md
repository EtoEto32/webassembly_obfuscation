# 遷移二乗を使う双模倣評価：実装と反証

2026-10-23。**主特許候補には不採用。** 別の計算問題で実行する仮説を実Wasmへ実装し、最適化後を含む全24条件を公開binaryだけから解除した。近接する回路還元・行列関数は既知で、独立した新規性は未確立。[設計](algorithm.md)、[先行技術との比較](prior-art.md)、[実測](../../results/invention-20261023/transition-square-report-v1/report.md)。

正54条件106,488呼出しで不一致0。単純なP^2への置換は負12条件すべてで誤答した。追加の682小graph・32,916partition比較、24件の式レベルSMT同値、別WABT162呼出しを検査した。全入力に対する変換器の形式検証を完了したとは主張しない。

二乗版は同じgraph評価器のbaseより約26–37%速いが、元のBoolean式比約811–8,643倍。回復は全体約0.25–0.40秒で、行列逆算部分約4–115ms。これらの回復時間は各条件1回の診断値。回復出力はBDDから作った等価コードであり、元のbyte完全再現率ではない。

## 再現

Python3.9+、Node24.15.0、WABT1.0.42、Binaryen133。監査はZ3 4.13.3を.tools/encoding-synthesis-pythonから読む。共通parser/tool helperはresearch/isotope-swizzle/prototype.pyとresearch/connectivity-elimination/prototype.py。出力先は存在しない名前を指定する。

```powershell
python research/transition-square/run.py results/square-main
python research/transition-square/audit.py results/square-main results/square-audit
python research/transition-square/performance.py results/square-main results/square-runtime
python research/transition-square/rounds.py results/square-main results/square-rounds
python research/transition-square/report.py results/square-main results/square-audit results/square-runtime results/square-rounds results/square-report
```

単体CLIは `prototype.py transform input.wasm output.wasm --mode base|square --seed 213071`、解除は `prototype.py recover input.wasm recovered.wasm`。公開profileは単一のpure Boolean式のみ。一般のWasm全機能を処理する変換器ではない。

v1はBinaryenのbulk-memory flag不足で中断、v2は正当性一致したがO3のprofile検査が未対応、v3は正規化を双方のbyte固定点まで行う修正で全例を回復した。これらを3つの発明や独立した正当性標本とは数えない。
