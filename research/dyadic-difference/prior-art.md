# 近接先行研究と新規性の判断

2026-10-22。読んだ資料と範囲を区別する。差分による計算、有限環での補間、係数の非一意性を新発見とは主張しない。

| 文献 | 出版状態・所在 | 今回読んだ範囲と対応 |
|---|---|---|
| Robert Paige, Shaye Koenig, **Finite Differencing of Computable Expressions**, 1982, ACM TOPLAS 4(3), 402–454 | 査読論文。[DOI](https://doi.org/10.1145/357172.357177)、[本文の複製](https://www.boopidy.com/aj/cs/cs265/p402-paige.pdf)。DOIの直接openは失敗、PDF表紙で書誌を照合 | 要旨・導入、§4のdifferential transformation/chain rule、§4.3の費用条件を確認。元の計算を更新式へ移す一般的な変換は既知。全53頁の精読、論文全実験の再現ではない |
| Robin Geelen, Ilia Iliashenko, Jiayi Kang, Frederik Vercauteren, **On Polynomial Functions Modulo p^e and Faster Bootstrapping for Homomorphic Encryption**, EUROCRYPT 2023 | 査読会議。[DOI](https://doi.org/10.1007/978-3-031-30620-4_9)、[著者ePrint記録](https://eprint.iacr.org/2022/1364)。ePrint初出2022、現行記録は2025改訂。本文PDF直接取得は403 | 書誌・要旨を確認。本文は下記著者博士論文の収録章で読む。暗号実装の評価を今回の難読化性能へ移していない |
| Jiayi Kang, **Optimisations and applications of fully homomorphic encryption**, KU Leuven博士論文、2025年11月 | 学位論文。[著者公開PDF](https://jiayikang2.github.io/files/phd_thesis_nopreface.pdf) | 上記論文を題名とする章の§2.2、§3.1–3.3（印刷頁81–91、PDF頁101–111付近）を確認。falling factorial基底、null polynomial、係数の標準範囲、縮約前進差分による補間が今回の回復原理に具体的に対応する。全328頁読了とはしない |
| David Singmaster, **On polynomial functions (mod m)**, Journal of Number Theory 6(5), 345–352, 1974 | 査読論文。[出版社ページ](https://www.sciencedirect.com/science/article/pii/0022314X74900316)、DOI 10.1016/0022-314X(74)90031-6 | 出版社由来の書誌・要旨だけ確認。全本文は未取得。係数の正規表現・零多項式という先行する課題の存在を確認し、定理の本文確認はKang収録章と区別 |
| Thomas W. Reps, Louis B. Rall, **Computational Divided Differencing and Divided-Difference Arithmetics** | [著者機関の報告書要旨](https://research.cs.wisc.edu/wpis/abstracts/tr1415r.abs.html) | 要旨だけ。分割差分を生成するプログラム変換が先行することを確認。本文・出版年・発表先は今回未確認で補完しない |

今回の具体的実装差分は、i32の32個の2進刻み、typed table、到達可能prefixで消える補正、正確なwrapを保つCLIである。しかしそれだけで有限差分化から独立した原理とは言えず、修正版も既知の有限環多項式の補間で解除できる。

最大のReject理由は、既知の差分評価を難読化へ移した構成に留まり、その狭い技術差が追加の保護費用を生んでいないこと。新規性の網羅的反証や全特許請求項の照合を完了したという主張はせず、本案の主発明としての採用を見送る。公開情報を数学的比較に用いただけで、暗号化方式を研究成果として採用してはいない。
