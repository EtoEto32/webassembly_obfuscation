# 健全性の論証に必要な条件

2026-10-26。機械検証済みの定理ではなく、実装の検証項目を明確にするための論証案。

## 型関係の要点

Core GCは宣言されたsingle-inheritanceのsupertype chainを持つ。canonical同値を同一視した後、ある実行時型DがUとTの両方のsubtypeなら、UとTは同じchain上で比較可能になる。したがって、`struct.get U k`がprotected型T（またはそのsubtype）のobjectを読めるための必要条件は、`U <: T`または`T <: U`である。field kが存在すること、mutable fieldの型が適合することは標準validationに依存する。

Tのsubtype Dを生成できれば、Tを要求するtrusted APIへDを渡せる。従ってTの生成禁止はDの生成にも及ぼす必要がある。一方Tのsupertype Uの生成だけではTを偽造できないので、生成禁止は上方向へ広げない。read/writeとcreateで閉包の方向を分ける。

array.copyのsourceはread、destinationはwriteの権限を必要とする。arrayの長さは今回公開でありarray.lenに内容read権限を要求しない。これを長さの秘匿性の証明へ広げない。

## 合成に必要な前提

1. trusted libraryと各consumerは同じ仕様の型同値性・subtypingでvalidateされる。checkerとengineの不一致はこの前提を破るため、別engine照合を続ける。
2. loaderは受理した同一byte列だけを実行する。policyはtrusted libraryの正確な型定義と結び付き、guestが変更できない。
3. constructor/read/writeを実行する全untrusted moduleを検査する。検査後に別の無検査moduleへGC参照を渡すhost APIは許可しない。
4. 新しいGC命令やproposalを黙って受理しない。現在のvalidator feature setを固定し、全aggregate操作の効果を列挙する。
5. 承認されたimport APIの意味は別契約。trusted汎用serializer等がfield内容を返すなら、直接field操作を拒否しても情報は得られる。Oだけではそのようなconfused deputyを防がない。

## 不十分な点と反証テスト

現在の36組は上の全前提を証明しない。追加すべきものは、再帰group全体の同値性、packed field、array.new_data/elem、array.init_data/elem、global/element/tableのconstant expression、imported reference、policyなし、未知feature、subtype枝分かれ、複数protected型の同型衝突である。

特に**同じcanonical型を使う異なるownerの値は区別できない**。例えば両者が独立に定義した通常の`array (mut i32)`は同じ型になり得る。一方だけに「private内容」を指定すると、もう一方の通常のarray処理も拒否し得る。これは単なる実装漏れではなく、型だけを根拠にする契約の制約である。型brandingやorigin解析を追加した場合は、既知のnominality/ownershipとの比較と費用評価が別途必要。

安全性を得ること、受理集合の精度が十分であること、先行研究からの新規性の3点は別に判定する。
