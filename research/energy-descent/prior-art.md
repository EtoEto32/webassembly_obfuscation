# 先行技術との照合と新規性判断

2026-10-22。検索語：`program obfuscation Hopfield`、`Boolean circuits energy function local minima hierarchical weights`、`Converting binary threshold networks into symmetric networks`、`control flow obfuscation recursion continuation`。検索結果の不在は新規性の証明ではない。取得できなかった本文の内容は補完しない。

| 文献 | 種別・読んだ範囲 | 今回との関係・限界 |
|---|---|---|
| Gadi Pinkas, *Converting Binary Thresholds Networks into Equivalent Symmetric Networks*, 1991-07-01, WUCS-91-31, DOI [10.7936/K7930RJB](https://doi.org/10.7936/K7930RJB) | 大学Technical Report、査読誌とは区別。[機関ページ](https://openscholarship.wustl.edu/cse_research/649/)の書誌・abstractを読んだ。PDFリンクは403で本文未読。 | 非振動のbinary threshold networkをsymmetric networkへ変換し、acyclicの場合に同サイズ・同効率の構成があるとabstractが述べる。方向付き計算を対称なenergyへ移す一般着想に非常に近い。今回の厳密な子重み式が本文にあるとは主張しない。 |
| Gadi Pinkas, *Symmetric Neural Networks and Propositional Logic Satisfiability*, Neural Computation 3(2), 282–291, 1991, DOI [10.1162/neco.1991.3.2.282](https://doi.org/10.1162/neco.1991.3.2.282) | 査読誌。[書誌・abstract](https://pubmed.ncbi.nlm.nih.gov/31167301/)確認。publisher本文の取得は失敗。 | 論理式とenergy最小化の相互変換を扱う。論理をenergyで評価することそのものは新原理ではない。今回著者実装を実行していない。 |
| Gadi Pinkas, *Representation and Learning of Propositional Knowledge in Symmetric Connectionist Networks*, 1991-12-01, WUCS-91-52, DOI [10.7936/K7VD6WTX](https://doi.org/10.7936/K7VD6WTX) | Technical Report。[機関ページ](https://repository.library.washu.edu/cse_research/670/)のabstract・書誌。PDF403。 | penalty logicとsymmetric networkの相互変換・学習を扱う。非一意の元制約を一意に戻せないことと、等価な計算を得られないことを区別する必要がある。今回と同じ復元攻撃が掲載されているとは断定しない。 |
| Gadi Pinkas, Rina Dechter, *Improving Connectionist Energy Minimization*, JAIR 3, 223–248, 1995 | 査読誌掲載版が[arXiv PDF](https://arxiv.org/pdf/cs/9510102)に収録。abstract・§1–2・§3のtree dynamic programming導入（印刷pp223–227）を確認。後半の証明全体は未精読。 | 局所最小と全体最小の区別、木構造上の改善を扱う。本文のacyclicは対称networkの無向木という文脈であり、今回のsource DAGと同一視しない。一般NP問題の難しさをこの生成族へ転用できない。 |
| Andrew Lucas, *Ising formulations of many NP problems*, Frontiers in Physics 2:5, 2014, DOI [10.3389/fphy.2014.00005](https://doi.org/10.3389/fphy.2014.00005) | 査読review。[publisher本文](https://www.frontiersin.org/journals/physics/articles/10.3389/fphy.2014.00005/full)のabstract、§3、§4.1–4.4を確認。HTMLで一部式が画像なので、その式の細部は判断根拠にしない。 | 制約違反が目的値の利得に負けないweight boundという一般方法が既知。今回のDAGごとの座標更新等価性をこの論文の結果として帰属しない。 |
| Kenny Zhuo Ming Lu, *Control flow obfuscation via CPS transformation*, PEPM2019, DOI [10.1145/3294032.3294083](https://doi.org/10.1145/3294032.3294083) | [ACM SIGPLAN公式abstract](https://sigplan.github.io/OpenTOC/pepm19.html)を確認。今回本文未読。 | 継続・高階combinator・関数pointerによる制御の分断が既知。冒頭に検討した継続案を独立した新発明として増やさない根拠。 |

## 判断

試作の実装上の特徴は、Wasmのbit集合とi64厳密算術による高次multilinear energy、DAGの直接の子への影響からの重み生成、極性・配置変更後の全初期値収束である。しかしこれらの特徴が既知のpenalty構成から独立した新規性を持つ根拠は未確立。Wasm移植・係数縮小・置換だけを発明として数えない。

方式を知る解析では、元制約の分解を求めず座標差分の符号から等価DAGへ戻せた。最重要の失敗原因は、安定化を保証する優越条件が、そのまま低次の局所更新を露出させること。特許の主核として採用しない。ここでの判断は技術的な候補選別であり、権利範囲の法的結論ではない。
