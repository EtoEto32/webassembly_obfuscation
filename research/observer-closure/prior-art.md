# 先行研究・特許の確認範囲

調査日2026-10-23。検索結果の不存在を新規性の証明にはしない。以下は技術比較であり、請求項の有効性・権利範囲・登録可能性の判断ではない。

|文献|状態・所在|実際に確認した範囲と本案への関係|
|---|---|---|
|Eduardo D. Sontag, *Discrete-time polynomial systems with inputs and outputs: structure, reachability, observability, and minimal realizations*, 2026|プレプリント、[arXiv:2609.36423v1](https://arxiv.org/abs/2609.36423v1)、DOI10.48550/arXiv.2609.36423、9月29日提出|要旨、HTML導入のobservation algebra・co-transition、§2の設定、§4冒頭を確認。無限体上の観測代数・canonical realizationが既存の中核。本論文は1976年博士論文の更新であり、2026年に初めて生まれた原理とは扱わない。全証明は未読。有限環での本worklistそのものを述べたとは確認していない。|
|Lucian C. Iacob, Maarten Schoukens, Roland Tóth, *Finite Dimensional Koopman Form of Polynomial Nonlinear Systems*, 2023|査読付きIFAC-PapersOnLine56(2),6423–6428、[DOI10.1016/j.ifacol.2023.10.849](https://doi.org/10.1016/j.ifacol.2023.10.849)、[所属機関の出版版PDF](https://pure.tue.nl/ws/portalfiles/portal/315095639/1-s2.0-S2405896323012296-main.pdf)|要旨、§2.2、定理1と帰納構成の冒頭を確認。連続時間・三角形の多項式系について、元stateを含む有限持上げを構成。今回は離散時間・剰余環・元stateを含めない場合で相違するが、自動的な観測関数の閉包という発想は新しくない。論文実験は未再現。|
|Steven L. Brunton, Bingni W. Brunton, Joshua L. Proctor, J. Nathan Kutz, *Koopman Invariant Subspaces and Finite Linear Representations of Nonlinear Dynamical Systems for Control*, 2016|査読誌PLoS ONE11(2):e0150171、[全文と書誌](https://pmc.ncbi.nlm.nih.gov/articles/PMC4769143/)、DOI10.1371/journal.pone.0150171|要旨、導入の観測関数・Carlemanとの関係、本文末の限界と謝辞にあるstate recoveryへの言及を確認。全実験・証明の読了ではない。非線形stateを観測座標で線形化する原理の先行性を確認。|
|Harold Johnson, Yuan Xiang Gu, Michael Wiener, *Securing accessible systems using dynamic data mangling*|公開特許[WO2013142979A1](https://patents.google.com/patent/WO2013142979A1/en)、優先日2012-03-30、公開2013-10-03、出願人Irdeto Canada|書誌、請求項1・5–19、付録のfalling factorial表現・多項式逆元・nilpotent係数の箇所を確認。請求項1の中心は入力依存の置換多項式によるM-register配置。本案と同一の請求項とは認定していない。一方、固定幅有限環の多項式や係数消滅を使うだけで新規とする主張は避ける。family全請求項・法的状況の確認は未実施。|
|Robin Geelen, Ilia Iliashenko, Jiayi Kang, Frederik Vercauteren, *On Polynomial Functions Modulo p^e and Faster Bootstrapping for Homomorphic Encryption*, EUROCRYPT2023|査読会議、[DOI10.1007/978-3-031-30620-4_9](https://doi.org/10.1007/978-3-031-30620-4_9)|本リポジトリの[既読範囲記録](../dyadic-difference/prior-art.md)を再利用。著者博士論文収録章で読んだfalling factorial・縮約補間が回復器の基礎。今回は再読していない。暗号方式を提案へ転用したものではない。|

追加検索語：`Carleman finite rings`、`exact finite-dimensional polynomial Koopman invariant subspace`、`obfuscation Carleman`、`lumping 2-adic`、`site:patents.google.com obfuscation Koopman`、`site:patents.google.com obfuscation Carleman`、`polynomial observable finite ring realization`、`obfuscation monomial nilpotent`。

近い追加候補としてGhandaliほか *Automatic High-Level Data-Flow Synthesis and Optimization of Polynomial Datapaths Using Functional Decomposition*（IEEE TC、DOI10.1109/TC.2014.2345395）と、Sontag *On finitely accessible and finitely observable rings* を検索で発見した。前者は著者投稿の要旨・断片、後者は著者PDFの検索抜粋のみ。出版版本文を精査した文献として数えず、今回の成立証明の根拠にも使わない。

最大の反証は文献の類似だけではない。主12条件とreset削除後12条件で同等の小さい更新を回復したため、この構成を有力な特許候補とする技術的効果が得られていない。有限精度の観測閉包という実装上の差分は保存するが、独立した新原理・特許性を断言しない。
