# 入力依存レーン移送と、1本の需要への縮約

## 保護仮説と対象

純粋な32bit整数関数の各中間値を、異なる仮入力に対する4個の値へ持ち上げる。正しい値を置くレーンは、演算ごと・実行入力ごとに変える。固定のlane 0を選ぶスカラー化では元計算へ戻らないことを狙う。Wasmの`v128`、`i32x4`演算、`i8x16.swizzle`を使う。暗号、秘密鍵、外部サービスを使わない。

変換器は実.wasmを受け取り、WABT validation後に命令を読む。単一のexport `run(i32,i32)->i32`、i32の定数・引数・local、add/sub/mul/and/or/xor、定数shift/rotateを受理する。純粋なblockとlocalの定義を展開できる。memory、table、global、import、call、一般CFG、例外、除算、浮動小数点は対象外。rawから変換し、出力にO3を適用する。任意Wasmを扱う完成パスではない。

## 生成規則

元の式DAGの節点nをF_nとし、仮入力kを `(x+k,y+3k)` とする。各節点にframe r_n∈Z/4を割り当てる。constant frameと、入力依存frameの両方を実装した。後者の具体式は、節点ごとの定数a,cとshift sを用いた `((rotl(x+a,s)) XOR (c*y)) & 3`。この形が秘密であるとは仮定しない。

不変式は次である。

```
V_n[i] = F_n(x+k, y+3*k), k=(i-r_n) mod 4
```

子のframeをr_child、親をr_parentとすると、`rotate(V_child,r_child-r_parent)`を使い、親のlane iへ子のlane `(i+r_child-r_parent) mod4`を置く。これにより両入力の仮入力kがそろう。pointwise演算を行い、最後にrootのlane r_rootを返す。

```
LIFT(node n):
    r = FRAME(n)
    if n is parameter x_j:
        base = splat(x_j) + [0,s_j,2*s_j,3*s_j]
        return rotate(base,-r), r     // s_0=1, s_1=3
    if n is constant c:
        return splat(c), r
    for child in operands(n):
        V_child,r_child = LIFT(child)
        aligned_child = rotate(V_child,r_child-r)
    return POINTWISE(op(n), aligned_children), r

return extract_lane(rotate(V_root,r_root),0)
```

32bit剰余演算なので、仮入力のoverflowは定義される。定数rotateはvector shift二つとORへ展開する。swizzleのbyte indexは `(byte_index+4*delta)&15` であり、常に0..15、4byteのword境界を保つ。この条件を外すとzero化やwordの部分交換が発生し、同じ意味保存説明は使えない。

実行上の追加費用は4laneの計算、frame計算、各辺のswizzle、入出力の変換。memoryやGC allocationは追加しない。元にtrap・副作用がない限定領域であり、未選択laneがtrapする一般コードへ無条件に広げない。

## 方式既知の解析

攻撃者はバイナリと方式を知り、元の式・seed・対応表・manifestを受け取らない。`attack.py`は実Wasmのlocal/teeをSSA相当のDAGへ展開し、許可した命令の意味で出力から要求laneを逆伝播する。変換profileを丸ごと再生成して一致を確かめる方式ではない。

lane indexはZ/4上の係数辞書として扱う。複雑なframe式は未知の原子のままでよく、同一式の加算・減算だけを相殺する。pointwise演算は同じ要求indexを各operandへ送り、word単位swizzleはindexを移す。vector定数は要求laneの定数に変わる。残る動的indexはselect式へ変換するため、無条件に0と仮定しない。

回復結果のDAGを共有したままlocalへ出力する。初期版のtree出力はrotateの左右shiftで同じ計算を繰り返し、解析・出力を膨らませた。主測定ではこの無駄を除いた。Wasm以外のSIMD ISAに対する一般解析器ではない。

## 1レーン需要の補題

上の生成規則では、rootに必要なlaneはr_root。節点nで要求がr_nなら、その子への要求は

```
r_n + (r_child-r_n) = r_child  (mod 4)
```

である。葉まで帰納すると、葉の最初の移送で `r_leaf-r_leaf=0` になり、元の入力へ戻る。同じDAG節点に異なる経路から到達しても、要求は同じr_nへそろう。frameの数値を解くことも、仮入力4本を全評価することも必要ない。

この補題は、動的frameを複雑にしたりlane数を増やしたりするだけでは防げない。ただし、任意のcross-lane演算や、別時刻の副作用を含むプログラムにも適用できる定理ではない。数学的な生成規則への説明と、Python/WABT/Node実装全体の形式検証を区別する。

## 次の判断に使う境界

位置が動くことと、複数の値を同時に推論しなければならないことは異なる。本案は全値の位置を正しく合わせる規則そのものが、解析者の需要も1本へ合わせる。単なる非線形なframe式の追加はこの弱点を解消しない。

次の候補では、実行可能性と意味保存を維持しつつ、出力の需要を逆伝播したときに1レーンへ閉じない機構が必要になる。複数レーンへ広がるだけでも十分ではなく、既知の線形基底回復等によって再縮約できないかを検査する。難しいframe式や大きい命令数を効果の代用にしない。
