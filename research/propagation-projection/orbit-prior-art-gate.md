# 回転を含む変数消去案の先行研究ゲート

2026-10-21。checkpoint.mdの次候補について、実装前の新規性検査を追加した。既存の実験・採否・固定済みファイルは変更していない。

## 検査した仮説

bitwise演算だけの計算をrotate付きの語演算へ広げ、節のliteralを `(wire, shift mod w, polarity)` として表す。各節は全bit位置に対する巡回移動の集合を意味する。消去するwireが各節に高々一つのbit位置でしか現れない場合、対象literalをshift 0へ揃えて正負の節をresolveし、一つのwireの全bitを同時に消す。これによってbit展開を省きつつ射影する、という着想だった。

これは未実装の設計仮説であり、実Wasmでの停止・正当性・性能・解析費用を測定した結果ではない。128個の独立Boolean入力への分解を失わせても、それだけでは保護効果にならない。

## 新たに確認した近い先行研究

Markus Anders, **SAT Preprocessors and Symmetry**, SAT 2022, LIPIcs 236, Article 1, 1:1–1:20。査読会議。DOI: [10.4230/LIPIcs.SAT.2022.1](https://doi.org/10.4230/LIPIcs.SAT.2022.1)。[出版社PDF](https://drops.dagstuhl.de/storage/00lipics/lipics-vol236-sat2022/LIPIcs.SAT.2022.1/LIPIcs.SAT.2022.1.pdf)。要旨、Table 2、§3のSymmetric Variable EliminationとCorollary 15、§4.1の実装記述を読んだ。本文の全証明・実験を再現したわけではない。

同論文は、軌道の和集合をまとめて変数消去する規則を示す。したがって「対称な変数を軌道ごと消す」という一般原理を独自の発明とは主張できない。実装では非対称と保証された変数へbounded eliminationを適用する。論文のWasm実装・難読化耐性評価を確認した、という意味ではない。

本案は既知の巡回部分群を使う。論文の全自己同型群の軌道と常に一致するとは限らず、全対称性の保存をそのまま引用しない。残る差分候補は圧縮表現での具体的な消去条件と実行器の生成だが、現在の条件では通常のresolutionを対象bitごとに適用した結果をまとめる構成である。これは本研究の技術的な比較判断であり、論文が本案の全実装を既に提示したという断定ではない。

関連する [CDCL-inspired Word-level Learning for Bit-vector Constraint Solving](https://arxiv.org/abs/1706.09229)（Zakaria Chihani, François Bobot, Sébastien Bardin, 2017）も書誌・要旨を確認した。読んだ資料はプレプリントで、word-levelの伝播・学習を扱う。本文と査読版は未確認のため、具体的なrotate消去規則の一致は主張しない。

## 判断

この段階では独立した新原理として採用しない。rotate対応やSIMD実装を追加しただけの案を、新規候補として数えない。圧縮消去に固有の効果と、方式を知る解析者に対する追加費用を別途示せる着想ができた場合に再検討する。

有限環残差フィードバック方式の既存の限定採用は別件であり、本ゲートの結果で取り消さない。研究全体の完了を意味する記録ではない。
