# 一次資料、先行性、確認範囲（2026-10-19）

| 資料 | 書誌・状態 | 今回実際に確認した範囲 | 関係と限界 |
|---|---|---|---|
| [Relaxed SIMD proposal](https://github.com/WebAssembly/relaxed-simd/blob/main/proposals/relaxed-simd/Overview.md) | WebAssembly提案リポジトリ、査読論文ではない。参照日のmain | Summary、Consistency、Relaxed swizzle、opcode表 | 16..127のindexには0または下位4bitによる選択が許される。環境の選択規則を無視して自由な乱数とみなしてはならない。strict選択が本実験の反証になる。 |
| [Conversion from Arithmetic to Boolean Masking with Logarithmic Complexity](https://iacr.org/archive/fse2015/85400106/85400106.pdf) | Jean-Sébastien Coron, Johann Großschädl, Mehdi Tibouchi, Praveen Kumar Vadnala, FSE 2015、[査読・DOI確認](https://orbilu.uni.lu/handle/10993/25599)、DOI 10.1007/978-3-662-48116-5_7 | Abstract、§4.1–4.3、Algorithms 2–4 | AND/XOR/shiftをmask表現上で行う代数が既知。本案の演算式は独立の新原理ではない。原論文はside-channel対策で、独立乱数等の条件がある。抄録の64bitで23%改善は原論文の報告で、今回の比較値ではない。 |
| [Manufacturing Opaque Predicates in Distributed Systems for Code Obfuscation](https://www.cs.auckland.ac.nz/research/groups/ssg/bib/ssgpapers/majumdar06manufacturing.pdf) | Anirban Majumdar, Clark Thomborson, ACSC 2006, CRPIT 48, pp.187–196、会議論文。本文はposition paperと記載 | Abstract、§2の定義、§3.4–3.5、結論の一部 | 非決定性・分散状態とopaque predicateの先行例。Wasmの実装依存SIMD値とは異なる。今回読んだ範囲から定量的な攻撃費用を転記しない。論文全体の主張の追試でもない。 |

Boolean maskの式に一般式のs=t=u=mを代入すると、ANDの式は今回のcross termになる。したがって、今回の候補に残る具体差は主にmaskの供給源とWasm命令への適用である。研究指示にある「既知方式のパラメータ変更を新候補と数えない」という基準に従い、主発明にはしない。

検索語：`"obfuscation" "relaxed SIMD"`、`"obfuscation" "relaxed_swizzle"`、`"software obfuscation" "nondeterminism"`、`"Boolean masking" "XOR" "AND" Coron`。完全一致の関連論文が検索結果に現れなかったことは新規性の証明ではない。

今回の別案スクリーニングでは、[Creating transformations for matrix obfuscation](https://www.cs.ox.ac.uk/people/stephen.drape/papers/SAS.pdf)（Stephen Drape, Irina Voiculescu、SAS 2009、DOI 10.1007/978-3-642-03237-0_19）の§5.1検索抽出に、行列式によるscalarの表現が見つかった。[著者の書誌](https://www.cs.ox.ac.uk/people/stephen.drape/publications.html)を確認したが、本文のopenは失敗した。全文読了や評価結果の確認とは扱わず、行列表現を直ちに新規案としないための手掛かりに留めた。

公開特許の追加検索ではUS20220035977A1、EP4542423A1等が出たが、この回では請求項を精読していない。新規性・進歩性・権利抵触についての結論には使わない。既存の[特許調査記録](../patent/README.md)と合わせても、特許性の確立は未達。外部公開・push・出願はしていない。
