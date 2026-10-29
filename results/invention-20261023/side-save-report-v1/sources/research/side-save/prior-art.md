# 先行技術との境界

2026-10-23。独立した特許性は未確立。検索対象は一般の保存・復元だけでなく、複数の復元点が異なる副情報を持つ構成を含む。

|資料|区分と確認範囲|今回との技術的関係|
|---|---|---|
|Namyoon Lee, Alexandros G. Dimakis, Robert W. Heath Jr., *Index Coding with Coded Side-Information*, [arXiv:1501.00077](https://arxiv.org/abs/1501.00077)、[本文](https://arxiv.org/pdf/1501.00077)、2014-12-31版|読んだ版はpreprint。Abstract、Introduction、§II、§III Theorem 1と証明を確認。線形副情報と共通送信を使う復元条件、および最小rankへの帰着を示す。数値実験・全Algorithmは今回未読、実装未実行|入口退避を共通送信、各prefixを受信者、現memoryを副情報とみなすと、今回の中心の線形条件は既知枠組みに対応する。nested順序を使う生成器・Wasm trap修復との同一実装は未確認だが、一般条件を新規とは言えない|
|Eimear Byrne, Marco Calderini, *Error Correction for Index Coding With Coded Side Information*, IEEE Transactions on Information Theory 63(6), 3712–3728, 2017、DOI [10.1109/TIT.2017.2687933](https://doi.org/10.1109/TIT.2017.2687933)、[出版社](https://ieeexplore.ieee.org/document/7887740/)|査読誌。出版社書誌・Abstractを確認。線形結合の要求と副情報を扱う一般化を記載。機関repository本文は405で取得不可、全文読了とは扱わない|D_jという線形要求へ一般化しただけでも独立した新規性にはならない。誤り訂正そのものは今回使わない|
|Daniele Cono D’Elia, Camil Demetrescu, *On-Stack Replacement, Distilled*, PLDI 2018、DOI 10.1145/3192366.3192396、[著者本文](https://season-lab.github.io/papers/osr-distilled-pldi18.pdf)|以前のloss-flag調査で導入・§5.2末尾・§5.3を確認。今回新たに全文を読んだとは数えない|現状態から値を復元し、足りない情報だけ残す考えが先行する。著者LLVM実装との性能比較なし|

リポジトリ内のprefix-repairは現memoryを修復の副情報に数えず、loss-flagは保存0にできるBへ制限した。本案は任意の選んだ可逆Bを維持し、現memoryの情報損失の順序に合わせて共有退避を生成する。この差分の実装・効果は測れたが、「異分野の既知index codingを、nestedなcopy列へ適用しただけ」と評価される可能性が最大の新規性上の弱点である。

`obfuscation index coding`、`checkpoint side information memory patent`、`nested side information linear index coding minimum`等で探索した。US8370609のcheckpoint/rollbackは検索leadに留まり、請求項を精査していない。該当結果が少ないことは新規性の証拠にしない。特許の網羅調査、権利判断、出願可能性の判定は未実施。

結論：全prefixへの意味保存と入口保存次元の削減を支える、検証可能な生成アルゴリズムとして残す。新しい強い難読化原理や有力な独立特許候補の確立とは呼ばない。全例が回復したという一点だけで工学的価値を否定せず、速度・保存量・code size・temporary・保護効果を別々に記録する。
