# 入力依存レーン移送：Wasm SIMD変換と適応的解析

2026-10-19。異なる4つの仮入力を同時に計算し、正しい結果のレーンを入力と節点に応じて動かす限定変換を実装した。通常O3では残るが、出力からの需要をmod4で追う解析は元のscalar計算へ戻せた。独立した新規性と十分な追加効果を確立できず、主発明には採用しない。研究全体の完了や特許性の確立を意味しない。

[設計・疑似コード・失敗の補題](algorithm.md)、[先行技術](prior-art.md)、[実測](analysis.md)、[日本語草稿](paper-note.md)、[事前ゲート](plan.md)。主56binary・240,128呼出し、別エンジン336呼出し、ランダム式60binary・257,280呼出しが一致。24回復式のscalarモデルはZ3で元の式と同値。全Wasm実装の形式証明とは区別する。

## 実行

Python3.9以上、Node24.15.0、WABT1.0.42、Binaryen133を使用。Windows `.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`が既定で、別配置は共通helperの`WASM_TOOLS_ROOT`を使う。`prove.py`のみ既存の`.tools/encoding-synthesis-python`にあるz3-solver4.13.3を使用する。ソースは`output-recurrence/prototype.py`と`connectivity-elimination/prototype.py`のWABT helperを再利用する。

```powershell
python research/lane-demand/run.py results/lane-reproduction
python research/lane-demand/verify.py results/lane-reproduction results/lane-verification
python research/lane-demand/prove.py results/lane-reproduction results/lane-proof
```

出力先は新しいディレクトリにする。`run.py NEW --compare OLD`で全binaryのbyte再現を照合する。性能測定は重い処理と並行実行しない。

```powershell
python research/lane-demand/prototype.py source.wasm transformed.wasm --mode dynamic
python research/lane-demand/attack.py transformed.wasm recovered.wasm
```

対象は単一のpure i32関数に限定する。trap、副作用、任意CFG、一般Wasmの型回復器ではない。命令単位の解析であり、元のsourceやgenerator対応表を回復器へ渡さない。

`report.py`は保存したv3の数値から本文を生成する。初期の未対応・解析器bug・DAG修正は実測文書に分離した。外部公開、push、出願は行っていない。

[保存成果物の監査](../../results/invention-20261019/lane-demand-final-audit-v1.json)はbinaryのhash・再現、実行時ソース、集計値、SMT記録、O3後のswizzle残存、文書リンクを確認する。`python research/lane-demand/audit.py results/lane-audit.json`で再実行できる。性能測定は再実行しない。
