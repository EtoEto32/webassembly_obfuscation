# 待機の観測集合を保存する表現

## 保護目標と契約

保護対象は共有メモリ内の二つのi32の対応関係。攻撃者はWasm binary、方式、ホストを知り、今回の公開store APIに選択値を書き、物理memoryを読める。暗号学的な秘密や解析不能性を仮定しない。評価タスクは物理語から元の二fieldの値を回復すること。汎用アプリの型推定精度は測っていない。

一つの固定1page共有memory32を8byte blockに分け、全参加者を変換する。初期状態はホストが開始前に符号化する。非atomic access、grow、data/start、外部関数、狭幅atomic、memory export等を拒否。i32のatomic load/store/add/sub/and/or/xor/xchg/cmpxchg、wait32/64、notifyを扱う。i64は純粋算術とwait64の引数に使えるが、元プログラムのi64 load/store/RMWは対象外。

保証を論じるのは、完了した操作の論理値・メモリ副作用・範囲／整列trapと、同じqueueアドレスでの待機比較である。CASによるstarvation、実時間timeoutの厳密な一致、追加stackや資源不足は契約外。テストは変換器全体の形式検証ではない。

## 比較の必要十分条件

blockの論理状態x、全単射E、waitが読むfield集合S、射影πSを考える。現在のmemoryを読まず、期待値tだけから期待物理値eS(t)を計算し、同じ幅・同じアドレスのnative wait一命令を使う場合、全状態で比較を保つ条件は

```
πS(E(x)) = eS(t)  iff  πS(x) = t
```

である。t=πS(x)を入れるとπS E=eS πSが必要。異なるtで同じeS(t)を許すと比較が誤るのでeSは単射。同じ有限集合上で全射にもなる。逆に、この因子分解とeSの単射性があれば比較は保存される。これはこの実装の適用条件を導いたもので、数学的初出を主張しない。

各Sについて、i∈Sならj∈Sとなる異なるfield i,jの組だけを使い、可逆更新 `x_i ^= f(x_j)` を許可する。Sにiがなければ射影は不変、iがあればjも含まれ、射影内の更新も逆変換できる。許された更新の合成は条件を保つ。これは構成の十分条件であり、途中で混ぜた依存を最後に相殺する全ての構成の必要条件ではない。

二fieldでは、両側にwait32があるならE(a,b)=(f(a),g(b))となり、cross-field依存を残せない。各f,gを恒等にする必要はなく、今回の簡単な試作では恒等を選んだ。wait64だけなら観測集合は全blockなので任意の全単射を使える。

## 試作の生成規則

rotは32bit回転。係数や回転数は秘密ではない。

| 成功し得るwait32アドレスの8byte内位置 | 表現E(a,b) |
|---|---|
| 0のみ | (a, b XOR rot(a,13)) |
| 4のみ | (a XOR rot(b,7), b) |
| 0と4 | (a,b) |
| wait32なし | u=a XOR rot(b,7), v=b XOR rot(u,13) |

const/AND/ADD/OR/XORのmod 8可能値を保守的に伝播し、未知の式は全剰余にする。memarg offsetを加え、正常に実行できる0/4の位置を集める。blockごとの最適化はせず、モジュール全体で一つの表現を選ぶ。

```
validate actual .wasm and reject unsupported instructions/sections
collect wait32 address residues; choose a compatible pair codec E
for each i32 atomic access:
    evaluate source operands once, pass them to a helper
    addr64 = unsigned(base32) + memarg.offset
    trap if addr64 > 65532 or addr64 mod 4 != 0
    block = addr64 & ~7; lane = (addr64 & 4) / 4
    oldPhysical = atomic.load64(block)
    repeat:
        logicalPair = inverseE(oldPhysical)
        old = logicalPair[lane]
        load: return old
        failed logical cmpxchg: return old
        logicalPair[lane] = original operation(old, operands)
        seen = atomic.cmpxchg64(block, oldPhysical, E(logicalPair))
        if seen == oldPhysical: return old (store has no result)
        oldPhysical = seen
for wait32: keep native instruction and expected value (this codec's anchor)
for wait64: keep native instruction/address and encode full expected word
for notify: keep address, count and instruction unchanged
```

64bit有効アドレスを検査してからblockへ丸めるので、offset加算の32bit wrapや不整列trapを失わない。page長は8の倍数で、正常な4byte fieldを含む8byte blockは範囲内にある。更新の実行点は成功CAS。失敗した論理cmpxchgとloadの実行点は観測したatomic loadまたは失敗CAS。全単射なので、同じ物理wordが戻るABAもこの値だけの操作ではその時点の論理値に対応する。pointer寿命の正当性を意味しない。

## snapshotでexpectedを作る危険な対照

cross-field混合したlow fieldへwait32を残し、直前の読出しから期待物理値を計算する案には競合がある。Eのlowを `a XOR rot(b,7)` とし、初期(a,b)=(0,0)でwaiterが0をsnapshotする。その後writerが(1,0x02000000)へ更新すると物理lowは0のまま。writerのnotifyはまだwaiterがいないので0を返す。waiterがsnapshotの0でnative waitすると、論理aが1なのに待機する。後続notifyが1を返し、waitは0で終了する。

元のwaitを更新より前へ置くなら最初のnotifyが起こすはずであり、更新後へ置くならnot-equalの1を返す。この履歴はどちらにも対応しない。実験ではprepare/commitの分割をスケジュール制御用に用いた。Wasmやエンジンの欠陥ではなく、素朴な表現翻訳の反例である。

## 解除方法と判断

選択対(0,1)、(1,0)を各2回のstoreで書き、四つの公開候補codecを識別する。逆shearで全メモリを戻せる。全24条件でこの有限族の同定が成功し、そのdecoderで全memoryを差分照合した。原ソースやmanifestのcodecは同定器へ渡さない。候補族外の任意表現を識別する一般的証明ではない。

幅と待機条件を保つ実装知見はあるが、安い公開逆変換は残る。CAS・shear・演算適合codecの既存技術に対する独立性、追加の保護効果は未確立。回転数を変えて再実験するだけでは、この失敗原因は変わらない。
