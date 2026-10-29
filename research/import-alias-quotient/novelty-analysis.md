# 先行技術との比較と不採用判断

2026-10-24。新規性を支持するより、広い主張を否定する証拠が得られた。

|技術要素|近い一次資料|確認範囲と判断|
|---|---|---|
|実objectの同一性をmodule内部の参照へ写す|[Binaryen wasm-merge](https://github.com/WebAssembly/binaryen/blob/main/src/tools/wasm-merge.cpp)|CLI helpとimport解決の説明を読み、手元version133で198統合を実行。小さなwrapperで本方式の変換を代替できる|
|意味保存変換によるcompiler試験|Donaldson/Lascu, MET2016|Abstract、§1–2、§3の関連箇所。opaque値・dead code・identity変換とaliasに関する方向が先行|
|複数bindingの比較|Stanley/Eide, ASE2025|公式要旨のみ。WIT bindingの差分試験自体は先行|
|変換mutantとmetamorphic関係を使う試験|US10970199B2|本文概要、請求項1–13を確認。一般的な試験構成を新規にしない|
|binaryを書き換えmulti-memoryで隔離|Bento, WWW2026|公式紹介のみ。本文403。隔離方式ではない本案と目的は異なるが、multi-memory操作を初めて扱うとは言えない|

Alastair F. Donaldson, Andrei Lascu, **Metamorphic Testing for (Graphics) Compilers**, MET 2016 short paper、DOI [10.1145/2896971.2896978](https://doi.org/10.1145/2896971.2896978)。[著者公開PDF](https://www.doc.ic.ac.uk/~afd/homepages/papers/pdfs/2016/MET.pdf)。実行時の値を保ちつつ静的な解析条件を変える試験が先行する。本案のhost aliasをindexへ写す具体的relationが同じものだと本文中で確認したわけではないが、原理的差の主張は弱い。

[US10970199B2](https://patents.google.com/patent/US10970199B2/en)、**System for metamorphic relationship based code testing using mutant generators**。発明者Madhusudhanan Krishnamoorthy、掲載出願人Bank of America Corp、掲載優先日2019-02-05、A1公開2020-08-13、B2公開2021-04-06。意図的な変更、関係の対応、試験結果比較、修正を含む構成を記載する。本案の意味保存商とこの文献の誤り導入を同一視はしない。全family・権利状態・抵触の法的分析は行っていない。

読んだ他資料とURLは[計画](plan.md)、WABTの既知不具合は[切分け記録](reader-note.md)。WasmSepaと資源隔離研究も探索したが、現時点ではAbstract/Introductionのみで本案の近接性判断に用いない。

## 判断

検査器としては動作し、V8とWasmtimeで一致、意図的な誤最適化を検出した。ただし、既存linkerで同じ変換を作れることが強い反証である。**主特許案として不採用、再利用できる検査資産として保存**する。既知のWABT問題を再遭遇したことも、新発見件数にしない。新規性のためだけに命名や条件を追加しない。
