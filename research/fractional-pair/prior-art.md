# 先行技術と新規性の判定範囲

2026-10-22。検索語は`software obfuscation projective coordinates`、`obfuscation homogeneous coordinates`、`quotient remainder fractional bits division Lemire`、`remainder fractional quotient patent`、`integer division perturbation remainder`等。完全一致する名称が出なかったことを新規性の根拠にしない。

| 資料 | 区分・確認範囲 | 技術的関係 |
|---|---|---|
| Daniel Lemire, Owen Kaser, Nathan Kurz, *Faster Remainder by Direct Computation: Applications to Compilers and Software Libraries*, Software: Practice and Experience 49(6), 2019 | 査読誌掲載情報を[arXiv書誌](https://arxiv.org/abs/1902.01961)で確認、DOI [10.1002/spe.2689](https://doi.org/10.1002/spe.2689)。読んだ本文は[著者公開v3](https://arxiv.org/html/1902.01961v3)の要旨、§3、Theorem3.3と証明。別の機関PDF URLは取得失敗 | 逆数近似との積の下位部分から直接余りを得る方法と精度条件。小数部を使う発想は既存。著者は通常コンパイラより高速な例を報告するが、本実験で著者実装を再現していない。 |
| Stephen Drape, *Obfuscation of Abstract Data-Types*, Oxford博士論文, 2004 | [大学公開PDF](https://www.cs.ox.ac.uk/files/2892/thesis.pdf)、表紙・要旨、§6.1本文107–108頁。学位論文、査読会議論文と区別 | 同次座標の倍率による同値性と行列の表現変更を扱う。同次座標を使うだけでは独自性にならない。今回のdiv/rem摂動式が掲載されているとは主張しない。 |
| Ping Tak Peter Tang, *Apparatus and method for remainder calculation using short approximate floating-point quotient*, US7013320B2 | [公報HTML](https://patents.google.com/patent/US7013320B2/en)、書誌・説明概要・請求項1/10を確認。B2公開2006-03-14、A1公開2003-07-31 | 指定精度の近似浮動小数点商・丸め・lookup table。今回のu32可変除数と整数の許容摂動区間と同一とは確認していない。全請求項・特許ファミリーを照合したとは扱わない。 |
| WebAssembly Community Group, *WebAssembly Core Specification*, Numerics | [公式仕様](https://webassembly.github.io/spec/core/exec/numerics.html#op-idiv)。unsigned div/rem、剰余演算、除数0の未定義性を確認。技術仕様 | native i64除算とi32/i64の厳密な幅が実装の前提。ただし数学的な生成則はWasm専用ではなく、C等のu32/u64でも表現できる。 |

最も近い具体的なアルゴリズムはLemireほかの小数部分からの余り計算。違いは、今回は定数逆数を前計算せず可変dのnative広幅除算を実行し、分子へtを加え、除数ごとに0<=t<=A-d+gcd(A,d)-1を生成する点である。この差分の記述と、独立した新規性の確定は別である。既知の量子化誤差・丸め区間の議論からの直接的な帰結である可能性を残す。

本案の最大のReject理由は、局所式の差分に対して、既存数値表現・除算手法を超える難読化効果を示せていないこと。通常のqsub対照より約1.58–1.81倍の実行費用を要し、方式既知の回復は全12条件で成功した。局所関係を保持する正当性条件が、そのまま短い回復規則にもなった。

新しい構成仮説の式・許容範囲・実装は研究資産として残すが、現段階で主発明や出願候補へ昇格させない。これは「回復できるから難読化ではない」という判断ではなく、追加の保護効果・費用・先行技術との距離を合わせた技術評価である。特許取得可否、権利範囲、侵害に関する判断はしていない。
