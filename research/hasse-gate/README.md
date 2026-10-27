# Hasse係数回路への変換の早期反証

2026-10-21。微分・係数計算を使う別方向を、実Wasm変換器と解析器へ実装した。
**実行は正しいが、既知の係数算術から独立した新規性は弱く、主発明には採用しない。**
以前の有限環残差フィードバック方式の限定した構成的提案は保持する。

[事前計画](plan.md)、[アルゴリズムと意味保存](algorithm.md)、[先行研究の読取範囲](prior-art.md)。

## 実測

- 4合成式、次数3/6/12/31と取得係数1/2/4/16。source/jet×raw/O3の16本と、その回復16本。
- 各1,280入力（端点の256組＋乱数1,024組）、計40,960呼出しで独立BigInt参照と不一致0。
- バイナリだけを渡した解析は16/16で係数表を回復。うち変換版8/8。unsupported/crash/timeout/解析失敗は0。
- 回復目標は元の多項式の係数とHorner実装。元DAG・因数分解の回復ではない。
- WABTによる別実行器128 probe、元・変換・O3・回復の32本byte再生成が一致。
- 4拒否対照、同じ零関数の異なる形式微分という反例3,840呼出しと、小幅1..12の8,190入力を保存。
- O3で36 fresh Node process、各65,536回warmup、目標5msの9 batch、3 process/条件。
  実行中央値のjet/source比は約1.14/1.79/2.15/9.57。
  正規化本体の中央値比は約1.63/3.73/4.08/32.84で、解析費用の増加は存在する。
- Horner回復版は全4例でjet版より遅い。今回の解析は高速な複製まで達成していない。
- O3サイズは59→81、61→127、63→202、131→1,479 bytes。
  変換37.85–47.93ms（各1回、WABT読取/生成/validate込み、O3別）。
  追加linear memoryなし。Node全体のmaxRSSは35,724–36,172KiBで、Wasm固有の使用量ではない。

[比較表](../../results/invention-20261021/hasse-gate-report-v1/comparison.md)、
[集計JSON](../../results/invention-20261021/hasse-gate-report-v1/report.json)、
[生の照合](../../results/invention-20261021/hasse-gate-v1/checks.json)、
[生の性能](../../results/invention-20261021/hasse-gate-runtime-v1/runtime.json)、
[再生成・別実行器](../../results/invention-20261021/hasse-gate-audit-v1/audit.json)。

解析読取は1回、本体は同一process内11反復。人間の解析器開発時間を含めない。
実行は共通Wasm loop内の入力更新・呼出し・checksumを含み、コンパイルを除外する。
短い式では測定ばらつきがあり、全processの中央値と範囲をJSONへ保存した。
CPU固定・周波数固定なし。汎用ベンチマーク・実アプリ・別CPUでの優位性は未検証。

## 判定と次の制約

斉次式Fでは、係数化の結果が単に二項係数×Fになる。中間ノードにも同じ恒等式が成立する。
通常O3が全機構を消したわけではないが、一般の疎多項式評価で係数表へ戻る。
解析費用が増えたことは認める一方、既存の係数計算を膨らませる機構との技術差が乏しい。
この結果を「新原理を発明した」「特許が取れる」「どの解析も容易」とは説明しない。
次数やjetの幅を増やすだけの再試行は行わない。原理の異なる有望な主発明の確立は未達。

## 再現

Python3.9、Node24.15/V8 13.6、`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin`。
追加package不要。共通parser/helperは`research/isotope-swizzle`と`research/connectivity-elimination`。
実験スナップショットと入力hashを結果に保存。出力先は未作成の名前を指定する。

```powershell
python research/hasse-gate/run.py results/hasse-new
python research/hasse-gate/performance.py results/hasse-new results/hasse-runtime-new
python research/hasse-gate/audit.py results/hasse-new results/hasse-audit-new
python research/hasse-gate/report.py results/hasse-new results/hasse-runtime-new results/hasse-audit-new results/hasse-report-new
```

単体CLI：

```powershell
python research/hasse-gate/prototype.py transform source.wasm jet.wasm --order 2
python research/hasse-gate/prototype.py recover jet.wasm recovered.wasm
```

対応範囲はalgorithm.md参照。任意のWasmを受理する汎用難読化器ではない。
正当性の実行テストだけで全入力の形式検証が済んだとはしない。
