# 先行例と特許候補としての判断

調査日 2026-10-19。今回は既存の非線形符号化を SIMD に配置するだけでは独立した発明を示せないと判断し、小規模な反証実験までで主案から除外した。暗号方式や鍵抽出耐性を開発・主張した結果ではない。

| 資料 | 書誌・読んだ範囲 | 含意と限界 |
|---|---|---|
| S. Chow, P. Eisen, H. Johnson, P. C. van Oorschot, *White-Box Cryptography and an AES Implementation* | SAC 2002、改訂論文集 LNCS 2595, 2003, pp.250–270、[DOI](https://doi.org/10.1007/3-540-36492-7_17)。査読会議論文。[著者版の大学ミラー](https://home.cs.colorado.edu/~jrblack/class/csci7000/f03/papers/oorschot-whitebox.pdf)の検索索引から要旨・§3.2 を実際に取得。PDF open は timeout。全評価節の精読ではない。 | 入出力全単射を演算に合成して表にすること、隣接表の符号化を接続すること、小さな全単射を連結することが直接先行する。min-loss encoding もあり、非単射の冗長表現へ変えるだけで初出とはできない。今回 AES を再現・攻撃したのではなく、同じ基本符号化を小さな算術へ適用した。既存論文の性能数値は未取得として転記しない。 |
| Maratyszcza, *Byte shuffle / table lookup operations* | [WebAssembly SIMD 公式 issue #24](https://github.com/WebAssembly/simd/issues/24)、2017-11-05。技術提案、査読論文ではない。issue 本文確認。 | byte shuffle による小さな並列表参照を明記。Wasm SIMD に表を置くこと自体を新規とは主張できない。難読化の評価資料ではない。 |
| A. A. Albert, *Quasigroups. I* | Trans. Amer. Math. Soc. 54 (1943), 507–519、[DOI](https://doi.org/10.1090/S0002-9947-1943-0009962-7)。査読論文。原 PDF は403で取得できず、[AMS の引用書誌](https://www.ams.org/journals/tran/1970-151-02/S0002-9947-1970-0272932-4/home.html)を確認。本文を通読したとは扱わない。 | principal isotope は既存の代数理論。今回必要な可換群の恒等式は algorithm.md に直接導出し、有限表の結合律と復元一致も自前で検査した。本文未取得を根拠に新規性を主張しない。 |
| Paul Gorissen, Wil Michiels, *Mechanism for Software Tamper Resistance: An Application of White-Box Cryptography* | ACM DRM '07、2007-10-29。[大学ミラー](https://profs.sci.univr.it/~giaco/download/Watermarking-Obfuscation/p82-michiels.pdf)の検索索引で1頁目の要旨・導入を確認。PDF open 失敗。 | コードを lookup table としても解釈し、白箱実装と結合する改変耐性。今回の命令定数に表を載せる実装とは異なる。後続節の評価を読めていないので効果の数値は記載しない。 |
| *Protecting look up tables by mixing code and operations* | [US9189425B2](https://patents.google.com/patent/US9189425B2/en)、発明者 Augustin J. Farrugia, Benoit Chevallier-Mames, Bruno Kindarji, Mathieu Ciet, Thomas Icart。B2公開2015-11-17、A1公開2013-03-07。特許公報。書誌、入力・出力写像の説明、請求項1–26を取得。 | 符号化表と演算を混ぜ、入力・出力を写像する構成が関連する。請求項1は暗号処理の表値取得と二つの関数を含む具体的構成。今回の非暗号 SIMD 算術を当然に包含すると断定しない。「同じ目的の特許がある」だけで権利範囲を判断しない。法的有効性・実施自由・世界全域の先行技術調査は未評価。 |

検索語：`WebAssembly SIMD swizzle obfuscation lookup tables white box`、`white-box swizzle`、`software obfuscation random encodings nibble lookup tables compiler`、`Albert quasigroups groups isotopic isomorphic 1943 principal isotope`、`patent software obfuscation lookup tables bijective encodings`。検索で見つからないことを、先行例がない証拠にしない。

差分候補は「Wasm SIMD のコード定数として符号化表を実行し、線形メモリを使わない」という実装配置だった。全単射で表を合成する核と SIMD 表参照の両方に明確な先行性がある。今回の測定でも、最適化後に表が残ることは確認したが、既知の代数的正規化で表ごとに分解できた。性能・解析費用を改善する新しい表合成規則もない。したがって、特許の主請求項に育てる根拠は現状弱い。法的な特許性の否定を確定したものではない。

前の operand-rebasing は bit 逐次の状態機械と残差計算、simd-quotient は符号の閾値への射影だった。今回は有限演算表の同位体を群へ戻す機構が異なる。一方、過去の案との違いは先行研究に対する新規性を意味しない。
