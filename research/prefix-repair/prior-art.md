# 先行性と差分の確認

調査日2026-10-21～22。読めた範囲に限定する。新規性・特許性を確定する調査ではない。

| 一次資料 | 書誌・区分 | 確認した内容と本案との関係 |
|---|---|---|
| [LINVIEW: Incremental View Maintenance for Complex Analytical Queries](https://arxiv.org/pdf/1403.6968) | Milos Nikolic, Mohammed El Seidy, Christoph Koch, SIGMOD 2014。査読会議の著者公開版。書誌は[公式project](https://www.epfl.ch/labs/data/research/linview/)でも確認 | §4.1の差分、§4.2の低rank因子、§4.3/Algorithm1の更新trigger生成を確認。密な変化を因子に分けて更新を安くする基本着想は既知。本案のGF(2) copy-prefixの式と同一だと確認したわけではない。著者の速度結果を今回の速度比較へ流用しない。 |
| [On-Stack Replacement, Distilled](https://season-lab.github.io/papers/osr-distilled-pldi18.pdf) | Daniele Cono D’Elia, Camil Demetrescu, PLDI 2018、査読論文、[DOI](https://doi.org/10.1145/3192366.3192396) | 状態の再構成が先行。§5.3はstoreを移動した場合のmemory補償も述べる。Definition2.4の終了意味とWasmのtrap後に観測される状態はそのまま同一ではないが、必要な地点で状態を整合させる一般発想は新しくない。今回は著者LLVM実装との性能比較をしていない。 |
| [WebAssembly Core 3.0 memory.copy](https://webassembly.github.io/spec/core/exec/instructions.html#exec-memory-copy) | 実行仕様、取得時表示2026-10-20。論文ではない | 範囲検査が書込みより先、重複範囲のcopy方向が規定される。本案はこの意味を使う。仕様の利用そのものを発明とはしない。 |

先行するdata encodingと、このrepositoryのcopy-centralizer/copy-fiberとの差もある。
後二者はcopyと表現の可換性を要求するが、本案はBをその条件で制限せず、差分を出口で修復する。
ただし、これはリポジトリ内の案との差であって、世界全体での先行性の不存在を意味しない。
Data Randomization / Data Space Randomizationの既読範囲と書誌は
[copy-centralizerの資料](../copy-centralizer/prior-art.md)に保持し、今回新たに全論文を読んだとはしない。

追加反証検索は `"compiler" "linear" "checkpoint compression"`、
`"checkpoint" "linear dependencies" program`、`"obfuscation" "compensation" memory`、
`"on stack replacement" "linear" "encoding"`。
Principled Composition of Function Variants for Dynamic…の大学repository PDFが候補に出たが、
取得は403で失敗し本文未読。検索の見出しだけから方式を同定しない。
検索結果の少なさは新規性の証拠にしない。関連特許の請求項を網羅照合した段階でもない。

差分候補は「符号化copy列の正常出口と全trap prefixをまとめて、共有保存基底と修復を生成する」具体化にある。
しかし低rank差分と状態補償からの直接的な構成に近く、独立した新規原理とは現時点で主張しない。
最大のReject理由は、その組合せ以上の技術的差分と保護上の効果を示していないこと。
工学的な費用削減は保存するが、主たる難読化発明としては不採用とする。
