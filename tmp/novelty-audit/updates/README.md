# Wasm Structured Encoding — 既存符号化の適用試作

**Wasmの分岐合流点・ループ境界で、複数の整数値の表現を切り替える難読化候補**です。
作業名は「構造化境界での状態再符号化」。既存研究に存在しないと確定した方式ではありません。
**2026-10-11の新規性監査：現状を新アルゴリズムとして採用しません。**
2006年の多変数符号化と2007年の領域別符号化・境界変換合成に直接の先行例がありました。
追加実験でも、対象42本の固定制御条件下の入出力式は各3回の問い合わせで再構成できました。
根拠・適用条件・限界は [新規性監査](docs/novelty-audit.md) に記録しています。

通常の2整数を混ぜ合わせて別の2整数として保持し、領域ごとに異なる表現へ変換します。
Wasmのmulti-value block/if/loopが値の組を受け渡す仕組みを利用します。
単にNOPを増やす方式ではなく、値同士の対応を複数領域にまたがらせる設計候補です。
ただし、アフィン符号化自体は既知であり、この試作を新アルゴリズムの完成とは扱いません。

## ファイルの入口

| ファイル | 内容 |
|---|---|
| `docs/novelty-audit.md` | 先行研究の該当節、棄却判断、42本の追加解析結果 |
| `docs/novelty-search-log.md` | 検索語、確認範囲、アクセスできなかった資料 |
| `tests/affine-recovery.cjs` | ソース・符号化情報を読まない入出力式の推定 |
| `artifacts/affine-recovery.json` | 1,344条件の推定係数・検証結果・SHA-256 |
| `docs/design.md` | 数式、Wasmの合流・戻り先の処理、意味が保存される条件、弱点 |
| `docs/related-work.md` | 一次資料との比較、新規性を判断するための未確認点 |
| `docs/experiment-report.md` | 実際に行った検証とサイズ比較 |
| `examples/boundary-demo.wat` | 1境界だけを説明する短いWATサンプル |
| `examples/programs.json` | 3種類の通常整数計算。基準となる処理の定義 |
| `src/prototype.py` | 制限したプログラム定義から基準版・符号化版を生成 |
| `tests/verify.cjs` | 生成器と別のJavaScript計算による出力照合 |
| `artifacts/manifest.json` | ツール版、設定、各バイナリのSHAとサイズ |
| `artifacts/verification.json` | 実行した比較件数と結果 |

## 動かし方

Python 3.10以降、Node.js、WABTが必要です。O2比較にはBinaryenも使います。
Python/Nodeの外部パッケージは不要です。依存実行ファイルの場所は引数で渡します。

```powershell
python src/prototype.py --wabt-bin C:/path/to/wabt/bin --wasm-opt C:/path/to/wasm-opt.exe
node tests/verify.cjs
```

O2比較を省く場合は `--wasm-opt` を省略します。
生成は `artifacts/` を更新するので、別の試行は `--out artifacts-new` を指定し、
`node tests/verify.cjs artifacts-new` で照合してください。

短い説明用サンプルは次でコンパイルできます。

```powershell
wat2wasm examples/boundary-demo.wat -o artifacts/boundary-demo.wasm
```

`step(2,3)` の結果は `[5,4]` です。詳しい検証結果は実験報告を参照してください。

## 今回の範囲

入力は小さな専用定義で、既存の任意Wasmを読み込んで難読化するツールではありません。
対象はi32の加算・定数倍と、条件分岐・最大15回のループを持つ純粋な2値計算です。
メモリ、import、採掘、ネットワーク処理は含みません。
新アルゴリズムとしての新規性は支持できません。今回の限定的な入出力解析への問い合わせ数の増加もありません。
一般の解析耐性・実行性能の優位性は未評価です。過去のmanifestにある `novelty: unverified` は生成時の記録として保持しています。
従来の採掘研究・原稿とは別の研究リポジトリとして管理します。
