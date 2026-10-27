# Relaxed SIMD の選択を運ぶ内部表現：反証実験

2026-10-19。通常の最適化に残ることは確認したが、方式既知の解析に対する入力依存mask以上の効果を支持しない。**特許の主発明として採用しない。研究全体は未完了。** 既知の Boolean masking の mask生成部を置き換えた限定案なので、独創的な候補の追加数にも数えない。

実際の `.wasm` を読む変換器、対照、回復器を実装した。主36条件と回復・精密化12条件の48本について Node 249,456呼出し、別エンジン WABT 288呼出しで不一致0。別出力への再実行で48本のバイト一致を確認。適応的解析と収束最適化の追加54本では280,638呼出し、WABT324呼出しで不一致0。これらは生成ファイル数であり、内容が異なるバイナリの種類数ではない。

境界・ランダムテストだけで全入力同値性を証明したとはしない。[意味保存の条件と導出](algorithm.md)、[先行技術と読了範囲](prior-art.md)、[実測・判断](analysis.md)、[日本語論文追補](paper-note.md)を参照。

## 再現

リポジトリのルートから実行する。Python 3.9以上、Node 24.15.0、`.tools/wabt-1.0.42/bin`、`.tools/binaryen-version_133/bin` を使用。Windowsの `.exe` を想定する。別の配置では `WASM_TOOLS_ROOT` を指定する。ネットワーク・課金・外部公開は不要。

```powershell
python research/relaxed-carrier/run.py results/relaxed-reproduction
python research/relaxed-carrier/verify.py results/relaxed-reproduction results/relaxed-verification
python research/relaxed-carrier/compare.py results/relaxed-reproduction results/relaxed-comparison
python research/relaxed-carrier/verify.py results/relaxed-comparison results/relaxed-comparison-verification
```

出力先は存在しないディレクトリを指定する。再現のバイト比較には `run.py NEW --compare OLD` を使う。測定中に他の重い処理を並行実行しない。

個別変換と範囲検査付き回復：

```powershell
python research/relaxed-carrier/prototype.py transform input.wasm output.wasm --mode relaxed
python research/relaxed-carrier/prototype.py recover output.wasm recovered.wasm
```

対象は、3個のi32引数を取る単一のexport `run`、i32戻り値、純粋な直線式とlocal.set。AND/OR/XOR、定数rotate/shiftを扱う。memory/import/call/branch/div/float等は拒否する。任意のアプリを処理できる難読化製品ではない。回復器は**このmask独立性が成り立つ生成系列**への条件付き攻撃であり、任意のWasmについて同値性を検証するツールではない。

主結果：[v2](../../results/invention-20261019/relaxed-carrier-v2/summary.json)、[正当性](../../results/invention-20261019/relaxed-carrier-v2/correctness.json)、[再現](../../results/invention-20261019/relaxed-carrier-v2/replay.json)、[追加比較](../../results/invention-20261019/relaxed-compare-v2/analysis.json)、[対照](../../results/invention-20261019/relaxed-verify-v1/controls.json)。v1も保存し、v2は同じ主実装の再実行。追加比較v1の範囲解析だけの時間差を最終結論には使わず、v2では共通の系列特化解析を加えた。
