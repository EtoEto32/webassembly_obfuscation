# 先行研究との具体的対応

2026-10-22。新しい一般原理を得たとは主張しない。

Filippo Bonchi, Marcello M. Bonsangue, Helle H. Hansen, Prakash Panangaden, Jan J. M. M. Rutten, Alexandra Silva, **Algebra-Coalgebra Duality in Brzozowski's Minimization Algorithm**, ACM Transactions on Computational Logic 15(1), Article 3, 1–29, 2014。査読済み。書誌は[ACM発行元](https://doi.org/10.1145/2490818)で確認。[著者公開PDF](https://www.cs.mcgill.ca/~prakash/Pubs/BrzMin.pdf)の要旨・導入・§2–4の関連定義、反転構成、Theorem 3.1、Corollary 4.1を確認した。公開PDF表紙の年・DOIはplaceholderなので書誌には使わない。全29頁を精読したとは記録しない。

同論文の§3は状態集合の部分集合Sを状態とし、記号aの前像で更新する。初期状態を最終判定に、受理集合を初期状態へ移す。この部分集合をbit vectorで書くと今回の`T_a(v)_q=v_δ(q,a)`になる。§4は反転と到達可能部分の取得を2回行う最小化を述べる。今回の観測関数の合成閉包も、この既知の反転・可観測性と近接する。本文の結果は理論的な正当性であり、Wasm難読化の性能評価ではない。

今回追加したものは、非線形Eを含む遷移・観測関数のANF生成、閉じたWasm profileの受理検査、binaryだけからの回復、実測比較である。一般の状態符号化、既知の反転、およびANF展開の組合せから独立した発明性は確立していない。「同じWasm実装を未発見」は新規性の根拠にしない。既存の[suffix-transport](../suffix-transport/prior-art.md)とも状態からsuffix受理情報へ移す方向が近く、独立原理の新候補として重複加算しない。

最大のReject理由は、数学的な核が既知の反転構成であり、明示的逆変換を消した差分も観測関数の閉包で処理できること。今回の全18条件で回復し、小さな3例の実行費用は元版の約1.17–11.29倍だった。解析が少し重くなることは否定しないが、独立した新規性や良好な費用対効果を支持する結果ではない。

全特許公報・全請求項の網羅検索を行ったとは主張しない。この判断は本候補の研究上の採否であり、特許性の確定判断ではない。
