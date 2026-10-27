# 零長による副作用の述語化：実Wasmの反証ゲート

2026-10-19。**追加のlinear memoryを使わず、0ページの場合も含めて条件付き書込みをbulk命令へ変換できた。一方、方式既知の解析は長さから副作用条件を再び露出でき、既知predicationとの差も小さいため、特許の主案には採用しない。** 復元できた事実だけでなく、測定費用と近接先行技術から判断した。

[事前計画](plan.md)、[アルゴリズム・意味保存](algorithm.md)、[先行技術・公報](prior-art.md)、[実測と採否](analysis.md)、[日本語草稿](paper-note.md)。新規で有効な主発明の確立は未達であり、この試作の完了を研究全体の完了とはしない。

入力は実際の `.wasm`。1関数・1非共有memory32・max≤2ページ、runとmemoryのexport、純粋なi32式と条件付きstore8/16/32、fill/copyを扱う。一般のC/Rust出力をそのまま扱うツールではない。sourceのload、div、local更新、外部呼出し等を拒否する。詳細はアルゴリズム資料を参照。

## 再現

ルートから実行する。Python 3.9以上（追加パッケージ不要）、Node.js、WABT1.0.42、Binaryen133。既存配置 `.tools/wabt-1.0.42/bin` と `.tools/binaryen-version_133/bin` を利用する。別配置は `WASM_TOOLS_ROOT` を指定する。存在しない出力ディレクトリを指定する。

```powershell
python research/zero-extent/run.py results/invention-20261019/extent-local --compare results/invention-20261019/extent-wasm-replay-v4
python research/zero-extent/interpreter.py results/invention-20261019/extent-local results/invention-20261019/extent-local-interpreter
python research/zero-extent/controls.py results/invention-20261019/extent-local-controls
python research/zero-extent/audit.py results/invention-20261019/extent-local-audit.json
```

性能測定を含む`run.py`と、interpreter等の負荷の高い処理を同時に走らせない。auditは保存済みの参照実験を監査する。ローカル再現の結果を表示するには、その出力先のchecks/summary/analysis/environmentを読む。

単独CLI:

```powershell
python research/zero-extent/prototype.py transform results/invention-20261019/extent-wasm-replay-v4/wide.plain.raw.wasm results/invention-20261019/extent-example.wasm --mode extent
python research/zero-extent/prototype.py recover results/invention-20261019/extent-example.wasm results/invention-20261019/extent-example-recovered.wasm
```

回復は元のsource構文を一意に再現する処理ではない。零長効果を条件分岐へ、1byte fillをstoreへ、同一宛先copyをbounds検査へ変換する。未対応命令を含む入力は拒否する。

## 保存した証拠

- [主値v4のmanifest](../../results/invention-20261019/extent-wasm-replay-v4/manifest.json)：4モデル×4方式×3最適化=48主条件と48回復バイナリ。
- [正当性](../../results/invention-20261019/extent-wasm-replay-v4/checks.json)：239,616呼出し、177,785 trap、返り値/trap/全memoryの不一致0。0/1/2ページ。
- [解析](../../results/invention-20261019/extent-wasm-replay-v4/analysis.json)、[性能生値](../../results/invention-20261019/extent-wasm-replay-v4/benchmark.json)、[性能集計](../../results/invention-20261019/extent-wasm-replay-v4/summary.json)、[環境とsource hash](../../results/invention-20261019/extent-wasm-replay-v4/environment.json)。
- [再現](../../results/invention-20261019/extent-wasm-replay-v4/replay.json)：v3と96バイナリがbyte一致。
- [WABT別エンジン](../../results/invention-20261019/extent-interpreter-v1/checks.json)：384 writer呼出し・7,296 memory probe呼出し、不一致0。v3を使用し、v4とのbyte一致で対応を確認。
- [負の対照](../../results/invention-20261019/extent-controls-v3/checks.json)：4種類の誤変換を検出。operand評価順の回復器検査21例も一致し、sourceのload/divを拒否。

v1の回復器は範囲伝播が保守的であり、operandのlocal.teeやif合流の扱いをv2で改めた。v1/v2のwide性能入力は常に同じ側を選ぶ設定だったため、v3で3つの分岐頻度条件へ修正。v3測定中に別エンジン検証を走らせたため、性能の主値には同時検証なしで再実行したv4だけを使う。controls-v1はテスト用のinline export表現がnormalizerの入力形式と合わずvalidate前に失敗した履歴であり、成功件数へ入れない。実バイナリを読み直すv2/v3で修正した。
