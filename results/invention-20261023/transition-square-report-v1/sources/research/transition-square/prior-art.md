# 最も近い先行技術と今回の判断

調査日2026-10-23。未読の技術内容や実験値を補わない。今回の案は主特許候補に採用しない。

|資料|書誌・閲覧範囲|提案との関係|
|---|---|---|
|[On the Complexity of Computing Probabilistic Bisimilarity](https://www.cs.ox.ac.uk/james.worrell/prob-bisim2.pdf)|Di Chen, Franck van Breugel, James Worrell。FoSSaCS 2012、LNCS7213、437–451、査読会議論文。[DOI 10.1007/978-3-642-28729-9_29](https://doi.org/10.1007/978-3-642-28729-9_29)。著者版の要旨・§2の定義、matching lemma、AND/OR還元を閲覧。後半pseudometricの全論証・実装評価は未再現。|回路の出力を双模倣判定に移す核は既知。本文はP-hardnessの還元を与えるもので、今回の保護性能やWasm実装を評価した論文ではない。|
|[What Is a Matrix Square Root?](https://nhigham.com/2020/05/21/what-is-a-matrix-square-root/)|Nicholas J. Higham、2020-05-21、著者による技術解説、査読論文ではない。本文を閲覧。|主平方根の一意性、primary matrix functionと多項式の関係は既知。今回の意味保存と逆算の基礎である。|
|[Improved MATLAB Function Sqrtm](https://nhigham.com/2016/04/05/improved-matlab-function-sqrtm/)|Nicholas J. Higham、2016-04-05、著者による技術解説。本文とtriangular recurrenceの説明を閲覧。|三角行列の平方根漸化式はBjörck–Hammarling 1983に遡る。今回の解除器はこの種類の既知演算の正確な有理数実装。記事のMATLAB測定値を今回の速度へ転用しない。|
|[An Eigenvector Condition for Markov Chain Lumpability](https://pubsonline.informs.org/doi/10.1287/opre.25.6.1028)|D. R. Barr, M. U. Thomas、Operations Research25(6)、1028–1031、1977、DOI10.1287/opre.25.6.1028。出版社要旨・書誌のみ閲覧。|lumpabilityを線形代数で扱う方向は既知。本文の正確な条件と今回の多項式条件が同一とは確認していない。|
|[On pth roots of stochastic matrices](https://doi.org/10.1016/j.laa.2010.04.007)|Nicholas J. Higham, Lijing Lin、Linear Algebra and its Applications435、448–463、2011。著者解説の参考文献を確認。出版社本文へのredirectは取得不可。|追加の精査対象。内容未読のため今回の構成を既に開示しているとは断定しない。|

WASMixer等の命令置換や制御フロー平坦化とは、プログラムを関係判定へ変換してその遷移行列を合成する点で異なる。しかし、この相違だけで新規性・非自明性は立証されない。既知回路還元、Markov遷移の合成、行列関数という近接技術からの独立した生成原理が弱い。Wasmは今回の実装先であり、同じ原理は他言語でも実行できる。

特許を含む反証検索：`site:patents.google.com obfuscation "transition matrix"`、`site:patents.google.com obfuscation "bisimulation"`、`"program obfuscation" "matrix square"`、`"obfuscation" "lumpability"`。検索結果にはUS12470591B2（attack graph abstraction）、US20130326625A1（分類用Markov特徴）等があったが、今回請求項本文は精査していない。これらを最も近い権利や重複根拠とは認定しない。検索で完全一致が出なかったことを新規性の根拠には使わない。

最大のReject理由は、意味保存を保証する公開可逆行列関数がそのまま効率的解除器を与え、実測でも全24条件を回復できたこと。square評価器の高速化は測れたが、既知の双模倣アルゴリズムの最良実装との比較ではなく、独立した保護技術の効果ではない。

高速化原因は2段先の情報を1反復へまとめることと整合する。診断用Wasmの反復counterを全4/8/12bit割当てで検査した。これを特許性の肯定材料へ自動的に読み替えない。修正を続けるには、公開多項式逆算へ還元されない別の構成が必要である。
