# 先行研究と新規性の限界

2026-10-22。全文、部分、要旨のみを区別する。特許性・権利範囲・実施自由の法的判断を行った記録ではない。

## Reeds–Sloane

J. A. Reeds, N. J. A. Sloane, **Shift Register Synthesis (Modulo m)**, 1985, SIAM Journal on Computing 14(3),505–513、査読論文。[DOI 10.1137/0214038](https://doi.org/10.1137/0214038)、[著者公開PDF](https://neilsloane.com/doc/Me111.pdf)。表紙・要旨・§1–3と§4の冒頭から主要更新規則までを読んだ。全9頁の証明と例を通読したとはしない。

既知の素因数分解を持つ整数modulusへBerlekamp–Massey型の漸化式合成を拡張する。逆元を持たない要素により通常の体上の方法が破れる問題を扱う。§2の式(2)は、有限応答と分母・分子の関係を形式級数として表す。著者は固定modulusで系列長に対して二乗の計算量を述べるが、本実装の性能保証として引用しない。

本案への反証：mod2^32、零因子、非一意な係数は、それだけで低次数の入出力規則を隠す根拠にならない。今回の小さな合同式solverは論文の逐次算法の忠実な再実装ではなく、同じ問題に対する単純な次数探索である。

## 有限環上の状態空間表現

Diego Napp, Raquel Pinto, Conceição Rocha, **State representations of convolutional codes over a finite ring**, 2022, Linear Algebra and its Applications 640,48–66、査読論文。[DOI 10.1016/j.laa.2021.12.006](https://doi.org/10.1016/j.laa.2021.12.006)、[出版社ページ](https://www.sciencedirect.com/science/article/pii/S0024379521004353)。出版社の一次検索結果で書誌・要旨を確認した。出版社本文は403、大学repositoryのPDFもこのturnでは開けなかった。**本文は未読**。

確認できた範囲では、Z/(p^r)上の入出力・状態表現と可観測性、可到達性、最小性を扱う。このため有限環の状態表現という一般分野を新しいものとは扱わない。ただし要旨だけから、今回のUD生成規則が同論文に掲載されているとは断定しない。

## データ表現による難読化

Roberto Giacobazzi, Neil D. Jones, Isabella Mastroeni, **Obfuscation by Partial Evaluation of Distorted Interpreters**, PEPM2012,63–72、査読workshop論文。[DOI](https://doi.org/10.1145/2103746.2103761)。過去の[確認記録](../symmetric-state/design.md)を参照。大学の書誌・要旨と検索で得た§5.5を確認済みだが、全文を読んだとはしていない。

今回も意味を保存する表現関係が中心であり、データrefinementという一般原理の発明ではない。非単射Eと観測の保存という具体的な条件は明示したが、これが独立した難読化の新規性を持つという先行技術上の根拠は確立していない。

## 採否

UDによる情報損失、native i32 globalによる持続状態、到達状態上で零になるKの生成を実装した。一方、公開応答は既知の低次数線形同定の対象のままだった。全24条件は同じ入力履歴から回復でき、状態の非一意性を独立した保護原理として採用できない。Wasmへの具体的なloweringや名称を新規性の根拠にせず、主発明には不採用とする。

前の有限環残差フィードバック候補と区別する。本案は固定点への反復計算でも、残差ミキサーの収束条件でもなく、1呼出し1遷移の入出力系の商表現である。この違いをもって独立した新発明の数へ加算するものではない。
