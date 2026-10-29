# 先行研究と新規性の評価

調査日2026-10-23。本文の閲覧範囲と著者の評価結果を、自分たちの実測と分ける。

|文献|区分・書誌|閲覧範囲、関連する内容、限界|
|---|---|---|
|Synchronizing weighted automata|Szabolcs Iván。AFL 2014、EPTCS 151, pp.301–313。[DOI:10.4204/EPTCS.151.21](https://doi.org/10.4204/EPTCS.151.21)、閲覧した版は[arXiv:1403.5729v3](https://arxiv.org/html/1403.5729v3)|abstract、導入、semiringの定義、Definition 1とその前後を読んだ。状態の行先だけでなく、語全体の重みも一致する同期を定義する。計算困難性の全証明は未読。論文の一般的な同期語探索の難しさを、今回の既知の語の評価に適用しない。実装を実行した比較ではない|
|Synchronization of finite automata|M. V. Volkov。Russian Mathematical Surveys 77(5),819–891 (2022)、査読誌。[出版社掲載ページ](https://www.mathnet.ru/php/archive.phtml?jrnid=rm&option_lang=eng&paperid=10005&wshow=paper)|書誌と検索で得た歴史記述のみ。本文全体は未読。同期オートマトンが古くから研究されることの補助確認であり、今回の算法の細部の典拠には用いない|
|VMSpec: A Decompiler-based Approach against Virtual Machine Obfuscation|Fabian Kilger, Leonard Auer, Manuel Andreas。2026-10-21公開の[arXiv:2610.29566v1](https://arxiv.org/html/2610.29566v1)。今回確認したのはpreprintで、査読済みとは認定しない|abstract、§3、§4の概要と§4.1、§4.2のmemory/call/specialization導入、§7.2のpath explosion・context・state identificationを読んだ。VM handlerからSLEIGHを生成し、147 benchmarkと追加6例で評価したという著者報告。自分たちでは実行していない。実装はTigress/Code Virtualizer向けで、context同定などに制限がある。未対応を今回の保護成功に数えない|

今回の重みは加算型なので、Ivánの定式化との対応を曖昧にしない。G=(Z/(2^32))^2とし、semiringを(P(G), union, Minkowski sum)、zeroを空集合、oneを{(0,0)}とする。各決定的辺にsingleton {(α,β)}を与えれば、語の経路重みは係数和である。全行が同じ列・同じsingletonになる条件は、既知のweighted synchronizationそのものになる。

従って「状態だけでなく計算も同期させる」という一般原理は今回の新発明ではない。限定Wasmへの生成、加算potentialで説明できない具体重み、同期による合流の原始操作という実装差はあるが、これだけで有力な独立特許候補とは言えない。今回の反証では代表状態から全体の同等計算が安く得られたため、主候補には採用しない。

`obfuscation synchronizing automata`, `code obfuscation synchronizing`, `virtual machine self synchronizing opcode`, `synchronizing automata obfuscation software patent`等を検索した。同名の暗号ストリーム同期や通信秘匿は今回の設計と同一と扱わない。関連特許の請求項を網羅比較した調査ではなく、検索で一致例が見つからないことを新規性の根拠にしない。VMSpecの公開contextモデルは本案の適応解析を考える材料にしたが、その実装を再現したという意味ではない。
