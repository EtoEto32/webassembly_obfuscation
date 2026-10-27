# 先行性と読解範囲

2026-10-21確認。検索で同じ名前が出ないことを新規性の証明にしない。

| 資料 | 種別・今回読めた範囲 | 関係・限界 |
|---|---|---|
| Jorge André, João Araújo, Janusz Konieczny, **Regular centralizers of idempotent transformations**, Semigroup Forum 82(2), 307–318, 2011. DOI [10.1007/s00233-010-9274-6](https://doi.org/10.1007/s00233-010-9274-6) | 査読誌。大学の[書誌](https://web.tecnico.ulisboa.pt/ist423274/document.php?doc_id=411&locale=pt&member_id=10)と著者所属機関リポジトリの検索索引から要旨と§2冒頭の短い抜粋を確認。PDF直接取得はaccess denied/timeoutで、定理・証明の全文は読めていない | 冪等変換と可換な写像、および同値関係・代表元との関係を扱う既存数学。本案のCに可換な変換という一般問題は新しくない。同論文に今回のWasm生成手順が記載されているとは主張しない。計算機難読化の実測結果を示す資料ではない。 |
| Claudio Chamon, Jonathan Jakes-Schauer, Eduardo R. Mucciolo, Andrei E. Ruckenstein, **Encrypted Operator Computing: a novel scheme for computation on encrypted data**, arXiv:2203.08876v2, 2022-11-11 | プレプリント。[本文](https://arxiv.org/html/2203.08876v2)の要旨、§2の共役式と仮定、§5.2冒頭の非線形共役とBDD出力表現を確認 | E F E^-1と可逆非線形写像による計算変換は既知。本案はコピー不変条件を使うが、非線形化そのものや復号境界を融合する一般着想を新発明にできない。同論文の安全性仮定を公開shearコードへ流用しない。今回EOCの実装・比較試験はしていない。 |
| Cristian Cadarほか、**Data Randomization**, MSR-TR-2008-120, 2008 | 技術報告。[前区間の読解記録](../copy-centralizer/prior-art.md)を参照。今回は本文を再読していない | alias制約から表現を割り当てる先行例。今回の源操作に応じたcodec生成という一般方向の先行性。 |
| Sandeep Bhatkar, R. Sekar, **Data Space Randomization**, DIMVA 2008 | 査読会議。[前区間の読解記録](../copy-centralizer/prior-art.md)。今回は本文を再読していない | memcpy等の扱いとdata encodingは既存課題。コピー費用削減だけでは独立した新規性を確立しない。 |
| WebAssembly Community Group, **WebAssembly Core Specification**, live 3.0版（表示2026-10-20） | [memory.copy実行規則](https://webassembly.github.io/spec/core/exec/instructions.html#exec-memory-copy)を確認。技術規格で学術査読論文ではない | 境界検査、byte転送と重なり方向の意味。本案はdisjoint固定32byteしか受理せず、一般のoverlap対応は主張しない。 |

今回の差分候補はC(h,w)=(h,h)からw XOR hという残差座標を選び、零を固定する
非線形写像をそこへ置くことでnative copyを保持する具体構成。しかし既存の
中心化・data refinement・可逆回路共役の自然な応用であり、独立した新原理は
確立していない。前の線形方式とは異なる実装だが、別原理の発明数を増やさない。

検索語は `centralizer idempotent transformation semigroup permutation fibers`、
`data obfuscation Feistel`、`memory copy nonlinear encoding obfuscation` 等。
retractionという単語だけの検索は論文撤回の記事へ偏り、本件の証拠にしなかった。
equivariant normalizing flowsの書誌・要旨も検索で見つかったが、今回は全文を読まず
重複の断定には使っていない。特許公報の新たな網羅調査は実施していない。

最大のReject理由は「既知の表現変換の特殊化で、実用的な保護優位を示せない」。
後の適応的解除と費用比較はこの懸念を支持した。これは特許可否の法的結論ではなく、
本研究で主案に採用しない判断である。
