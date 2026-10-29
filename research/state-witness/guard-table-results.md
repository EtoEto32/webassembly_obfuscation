# memory/tableを共通化した条件合成

2026-10-24。[実装前の計画](guard-table-plan.md)、[実装](guard-table.py)。memory版を変更せず、同じ既知の等式抽象をfuncref tableへ拡張した。新しい原理の候補を一つ増やしたとは数えない。

## 条件と参照の扱い

memory byteとtable slotを資源番号・位置で区別する。値はbyte、null、元function indexからなる参照定数に分け、異なるsort間のcopyは受理しない。外部参照を注入しない閉じたmoduleが前提である。API終了時の契約は結果・memory全体・全table内容の一致で、segment寿命だけが異なる初期状態対を扱う。任意の元API列を許すが、hostからの外部書込みは列に含まない。

定数table.init/copy/fill、elem.dropを受理し、multi-table copyと重複copyも扱う。固定容量、最大1memory/4table、1操作128位置、footprint256位置、状態対/反復1024という制限は残る。動的address、間接call、loop等は未対応である。式の必要十分性は[論証](guard-proof.md)の限定契約に限り、より弱い非公開stateのcontextual equivalenceまで判定しない。

## 結果

|集合|条件合成の結果|確認した範囲|
|---|---|---|
|[自作table対照12例](../../results/state-witness/guard-table-controls-v1/results.json)|null/異なる関数/overlap/multi-table/0長/符号なし境界を含む|144初期store、Node/Wasmtime各6,758 API呼出し。一致|
|[公式由来67状態対](../../results/state-witness/guard-table-corpus-v1/results.json)|全store一致41、満たすstoreなし14、未対応12|memory版で受理済み17対の条件と分類は不変。今回の表は静的適用結果|
|[実測由来18状態対](../../results/state-witness/guard-table-context-v1/results.json)|全store一致14、条件付き2、満たすstoreなし2|memory版で未対応だった7対を受理。条件付き2対の式は不変|

公式67対は以前の具体状態closureと同じ41/14/12になった。今回の主な追加は、固定した具体storeに限らない条件を出す点であり、分類件数の増加だけを新規性とはしない。公式集合には条件付き例がなく、条件付きの動作確認は自作例と実測由来のmemory例に依存する。

[Wasmtime追試](../../results/state-witness/guard-table-cross-v1/results.json)のtable比較は、101/202を返すことを原binaryで確認した純粋関数のtagに限定した。12,365回のtag呼出しはAPI呼出し数に含めない。Nodeは同じinstance内のexport関数とのidentityを比較した。一般のWasmtime関数参照の同一性を検査したとはしない。

## 別の数式による検査

[array検査器](guard-table-check.py)はStore/Selectで効果を再記述する。初期cellはmemoryなら0..255、tableならnull又は同じmoduleの関数定数に制約する。parserは共有するため、完全に独立した検証系ではない。

自作12条件33義務、公式55条件55義務、実測18条件36義務の**計85条件・124義務がUNSAT**となった。条件を弱めた16対照ではSATを得た。UNSATは各APIの帰納的な十分条件であり、Wasm意味論全体に対する機械証明ではない。重複するmemory条件があるため、memory版の件数と単純に足して独立例数としない。

## 再現

```powershell
python research/state-witness/guard-table-controls.py results/state-witness/local-table-controls
python research/state-witness/guard-table-cross.py results/state-witness/local-table-controls results/state-witness/local-table-cross
python research/state-witness/guard-table-corpus.py results/state-witness/spec-v4 results/state-witness/disjoint-v1 results/state-witness/guard-corpus-v1 results/state-witness/local-table-corpus
python research/state-witness/guard-table-context.py results/state-witness/cut-inputs-v1 results/state-witness/context-inputs-v3 results/state-witness/cut-v1 results/state-witness/guard-context-v1 results/state-witness/local-table-context
python research/state-witness/guard-table-check.py results/state-witness/local-table-controls results/state-witness/local-table-check
python research/state-witness/guard-table-check.py results/state-witness/local-table-corpus results/state-witness/local-table-check-corpus --spec results/state-witness/spec-v4
python research/state-witness/guard-table-check.py results/state-witness/local-table-context results/state-witness/local-table-check-context --spec results/state-witness/cut-inputs-v1
```
