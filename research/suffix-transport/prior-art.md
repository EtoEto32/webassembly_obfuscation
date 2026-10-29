# suffix輸送候補：先行技術と発明差分の検査

2026-10-18確認。公開情報の読了範囲と今回の独自検査を区別する。新規性、進歩性、権利範囲についての判断書ではない。[特許調査全体](../patent/README.md)

## 一次資料の確認範囲

|資料・書誌|種別／読んだ範囲|今回に関係する内容・限界|
|---|---|---|
|Stefan Kiefer, *Notes on Equivalence and Minimization of Weighted Automata*, 2020, arXiv:2009.01217v1。[HTML](https://arxiv.org/html/2009.01217v1)、[PDF](https://arxiv.org/pdf/2009.01217)|プレプリントの講義ノート。§1、§2 Algorithms 1/2、§3 Theorem 3.7まで確認。著者自身が既知結果の再証明と明記。|重み付きオートマトンのrow/column空間、基底計算、共役と同値性・最小化。最も近い数学的枠組み。Wasm難読化の実測論文ではなく、今回の性能値の出典ではない。|
|W. Erik Anderson, *On the Secure Obfuscation of Deterministic Finite Automata*, 2008, IACR ePrint 2008/184。[掲載ページ](https://eprint.iacr.org/2008/184)|ePrint掲載版。書誌・抄録、PDFのp.2に関する一次検索抽出を確認。全文の直接取得は失敗。掲載ページは「他で出版、発表先不明」としており、査読済み発表先は未確認。|小さな秘密を保持するoracleと二者実行を用いるモデル。公開Wasmだけを渡す今回と前提が異なる。DFA保護という一般目的の先行性を示すが、未読の証明や性能評価は推測しない。|
|Emscripten project, *Using SIMD with WebAssembly*, オンライン技術文書、2026-10-18閲覧。[文書](https://emscripten.org/docs/porting/simd.html)|査読論文ではない。swizzleのx86への対応に関する表を確認。|範囲外indexのzero化の差により、一部runtimeで追加命令が必要になる場合を説明。今回のJIT出力を測った資料ではない。|

Kieferのアルゴリズムは、到達rowが張る空間の基底を計算する。今回実装したのは、DFAの共役という制約を利用して実際の有限row軌道を列挙する手順であり、同アルゴリズムの完全再実装とは称さない。同資料は計算量の議論で有理数体を仮定する箇所があり、そのbit計算量をGF(2)実装へ無条件に転記しない。

追加検索は `weighted automata obfuscation conjugation SIMD`, `reverse automaton obfuscation linear representation`, `finite automata matrix obfuscation patent` 等。*Weighted automata are compact and actively learnable* は出版社検索抽出のみで、全文・完全な書誌を今回確認できず採用文献にしなかった。Berstel/Reutenauerの書籍は出版社書誌と序文の検索抽出にとどまり、版・年の照合と本文確認が未完了。これらを読了済みの根拠にしない。

## 具体的構成の対応

|今回の要素|既知の枠組みとの関係|差として残るか|
|---|---|---|
|前向き状態からsuffixの受理条件へ変更|オートマトンの逆向き評価・column表現|単独では新規と主張しない|
|可逆Lによる共同混合|線形表現の共役・複数変数符号化|単独では新規と主張しない|
|B、LF、ellを生成しvへの境界を消す|生成時の行列積合成|既知の線形枠組みから独立した差を未確認|
|16lane swizzle/AND/XORへの実装|標準SIMD命令による有限行列・lookupの実現|動く具体例はあるがWasm移植だけで差を確定しない|
|厳密sourceテンプレート照合とtrap条件|実装の適用条件・意味保存の検査|必要な実装品質であり、そのまま保護発明の核とはしない|
|逆向き状態数の増加|実験では最大1,376状態|出力側rowは16状態へ閉じ、解析者へ同じ探索を強制しない|

前回読んだ [JP2008090668A等の記録](../patent/joint-relations.md)には複数変数のmatrix符号化や関係を使う記載がある。ただし本候補の逆向きDFA手順が公報の全構成と同一であるとは判断していない。本候補を直接対象とする追加の特許公報について、新たに請求項全体を読了できたものはない。検索で一致公報が見つからないことを新規性の証明にしない。

## 実装後の判断

[実測](README.md)は、混合を加えた場合の解析費用増加を示す。一方でO3実行は元の約12〜14倍で、既知の双対構成による回復は数msだった。比較器の実装依存性と他方式との同費用比較が未実施である点も残る。したがって新しい有効な主方式として採用せず、出願構成を確定しない。将来の候補については「同じ原理をWasmにした」という説明を超えて、生成規則の差がどの復元課題の費用を変えるかを検査する。
