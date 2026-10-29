# 書込みの失敗境界を保存する被覆：実装と反証

2026-10-18。実Wasmのstore列を、途中のtrap後に残るmemoryまで保存して組み替える試作を実装した。境界横断を優先した方式は、一部で通常の広幅化・同じ書込み数のランダム被覆より解析の処理時間が増えた。しかし、公開APIだけでも2–5回の呼出しで同じ更新を回復できた。**今回の限定方式を特許の主案には採用しない。** 解析成功そのものを不採用理由とはしていない。

[事前仮説](plan.md)、[設計・意味保存・実測](analysis.md)、[先行技術と公報](prior-art.md)、[日本語草稿](paper-note.md)。新規で有効な主発明の確立は未達であり、この反証を研究全体の完了へ読み替えない。

## 実装範囲

入力は実際の `.wasm`。非共有memory32を1個、min=max=1ページ、importなし、関数1個。`run(p:i32, a:i32, ...)->i32` は共通base pと即値offsetの1/2/4byte store列だけを実行し、0を返す。書込み値は引数の下位byte列、offset+width≤256、引数はpを含め2–32個。重なるstoreを扱える。任意のC/Rustプログラム、loadを使う計算、別々のbase、外部呼出し、分岐、共有memory、memory64は対象外。

変換はbyte分割、広幅被覆、フィールド境界横断を優先する被覆、同store数のランダム被覆。元のバイナリを読んで変換し、WABTで再生成・検証する。既存の出力は上書きしない。

## 再現

リポジトリルートから。Python 3.9以降、Node.js、WABT 1.0.42、Binaryen 133を使用。Python追加パッケージ不要。既存ツール配置は `.tools/wabt-1.0.42/bin` と `.tools/binaryen-version_133/bin`、別配置には `WASM_TOOLS_ROOT` を使う。出力先は存在しない名前を指定する。

```powershell
python research/write-frontier/run.py results/invention-20261018/frontier-local-reproduction --compare results/invention-20261018/frontier-wasm-v3
python research/write-frontier/study.py results/invention-20261018/frontier-local-study
python research/write-frontier/io-study.py results/invention-20261018/frontier-local-reproduction results/invention-20261018/frontier-local-io
python research/write-frontier/audit.py results/invention-20261018/frontier-local-audit.json
```

単独CLI。`.wasm` と同名 `.wat` の両方が未作成である必要がある。

```powershell
python research/write-frontier/prototype.py transform results/invention-20261018/frontier-wasm-v3/zigzag.plain.raw.wasm results/invention-20261018/frontier-example.wasm --mode woven1
python research/write-frontier/prototype.py recover results/invention-20261018/frontier-example.wasm results/invention-20261018/frontier-example-recovered.wasm
node research/write-frontier/io-attack.cjs results/invention-20261018/frontier-example.wasm
```

静的回復器は全byteの由来と失敗境界を抽出して簡潔な等価store列を生成する。元ソースや生成ログを受け取らない。公開I/O回復器はWasmをインスタンス化してexportだけを使い、命令列を検査しない。ただし対象が上記の引数byte書込み族であるという事前知識を使う。任意プログラムを数回のI/Oで同定できるとは主張しない。

## 証拠

- [主実験v3](../../results/invention-20261018/frontier-wasm-v3/manifest.json)：4カーネル×6方式×3最適化=72本と、静的回復72本。
- [Node差分検証](../../results/invention-20261018/frontier-wasm-v3/checks.json)：144本、164,196呼出し、70,632 trap、返り値・trap有無・全64KiB memoryの不一致0。
- [WABT別実行](../../results/invention-20261018/frontier-wasm-v3/interpreter.json)：writer 288回、trap後を含むmemory読取り16,128回、不一致0。
- [解析費用](../../results/invention-20261018/frontier-wasm-v3/analysis.json)、[性能](../../results/invention-20261018/frontier-wasm-v3/summary.json)、[環境・ソースhash](../../results/invention-20261018/frontier-wasm-v3/environment.json)。
- [再現v4](../../results/invention-20261018/frontier-wasm-replay-v4/replay.json)：144バイナリのbyte一致。
- [400モデルの132,000比較](../../results/invention-20261018/frontier-study-v1/model-checks.json)、[誤変換2件](../../results/invention-20261018/frontier-study-v1/controls.json)、[入力拒否3件](../../results/invention-20261018/frontier-study-v1/rejections.json)。
- [公開I/O回復v2](../../results/invention-20261018/frontier-io-v2/analysis.json)：72本を計234問い合わせで回復。[72 cloneの82,098呼出し](../../results/invention-20261018/frontier-io-v2/checks.json)で不一致0。主実験と入力が重複するため独立標本数には合算しない。

v1はbit単位の解析と5方式、v2はbyte解析と同store数の対照を追加した。v3では通常被覆も重複を許した最小store数に改善した。旧版の結果を主値に混ぜない。`frontier-io-v1` とv2の差はソースsnapshot追加であり、重複を独立した成功件数には数えない。
