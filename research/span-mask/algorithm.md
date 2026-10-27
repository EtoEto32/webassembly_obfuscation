# アルゴリズム、意味保存、保護目標

2026-10-23。事前仮説は[plan.md](plan.md)。実装は[prototype.py](prototype.py)。

## 表現

Boolean式の真偽をGF(2)上の「targetが行の線形包に入るか」に移す。i32の32bitは独立した32組のBoolean入力である。各係数をBoolean多項式環GF(2)[x]/(x_i²=x_i)の単項式集合で保持する。

```
compile(expr, v):
  literal x または not x: 行 (x*v または (1+x)*v) を追加
  OR(a,b): compile(a,v); compile(b,v)
  AND(a,b): fresh coordinate e; compile(a,v+e); compile(b,e)
  XOR(a,b): (a AND not b) OR (not a AND b) へ展開
target = e0
rows = compile(expr, target)
repeat selected elementary shears:
  row b += c(x) * row a, a != b
  または column b += c(x) * column a, a != b
  column操作はtargetにも適用
係数多項式を展開・相殺し、表と汎用membership evaluatorを出力
```

対照はspanのみ、全c=1の固定混合、c=入力変数を追加する入力依存混合。後2者は生成seedと操作位置を共通にする。入力依存版にも固定混合prefixがある。係数を展開してから配布するため元式・元ゲート・生成列は必要ない。ただし係数表自体は公開情報である。

## packed消去

各行・各pivot位置について、`a = v[j]`、`new = a & ~basis[j][j]`とする。j以降の係数について新pivotを`basis[j][k] ^= v[k] & new`で追加し、`v[k] ^= a & basis[j][k]`で消去する。basisは毎回ゼロから開始する。targetを同様に消去し、全係数のORのNOTが結果となる。

各bitに投影すると通常のGF(2)消去である。32laneのpivot位置が異なってもmaskにより区別される。`if a`は全laneがゼロの処理だけを省略する。費用は概ねO(m d²)のmask命令に係数評価が加わる。これはGaussian eliminationやSWAR自体の新規発明ではない。

## 意味保存の根拠と限界

ORでは片方がtargetを張ればよく、ANDで導入した固有座標は両子の寄与がなければ打ち消せない。木構成について帰納的に元式とmembershipが対応する。各shearは入力を固定すると可逆で、行操作は行空間を、列操作は全行とtargetのmembership関係を保つ。したがって変換後も各bitの真偽は等しい。

生成したWasmでは係数・作業領域・basisを分離し、作業領域を毎回初期化する。有限の表アクセスと配列境界を生成時に決める。元プログラムはtotalで無副作用に限る。追加memory確保が失敗する資源不足、engine実装のバグ、実装全体の形式検証はこの議論の対象外。数学的構成の説明と実装のテストを混同しない。

## 攻撃モデル

解析者はWasm全体、係数表、kernel、方式を知り、実行・計測・最適化・書換えが可能。生成時の元式、seed、変換manifestは渡さない。目標は元の記述を文字通り当てることではなく、同じABIを持つ短いBoolean実装を再生成すること。回復器は元式を参照せず、採点時にだけ元式とのBDD digestを照合する。

直接BDD記号消去、係数空間での定数行消去、入力依存shearを探す逆簡約、公開I/Oからの全数学習を実装した。回復器は表だけを信じず、kernelのrawまたはO3を再生成しbyte一致を検査する。このfamily限定の認識は汎用decompilerの実力ではない。NotDec・WASMixer・LOKI本体の比較実行はしていない。

## 失敗条件

固定行混合は通常の係数消去で消える。入力依存混合にも単項式数を減らす局所逆変換がある。さらに各bitが独立なので、n変数の全真理値表は2^n/32回の公開呼出しで得られる。24入力の実測ではこれが有効だった。変数を増やせば全数問い合わせは増えるが、それだけで新原理・特許性・現実的保護優位が成立するとは扱わない。
