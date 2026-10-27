# 全体計算をtraceへ移す案の先行性

2026-10-21。以下は実際に取得できた範囲と、自分たちの数式・実験による判断を分けた記録。

## 最も近い構成

Christian Ikenmeyer, J. M. Landsberg, **On the complexity of the permanent in various
computational models**, Journal of Pure and Applied Algebra 221(12), 2911–2927,
2017、[DOI 10.1016/j.jpaa.2017.02.008](https://doi.org/10.1016/j.jpaa.2017.02.008)。
査読誌版の書誌を出版社情報で確認。今回読んだのは[arXiv PDF](https://arxiv.org/pdf/1610.00159)
の定義2.1–2.2、定理4.1周辺、Remark4.5。arXiv登録は2016、取得PDFの表紙には
July7,2021という日付もあり、2017年最終誌面との同一性を確認したとはしない。

層付きABP、行列積による多項式計算、始点と終点をつないだ隣接行列のべき乗traceを
用いる構成が記載される。本案の「元の計算を閉路・traceへ移す」核心に非常に近い。
この数学の計算量結果をソフトウェア解析耐性の下界には転用できない。

本ゲートでは通常の行列traceの定義を使い、単純閉路では始点の数だけL*fになることを
明示的に検査した。複素数体なら係数を除算できるが、mod2^32ではLを奇数にして
逆元を使う必要がある。原文の正規化表記の扱いを超えて、論文全体に誤りがあると
主張したり、その補正を新しい難読化発明と呼んだりしない。

## 近接する難読化資料

Stephen Drape, Irina Voiculescu, **Creating Transformations for Matrix Obfuscation**,
SAS2009、DOI10.1007/978-3-642-03237-0_19。
[以前の本文読解](../../tmp/determinant-representation-audit/README.md)を参照。今回は再読なし。
数値ごとの2×2行列式表現と、今回の式全体の閉路表現は同一ではない。しかし行列やtraceを
使うことだけでは差分にならず、有理数での除算をi32へ移す問題も既に台帳にある。

Craig Gentry, Charanjit Jutla, **Obfuscation using Tensor Products**, ECCC TR18-149,
2018-08-25。[書誌・要旨](https://eccc.weizmann.ac.il/report/2018/149/)のみ確認。
技術報告として扱い、査読版の有無は今回未確認。有限体のmatrix-product branching
program難読化を扱う。本文未読のため具体的構成・安全性・性能を本案へ流用しない。

## 同じ探索中に確認した資料

- Ning Shi, Lei Xu, Tianqing Zhu, WanLei Zhou, Weizhi Meng, Yu-an Tan,
  **Exact constrained-training neural networks for confidential 8-bit arithmetic
  primitives in code obfuscation**, Journal of Systems Architecture173,103729,
  2026-04、[DOI10.1016/j.sysarc.2026.103729](https://doi.org/10.1016/j.sysarc.2026.103729)。
  査読誌。[出版社ページ](https://www.sciencedirect.com/science/article/pii/S1383762126000470)
  の検索抽出で要旨・導入・実験設定の冒頭を確認した。直接openは403、著者PDFは取得失敗。
  8bit加算と4bit乗算からのcascadeを扱い、全域正答を報告するが、今回modelを取得・再現していない。
  neural演算への置換それ自体を新しい発明にしない。本文を読まずに全手順・耐性を推測しない。
- Jeongpil Park, Eun-Sun Cho, **WeBMO: WebAssembly Memory Bitwise Operation Obfuscation**,
  IEEE COMPSAC2024,1436–1439、DOI10.1109/COMPSAC61105.2024.00189。
  [公式プログラム](https://ieeecompsac.computer.org/2024/wp-content/uploads/sites/14/2024/06/COMPSAC2024_webprogram.pdf)
  の検索抽出でSRS枠と著者を確認。枠ごとの査読条件は未確認。本文・実装は取得できていない。
  既にoverlap-cellsの調査待ち一覧にもある資料だった。二次要旨だけから変換規則や
  本案との重複を断定せず、今回は未読状態を維持する。

以上から、trace案を「未開拓な計算モデル」として採用する根拠はない。今回の奇数条件は
意味保存の移植条件であり、それだけで先行方式を越える独立した生成規則にはならない。
新たな特許性判断や網羅的公報調査は行っていない。
