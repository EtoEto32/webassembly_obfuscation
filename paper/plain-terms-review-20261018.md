# 日本語・用語の推敲（2026-10-18）

対象: main.tex と図1の日本語ラベル。
情報工学を専門としない読者が追える説明を目指し、である調を維持した。

## 主な変更
- 「実効入力」を「実際に読み込まれる入力」、「計数用の版」を「実行回数を数えるための版」に変更。
- 「構文から作った指紋」は命令列・変数宣言などの構文情報を完全一致で比較する説明に変更。
- 「シグネチャ」は「引数・戻り値の型」、「由来名」は採点用に元の関数を示す名前として説明。
- 「局所規則」「局所最適化パス」「有限入力」「受理出力」などの読みにくい表現を具体化。
- LLVM中間表現、WAT、ホスト側、ウォームアップ、XOR、定数畳み込み、副作用、インライン化などを説明。
- ファイル内の命令数と実行回数を区別。表のコード比にはコードサイズの比であることを明記。
- 図のNOPをnop挿入に統一し、95%区間を95%信頼区間に変更。測定値・集計方法は変更していない。
- 説明追加に伴い、同じ結果・設計方針の繰り返しを整理した。8ページを維持。

## 用語を確認した一次資料
- MDN「シグネチャ (関数)」: https://developer.mozilla.org/ja/docs/Glossary/Signature/Function
- MDN「WebAssembly の概要」: https://developer.mozilla.org/ja/docs/WebAssembly/Guides/Concepts
- MDN「WebAssembly テキスト形式の理解」: https://developer.mozilla.org/ja/docs/WebAssembly/Guides/Understanding_the_text_format
- V8「WebAssembly compilation pipeline」: https://v8.dev/docs/wasm-compilation-pipeline
- Microsoft「コンパイラの最適化についてすべてのプログラマが知っておくべきこと」: https://learn.microsoft.com/ja-jp/archive/msdn-magazine/2015/february/compilers-what-every-programmer-should-know-about-compiler-optimizations

「定数畳み込み」など一般に使われる専門用語は残し、短く説明した。
現行ドキュメントの起動オプションを実験時の条件に置き換えることはしていない。

## 確認結果
- 参考文献を含め8ページ。既存のクラス、余白、文字サイズを維持。
- 表の数値セル、主要な測定値、別行数式、引用キー・ラベル・参照、タイトル・著者・所属、英文要旨の一致を確認。
- 主張の適用範囲を維持。限られた入力での出力一致、共通コードに由来する既知の関数での照合、統計的な結論を出さないこと、自動難読化解除や検知改善の未達を残した。
- yomiyasu_lint.py: 指摘なし。意味の差分を確認し、対象や断定の強さを保持。
- 既存build.ps1（pLaTeX / pBibTeX / dvipdfmx）でコンパイル成功。Overfull、LaTeX Warningなし。
- 内蔵の単一ファイル用コンパイラではipsj.clsが不足するため失敗。上記ローカル環境で最終PDFを生成した。
- 最終PDFの全8ページを画像で確認。図表のはみ出し・重なりなし。
- 実験・マイニング処理の再実行なし。図の再生成には既存の測定集計ファイルを使用。
- 修正前のmain.tex、main.pdf、図1のPNG/SVGはrevisions/before-plain-terms-20261018/に保存。
