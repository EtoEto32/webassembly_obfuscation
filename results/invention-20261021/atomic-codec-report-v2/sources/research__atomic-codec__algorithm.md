# アトミック更新に両立する表現：構成と制限

## 対象と構成

一つの共有memory32内を32bitの整列cellへ区切る。各cellに同じ全単射 E を使う。すべての参加threadが変換後コードを使い、hostは起動前の初期状態だけを一度符号化する。data/start/grow/非atomic/異なる幅/外部関数/import以外のmemory/公開memoryは変換器が拒否する。memoryは固定1page。通常のi32計算・構造化制御・関数callを保持し、命令の引数を一度評価してhelperへ渡す。debug/custom sectionは保持しない。

```text
read and validate actual .wasm
reject unsupported state and memory operations
collect atomic operation footprint
if no bitwise atomic occurs:
    E(x) := a*x+b mod 2^32, a odd
    add/sub operand y := a*y; decode returned old value
else:
    E(x) := ~x
    add <-> sub, AND <-> OR with complemented operand, XOR unchanged
encode store/exchange values and both compare-exchange operands
decode all returned old values and atomic loads
emit helpers with the original memarg offsets unchanged
```

autoの符号化は二択であり、全codecからの最適選択器ではない。XORだけのprofileにも反転を選ぶ保守的な規則。affineの定数は秘密ではなく、現在は固定である。実装済みの生バイナリ変換と、限定profile上の保証を区別する。

反転では `~(x+y)=(~x)-y`、`~(x AND y)=(~x) OR (~y)`。旧値の復号はRMWが返した旧値に適用する。atomic.loadとstoreへ分割して旧値を取得し直すことはしない。CASはEの単射性により比較の真偽を保存する。元のmemargを残すため、32bitを超える有効アドレスやunaligned trapをwrapさせない。追加helperのstack/resource不足、実時間、trap位置・文言は契約外。

## 単一のnative opcodeに閉じる表現の制限

w>=1、R=Z/(2^w)、E:R->Rを全単射とする。次を全x,yで要求する。

1. ADDを、更新前値に依存しない引数g(y)を持つ固定したADDまたはSUB一命令へ写す。
2. ANDを、同様のt(y)を持つ固定したANDまたはOR一命令へ写す。

このときEは恒等写像または全bit反転だけである。これはこの研究内で導出した設計条件で、数学的な初出を主張しない。

証明：SUBをgの符号へ吸収する。条件1から E(x+y)=E(x)+g(y)。x=0を代入すれば E(x)-E(0) が巡回加法群の自己同型なので E(x)=a*x+b、aは奇数。

条件2のtargetがANDなら E(x AND y)=E(x) AND t(y)。x=all-onesを入れ、Eが全射であることから E(all-ones)=all-ones、t(y)=E(y)。またE(0)=0となる。従ってEはBoolean latticeの自己同型で、1bitだけ立つatomを置換する。E(1)=aは1bit値かつ奇数であるためa=1、b=0。targetがORならC(x)=~E(x)を用いて同じ議論が成立しC=id、従ってE=NOT。

CAS loop、複数cell、非全単射表現、実際の到達値のみへの制限、値によってtarget opcodeを変える構成には、この定理を適用しない。native命令を多く使うすべての難読化が不可能という結論ではない。

2～6bitの2,728 affine候補を分類し、各幅でこの二つだけが通った。棄却にはAND/OR双方の具体的反例を保存する。173,922のx,y検査は反例で打ち切る列挙で、全候補の全組合せを最後まで走査した数ではない。全語長の結論は上の証明に基づく。

## CAS対照と並行意味

```text
old := atomic.load(p)
repeat:
    next := E(op(E^-1(old), y))
    seen := atomic.cmpxchg(p, old, next)
    if seen == old: return E^-1(old)
    old := seen
```

成功CASを元のRMWの実行点に対応付ける。全cellが共有codecに従うとき完了した操作は正しい。元の一命令と同じ個別threadの進行保証はなく、競合によるstarvationを排除しない。ABAで同じwordが戻っても、wordだけを対象とする本更新ではその時点の値への作用が正しい。ポインタ寿命や複数cell invariantを保証する議論ではない。

## 解析者と失敗条件

全binary・方式・host、物理memoryを読める白箱解析者を想定する。評価APIには選択値を書けるstoreがある。0と1を書いた後の物理wordを観測し、b=E(0)、a=E(1)-E(0)を求め、奇数aの逆元から全cellを戻せる。元ソース・生成器の定数・正解memoryは識別器へ渡さない。回復後の照合にのみ正解を使う。

これは型復元器や一般アプリの閉じたAPIへの攻撃ではない。ただし今回の新規性・効果を支えるために選んだprofileでは、codec選択が保護を追加するという仮説は支持されない。今後この方向を再開するには、単なる係数変更でなく、この二点回復と一命令閉性の制限を変える具体的規則が必要である。
