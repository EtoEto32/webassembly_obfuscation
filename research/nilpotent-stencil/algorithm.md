# 4点実行の設計、意味保存、回復算法

対象は`run(i32 x,i32 y)->i32`のみをexportするpureな整数DAGである。add/sub/mul、定数、local、分岐のないblockを受理し、その他の演算、memory、import、table、global、任意CFGを拒否する。WABTで実バイナリを検証・読取り・再生成する。custom/debug sectionの完全保存は保証しない。

## 核となる規則

R=Z/(2^32)、I=256RとするとI^4={0}。各入力についてd_x,d_y∈Iを選び、次を計算する。

```
X := i32x4(x+d_x, x+2*d_x, x+3*d_x, x+4*d_x)
Y := i32x4(y+d_y, y+2*d_y, y+3*d_y, y+4*d_y)
V := 元のadd/sub/mul DAGをX,Y上でレーンごとに評価
return 4*V[0] - 6*V[1] + 4*V[2] - V[3]  (mod 2^32)
```

constantはd_x=256,d_y=768。dynamicはd_x=-256*(x>>u10)、d_y=-256*(y>>u10)。diagonal対照はd=0でlane0だけを返す。実装は部分式の共有を維持し、元の高次数多項式を展開しない。

元入力でfを計算する専用レーンを置かない。しかしd=0になる入力や、異なる評価点で値が一致する入力はある。「すべての入力について元の値が一度も出ない」という主張ではない。公開入力x,yを秘匿する方式でもない。

## 意味保存の説明

固定したx,yについてd_x,d_yは定数として扱える。f(x+k*d_x,y+k*d_y)を形式的にkの多項式へ展開すると、次数jの係数はI^jに属する。j>=4は0なのでP(k)=a0+a1*k+a2*k^2+a3*k^3であり、a0=f(x,y)。重みw=(4,-6,4,-1)はΣw_i=1、Σw_i*i^j=0 (j=1,2,3; i=1..4)を満たす。したがって合成出力はa0に一致する。fの元の次数が4以上でも成立する。

これは整数環の恒等式による説明であり、Python parser・WABT・V8を含む機械検証済みコンパイラの証明ではない。通常整数演算だけの対象はtrapも公開副作用も持たない。一般のtrap、共有memory、資源不足、実行時間を保存するという主張には拡張しない。浮動小数、XOR、右shiftなどをfへ無条件に加えるとこの論拠は成立しない。

## 各レーンの非単射性

x=1024q+r (0<=r<1024)なら、lane kのx側入力は(1024-256k)q+rとなる。k=1..4について、x=1024とx=(4-k)*256は異なるが同じlane入力になる。実Wasmで4例を検査した。したがって任意の元xを一つのlaneから逆算する一般的な逆関数はない。複数laneをまとめた観測や公開コードからの回復を否定する性質ではない。

## 方式既知の回復

配布バイナリからlocalをDAG化する。各vector節点に次を付ける。

- kの各次数jの係数が2の何乗で割り切れるかという**下界**v[j]。32以上ならその項は0。
- k=0の定数係数を計算するscalar式C。高次係数の具体的な式は作らない。

```
vector_constant(a, a+d, a+2d, a+3d):
    C := a-d; v := {0:val2(a-d), 1:val2(d)}
splat(s): C := s; v := {0:known_trailing_zero_lower_bound(s)}
add/sub(A,B): C := C_A +/- C_B; v[j] := min(v_A[j],v_B[j])
mul(A,B): C := C_A*C_B; v[j] := min_{r+s=j}(v_A[r]+v_B[s])
discard coefficient entries with v[j]>=32

collect output coefficients w_i of extract_lane(i-1,V)
for every retained j>0:
    require val2(sum_i w_i*i^j) + v[j] >= 32
emit sum_i(w_i)*C_V plus any scalar constant
```

複数のvectorが線形合成される場合は各々の条件を検査する。constant vectorの等差性、scalar observationの線形性、演算の対応範囲を確かめ、条件が証明できないものを拒否する。最適化後の定数乗算がshiftへ変わる形にも対応する。元式・seed・生成ログを入力にしない。

本生成規則ではfの内部vectorの保持次数は最大3なので、係数の付値伝播は節点当たり定数個の組合せで済む。定数係数Cを伝播すると元の演算DAGへ戻る。高い元次数、入力写像の非単射性、4laneすべての利用は、この回復に元入力の逆関数や高次式の展開を要求しない。

## 見直しの判断

全件回復自体を難読化失敗とはしない。測定した増分費用と技術差が採用判断の根拠である。ただし、方向関数dを複雑にするだけの改良は、dの付値だけを知ればよい本解析を複雑化しない。高次化やlane数増加だけを新候補として続けない。次の方式には、評価点0への安い代数的射影を強制的に残すかどうかの事前検査が必要になる。
