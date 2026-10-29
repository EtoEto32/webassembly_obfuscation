# 先行技術の読取範囲と差分

確認日2026-10-21。検索結果に同じ題名がないことを新規性の証拠にしない。

| 資料 | 書誌・読取範囲 | 今回との関係 |
|---|---|---|
| [Data Randomization](https://www.microsoft.com/en-us/research/publication/data-randomization/) / [本文](https://www.microsoft.com/en-us/research/wp-content/uploads/2008/09/tr-2008-120.pdf) | Cristian Cadar, Periklis Akritidis, Manuel Costa, Jean-Philippe Martin, Miguel Castro。MSR-TR-2008-120、2008年9月。読んだ版は技術報告で査読論文として数えない。要旨と§3.1の等価クラス・union-findの記述を確認 | 接続・alias制約から同じmaskを使う対象をまとめる構成は既知。要旨の平均時間overhead 11%は著者の条件であり、今回と同条件の比較ではない。本案の複数byte混合とcopy行列制約はそのまま同じ実装ではないが、制約に応じた表現割当という一般発想は先行する。 |
| [Data Space Randomization](https://www.seclab.cs.sunysb.edu/seclab/pubs/dsr.pdf) | Sandeep Bhatkar, R. Sekar。DIMVA 2008、査読会議。[公式program](https://dimva.org/dimva2008/program.html)でも確認。著者PDFの要旨、§2.1–2.2の関連部分、§3.1のbulk関数に関する段落を確認 | points-toとmaskの等価クラス、memcpy/memset/bzeroに特別な扱いが必要になることを扱う。著者要旨の5–30% overheadを今回へ転用しない。メモリ破壊防御と公開binaryのIP保護は攻撃モデルが異なり、その安全性主張を流用しない。 |
| [Magma Handbook: Operations on Matrix Algebras](https://magma.maths.usyd.edu.au/magma/handbook/text/1033) | University of Sydney Computational Algebra Groupの公式技術資料。Centralizer(A,S)の定義を確認。更新される文書であり、APIの初出年は未確認 | 行列代数の部分代数と可換な行列を求める操作は既知。全copy生成元との可換性から許容Bを求めることを、新しい中心化代数の算法とは呼ばない。Magma本体は実行していない。 |
| [Creating Transformations for Matrix Obfuscation](https://www.cs.ox.ac.uk/files/2891/SAS.pdf) | Stephen Drape, Irina Voiculescu、SAS 2009、DOI 10.1007/978-3-642-03237-0_19。今回は[既存の読解記録](../../tmp/determinant-representation-audit/README.md)を参照。全文を再読したとはしない | 行列を使う表現変換自体は既知。保存された比較は行列式による数値表現で、本案のcopy行列からのメモリcodec生成と区別する。 |

Wasmのmemory.copyを利用するが、中心化条件は他の形式のmemmoveにも適用できる。Wasm固有性は、明確なbyte意味論と検証可能な固定profileで実装できる点に留まる。

今回の具体的な差分候補は、**実binaryにある操作集合から、コピーを修復なしで実行できる非対角メモリcodecとread/write更新器を一緒に生成すること**。既存copy-commutationの手で選んだ整列pairからは進んだが、中心化代数・線形符号化・data refinementを用いた自然な構成でもあり、独立した発明としての新規性は確立していない。今後同じ自動生成規則を示す文献があれば差分を更新する。

主要検索語は `data encoding obfuscation memcpy`、`data randomization equivalence classes memcpy`、`obfuscation centralizer matrix`、`data representation commutant compiler`。検索で見つかった非公式CTF解説や本文未取得資料を技術的根拠として採用していない。

最大のReject理由は、既知の中心化計算をデータ表現へ使った範囲を超える独自性と、実アプリでの保護効果を示せていないこと。高速化だけで特許性を認定しない。副次的な実装部品として残すが、主難読化方式としては採用しない。
