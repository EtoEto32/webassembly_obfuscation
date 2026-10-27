# 近接する既存技術と主張の境界

確認日2026-10-21。読めた範囲を以下に明記する。検索で一致しなかったことを新規性の証明にしない。

| 資料 | 種別・書誌 | 今回確認した範囲 | 提案との関係 |
|---|---|---|---|
| [CPFloat: A C Library for Simulating Low-precision Arithmetic](https://doi.org/10.1145/3585515) | Massimiliano Fasi, Mantas Mikaitis; ACM TOMS 49(2), article18, 2023 | 著者公開PDFの要旨・導入・§5のAlgorithm5.1/5.2周辺。publisher本文は取得不可 | 高精度のnative演算後にbit操作で目標精度へ丸めること、特殊値・underflow/overflow処理は既存 |
| [CPFloat公式文書](https://north-numerical-computing.github.io/cpfloat/readme.html) | 実装の現行文書 | format定義とv0.6.0以降のemin/emax独立指定 | 24bit精度と両指数限界を同じpだけ移す格子は、既存のcustom format枠組みで表せる |
| [US6668325B1: Obfuscation techniques for enhancing software security](https://patents.google.com/patent/US6668325B1/en) | Christian Sven Collberg, Clark David Thomborson, Douglas Wai Kok Low; 公開2003-12-23、掲載優先日1997-06-09 | 書誌、明細書§7.1.1 Change Encodingと周辺。全請求項を精査したものではない | affine符号化、2の冪の倍率、精度・overflow問題と型を広げる選択が既出 |
| [Innocuous Double Rounding of Basic Arithmetic Operations](https://jfr.unibo.it/article/view/4359) | Pierre Roux; Journal of Formalized Reasoning 7(1):131–142, 2014; DOI10.6092/issn.1972-5787/4359 | 出版元の要旨・書誌。本文PDF取得はtimeout | 高精度で基本演算して低精度へ丸めることの安全条件・形式証明を新発明としない |
| [Formal Verification for Numerical Computations, and the Other Way Around](https://guillaume.melquiond.fr/doc/19-hdr.pdf) | Guillaume Melquiond; HDR, 2019 | PDF p134 §5.2、p168参考文献 | binary32入力の演算をbinary64で行う無害な二重丸めの既知結果を確認。任意のf64入力へ拡張しない |
| [Protecting Floating-Point Computation for Deep Neural Network Binaries with Mixed Boolean-Arithmetic Obfuscation](https://arxiv.org/html/2607.17603v3) | Yikun Huほか; arXiv2607.17603v3, 2026; preprint、査読発表先未確認 | 要旨と§3–5。比較はv3の計画記述に限定 | 高精度表現で浮動小数点を保護する方向は既出。本案はnative f64の格子変換だが、高精度化そのものには新規性を置けない |
| [Wasm Core Numerics](https://webassembly.github.io/spec/core/exec/numerics.html) | Core3.0の公式仕様、表示2026-10-20 | Floating-Point Operationsの丸め・NaN・flagの規定 | 正当性の前提。仕様上の性質の利用と新発明を区別する |

CPFloatの著者公開版は[ManchesterのPDF](https://eprints.maths.manchester.ac.uk/2850/3/fami22.pdf)。
表紙のEPrint年は2020、内側の版日は2022-03-05。2023年の出版版と同じ版を読了したとはしない。
現行docsのemin/emax独立指定が2023年版にもあったと遡って主張しない。
同資料は低精度エミュレーションの高速化を報告するが、本実験の速度との直接比較はしていない。
CPFloatをcompileしていないため、本案のgrid0を「CPFloat実測値」と呼ばない。

## 技術的な差分の評価

当初の差分仮説は「nodeごとの倍率と、その演算結果のnormal/subnormal/overflowを含む丸め格子を同時に生成する」ことだった。
実装ではこの具体的規則が動作し、途中のf32復号を除けた。しかし、倍率符号化・型の拡張・custom formatの丸めはそれぞれ近接する先行構成を持つ。
今回確認した範囲で、この生成器と完全に同一の記載を特定したわけではない。
それでも、具体化の独立した技術効果が乏しいまま「新規な難読化原理」と断言する根拠にはならない。

保護タスクでは方式既知の局所認識により全対象が回復され、通常入力では実行費用も増えた。
underflow条件の高速化は倍率0でも得られ、node別倍率の利得ではない。
したがって「元の演算順序を保つWasm実装・境界処理・適応解析の測定」を成果として保存し、独立した主発明には採用しない。
特許の新規性・進歩性・有効性の法的判断、全請求項を対応付ける調査、網羅的な特許調査は行っていない。
