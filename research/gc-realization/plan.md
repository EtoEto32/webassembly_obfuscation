# S候補: 型付きGC heapの実現手順

2026-10-27、実装・実験前の仮説。前turnはRの実生成器対照・入力実験・監査によるprogress。R主テーマの独自効果は不足。Sは構築できる型を一つ探すRから、指定された参照同一性・循環を持つ有限heapを実現する問題へ対象を変更する。独立した新原理を確立済みとは扱わない。

## 研究課題

各辺が型に適合する有限heap記述を、元の型を修正せずにWasm constructorとset命令で作れるか。Wasm GCではimmutable fieldを後から書けず、nonnull mutable fieldもconstructor時に値が必要。Java向けのfield代入や特別constructorによる任意heap構築を、そのまま標準Wasmへ移せない。

対応断片をfinal struct/array、scalar/packed、具体GC参照にまず固定する。外部からのGC seed、関数参照、subtyping、shared GC、descriptor、abstract nonnullは未対応と分ける。これは新規性・実用性を立証するための最初の限定実験であり、全Wasm対応で完了としない。

## 仮説

対応断片で、(1)全node型が有限構築可能、(2)immutable参照辺だけのgraphが非循環、なら指定heapは一時的な値を使って構築できる。mutableのnullable辺はnull、nonnull辺は構築可能な同型seedで初期化し、全nodeを作った後で本来の参照へ更新する。immutable辺は目的nodeを先に作る。最終nodeは全て別objectで、指定IDだけがaliasする。一次型判定はRの既知worklistを再利用し、新規部分として数えない。

最終heapへ到達する途中の補助objectは許す。OOM、外部副作用、GC finalizerは対象外。書換え不能な参照cycleは、空storeから最初の構成要素を作れないため拒否する。nullableであっても最終値が非nullのimmutable cycleなら同じ問題がある。

## 反証と強い対照

Korat、generalized symbolic execution、constructor-based test generation、immutable object graph constructionとの先行性を検索する。単なるtopological sortと二段階初期化で十分なら、新しい一般アルゴリズムとしない。

対照は(1)全参照辺をconstructor依存とする再帰生成、(2)全fieldをnull/defaultで初期化後patch、(3)immutable辺toposort＋既知の型seed、(4)小規模での独立状態全探索。Sの核が(3)そのものなら、その事実を明記する。実装上の正しさと修士テーマとしての新規性を別に判断する。

## 検証

小規模の要求graphを列挙し、判定と独立な構築状態探索を比較する。成功例は実wasmへ出力し、元型・検証・最終辺・全node間ref.eqの関係を3engineで確認する。mutable cycle、immutable cycle、nonnull struct cycle、空array、同型だが別node、共有child、nullable leafを含める。seedの共有を最終nodeの共有と混同しない。

速度/生成サイズ/補助allocation/生成メモリを測る。実GCアプリの型に対する適用率も調べ、toy限定の成功を主テーマの十分性としない。
