# 先行性の確認範囲

調査日2026-10-21。暗号化配布やMLのgradient obfuscationを、今回の意味保存するプログラム変換と混同しない。

|資料|書誌・区分|実際に確認した範囲|今回との関係・限界|
|---|---|---|---|
|Explicit Noether Normalization for Simultaneous Conjugation via Polynomial Identity Testing|Michael A. Forbes, Amir Shpilka。2013 arXiv:1303.0084。RANDOM2013の刊行記録も大学の業績ページで確認|[arXiv PDF](https://arxiv.org/pdf/1303.0084) §5 Definition5.1、Lemma5.4と証明。PDFの表紙には2018-10-31、arXiv表示はv2/2013-03-08とあり、両日付を区別|可換環でのHasse係数定義と積の畳込みは明示的な既知構成。難読化評価の論文ではない。全文を読了したとはしない|
|Polynomials, Divided Differences, and Codes|S. Venkitesh、ITCS2025、査読会議論文、[DOI 10.4230/LIPIcs.ITCS.2025.93](https://doi.org/10.4230/LIPIcs.ITCS.2025.93)|[公開本文](https://drops.dagstuhl.de/storage/00lipics/lipics-vol325-itcs2025/html/LIPIcs.ITCS.2025.93/LIPIcs.ITCS.2025.93.html) 書誌・要旨・§1.2冒頭|有限体の符号の構成で、今回のWasm難読化と同一とはいわない。関連する微分表現を見落とさないための周辺資料。復号定理の証明は未読|
|Dynamic analytical differentiator for obfuscated functions in complex models|[US8312260B2](https://patents.google.com/patent/US8312260B2/en)、2012-11-13公報。検索抽出でUS20110087876A1/2011-04-14も確認。発明者名は今回未確認|通常openはcache miss。一次ページから検索で返ったAbstract、説明のFig5付近、請求項1の抽出を読んだ。全公報読了ではない|暗号化containerを受信側で復号・微分・コンパイルする構成。今回の公開係数回路への変換と同じものと断定しない。タイトル一致だけで既知/新規を判定しない。権利範囲・特許性は未判断|

RANDOM2013刊行記録：[著者所属大学の業績](https://experts.illinois.edu/en/publications/explicit-noether-normalization-for-simultaneous-conjugation-via-p/)。
CppADの公式目次にTaylor/forward modeがあることは確認したが、今回試みた詳細ページは取得できず、
実装を監査したとはしない。Griewank–Utke–Waltherの論文も書誌検索に留まり、本文の評価数値を転記しない。

検索語は `program obfuscation differentiation`, `software obfuscation derivative`,
`Hasse derivative homogeneous Euler`, `Hasse derivatives product rule automatic differentiation`,
`obfuscation derivative homogeneous`, `US8312260B2`。
直接同じ題名が見つからないことを新規性の証拠にしない。

最も近い実装上の核は、可換環の係数抽出と積の畳込みである。
Wasmのmod 2^32に合わせて奇数の二項係数を選ぶのは具体的な適用条件だが、
今回の選択は逆元の存在条件から直接決まり、それだけで独立した発明の核とは判断しない。
先行研究の著者実装は比較実行していない。評価結果の数値は本リポジトリの実験だけに帰属させる。
