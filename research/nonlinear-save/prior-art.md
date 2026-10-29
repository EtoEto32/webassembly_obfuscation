# 先行研究と新規性の反証

調査日2026-10-23。調査で見つからないことを新規性の証明とはしない。以下は閲覧範囲を区別した技術比較であり、特許性の確定判断ではない。

|研究|書誌・状態|実際に読んだ範囲|今回との関係|
|---|---|---|---|
|Error-Correcting Functional Index Codes, Generalized Exclusive Laws and Graph Coloring|Anindya Gupta, B. Sundar Rajan。2015 preprint [arXiv:1510.04820v2](https://arxiv.org/html/1510.04820v2)。ICC 2016掲載は[著者の所属機関の一覧](https://ece.iisc.ac.in/~bsrajan/Conference_Papers.html)項目123で確認。DOI候補10.1109/ICC.2016.7511555はpublisher遷移失敗のため今回未確認|abstract、§IIIの定義1–4、§IVの命題1–2・証明・Algorithm 1、§IV-Aの定理1周辺。誤り訂正部の全証明や会議最終版との一致は未確認|副情報関数と要求関数から衝突グラフを作り、彩色を共通codeにする構成が直接先行。S_jをHas、T_jをWantと置けば今回の定式化になる。今回の階層制約とWasm修復実装の有無は別の論点|
|Indirect identification of horizontal gene transfer|David Schaller, Manuel Lafond, Peter F. Stadler, Nicolas Wieseke, Marc Hellmuth。Journal of Mathematical Biology 83, article 10 (2021)、査読済み。[DOI:10.1007/s00285-021-01631-0](https://link.springer.com/article/10.1007/s00285-021-01631-0)。preprint arXiv:2012.08897v2|書誌・abstract、time mapとLDTの定義、Lemma 8の主張と証明冒頭。生物学的評価全体・証明全体は未読|二つの木の併合時刻の比較とcograph性が近い。今回のS/Tのloss treeも時刻比較グラフを作る。union/joinで彩色できることを新定理として主張する根拠はない|
|The zero-error side information problem and chromatic numbers (Corresp.)|H. Witsenhausen。IEEE Transactions on Information Theory 22(5),592–593 (1976)、査読済み。[DOI:10.1109/TIT.1976.1055607](https://doi.org/10.1109/TIT.1976.1055607)|publisher検索結果のabstractと書誌。本文はJS/検証画面で未読|副情報付き零誤り符号化と彩色という一般原理が古くから存在することの確認。本文未読部分から新しい差分を推定しない|
|Index Coding with Coded Side-Information|Namyoon Lee, Alexandros G. Dimakis, Robert W. Heath Jr.。2014-12-31版preprint [arXiv:1501.00077](https://arxiv.org/abs/1501.00077)。書誌の詳細は[既存side-save調査](../side-save/prior-art.md)|今回の追加閲覧ではなく、先のside-save調査でintro・§II–III・Theorem 1証明を読んだ記録を参照|線形副情報の最小保存との比較対象。今回の非線形化自体はfunctional index codingに包含される|

今回のモデルは一般のfunctional index codingと違い二つの情報損失階層を持つため、最適彩色を直接構築できる。技術的な作業は、この入力への縮約、同時に生成するclique証明書、copy途中のtrapを含むrepairの生成、最良線形保存との実バイナリ比較である。一般符号化・cographの組合せから容易に導けると判断されることが、特許を目指す上で最大の懸念である。

探索には `two ultrametrics cograph`, `later-divergence-time cograph`, `index coding nested side information`, `checkpoint confusion graph coloring`, `state saving nonlinear graph coloring compiler`, `obfuscation cograph` を用いた。特許サイトでも `state saving encoding nonlinear`, `confusion graph memory`, `checkpoint cograph` を検索したが、今回の検索結果では関連請求項の照合に至っていない。これを網羅的な特許調査や抵触の否定と扱わない。

公開reset/peekを使う有限状態学習に全24変換条件が戻せたため、今回の実測は新しい解析耐性を支持しない。メモリ表現を非線形化しただけで既存難読化を超えたとは言えない。候補は補助的な表生成の最適化として保存し、主たる難読化発明には採用しない。
