# 共同多項式更新候補：実装・測定・反証

2026-10-18。**特許の主案には不採用**。4個のi32状態を混合し、非線形更新を展開してi32x4で共同計算する試作。元の更新則の回復計算には追加費用が生じたが、明示的な復号方式との比較では追加の解析負担を確認できず、中心構成には近い先行技術がある。回復成功そのものを棄却理由にはしていない。

[事前仮説](plan.md)、[設計・結果](analysis.md)、[文献と公報の照合](prior-art.md)、[日本語論文ノート](paper-note.md)。研究全体の新規で有効な発明・特許性の確立は未達。

## 実装範囲

実際の `.wasm` を入力し、別の `.wasm` を生成する。入力は、同梱生成器と同じASTを持つ、4状態・次数2以下・ゼロ初期状態の整数多項式スキャナに限定する。入力byte列を1回ずつ前向きに読む `run(p:i32,n:i32)->i32`、1ページ固定memory、出力は状態の第0成分。演算はmod 2^32。

任意のC/Rust製Wasmの変換器ではない。追加関数、import、store、共有memory、memory.grow、例外、GC、浮動小数、非多項式演算には対応しない。memoryへのアクセス順・アドレスを変更せず、追加memoryを確保しない。復元器も、この生成系とBinaryen O2/O3の対応形に限定する。

## 再現

リポジトリルートのPowerShellから実行する。Python 3.9以降、Node.js、WABT、Binaryenが必要。外部Pythonパッケージは不要。測定環境はWindows、Python 3.9.0、Node 24.15.0 / V8 13.6、WABT 1.0.42、Binaryen 133、Intel Core i9-11900K。

ツール配置は既存共通コードに従い `.tools/wabt-1.0.42/bin` と `.tools/binaryen-version_133/bin`。再現先は存在しないディレクトリを指定する。

```powershell
python research/polynomial-carrier/run.py results/invention-20261018/carrier-local-reproduction --compare results/invention-20261018/carrier-wasm-v3
python research/polynomial-carrier/study.py results/invention-20261018/carrier-local-study.json
python research/polynomial-carrier/audit.py results/invention-20261018/carrier-local-audit.json
```

単独CLI。出力の `.wasm` と同名の `.wat` が既存なら上書きしない。

```powershell
python research/polynomial-carrier/prototype.py transform results/invention-20261018/carrier-wasm-v3/shift_product.plain.raw.wasm results/invention-20261018/carrier-example.wasm --mode fused --seed 17
python research/polynomial-carrier/prototype.py recover results/invention-20261018/carrier-example.wasm results/invention-20261018/carrier-example-recovered.wasm
```

`identity` は同じSIMD生成器の無混合対照、`decode` は明示的な復号・元更新・再符号化、`fused` は展開した共同更新。`recover` はバイナリから係数と出力形式を抽出し、元ソース、seed、生成時の行列、モデルJSONを読まない。成功時には検証可能な復元バイナリを出力する。

## 保存した証拠

- [主実験v3](../../results/invention-20261018/carrier-wasm-v3/manifest.json)：36主条件と36回復バイナリ。
- [差分検証](../../results/invention-20261018/carrier-wasm-v3/checks.json)：75,024呼出し、19,728 trap、値・trap有無・64KiB memory比較の不一致0。
- [WABT実行](../../results/invention-20261018/carrier-wasm-v3/interpreter.json)：288呼出し、不一致0。Binaryenは最適化に使用し、この候補の実行検証には使っていない。
- [解析記録](../../results/invention-20261018/carrier-wasm-v3/analysis.json)、[性能](../../results/invention-20261018/carrier-wasm-v3/summary.json)、[変換時間](../../results/invention-20261018/carrier-wasm-v3/transforms.json)、[環境・ソースhash](../../results/invention-20261018/carrier-wasm-v3/environment.json)。
- [一括再実行](../../results/invention-20261018/carrier-wasm-replay-v4/replay.json)：72バイナリのbyte一致を検査。時間値の一致は要求しない。
- [追加24基底×3モデル](../../results/invention-20261018/carrier-study-v1.json)：72/72で回復。追加Wasm件数には数えない。

v1では線形逆像解析だけを試し、coupledで結論が出なかった。v2で既知因子解析を追加し35/36を回復、未変換のcoupled O3だけテキスト抽出未対応だった。v3ではWAT上の一時スタック値を正しく扱い36/36へ修正した。この未対応を保護効果として集計しない。古いログは残すが主結果には使わない。
