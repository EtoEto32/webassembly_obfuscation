# コピーの情報損失に適合する符号化と現状態修復

2026-10-22。具体的な生成器・正当性条件の記録であり、新しい線形代数や新規な強い保護方式を主張しない。

## 問題と対象

N byteの論理状態xを、GF(2)行列Bを各bit面へ作用させたy=B xで保持する。コピーは行選択行列Cで表し、重なりもcopy開始時の値を選ぶ。列のprefixをP_j=C_j ... C_1、P_0=Iとする。nativeコピーだけをj個実行すると現memoryはy_j=P_j y_0だが、出口で必要な状態はT_j y_0=B P_j B^-1 y_0である。

以前のprefix-repairはD_j=T_j+P_jの全行に対する共通基底Vを入口で保存し、D_j y_0を修復する。入口保存値のみを使うという旧最小性の前提を、今回の現memory参照は満たさない。旧証明への反例とは扱わない。

入力は既存prefix-repairの厳密profileを再利用する。private memory32固定1page、先頭2..64 byteの初期data、正長・領域内の定数copyが1..16個、run(i32 fail)、復号した状態のdigest()->i32。failがjならcopy jのdstだけ65536として範囲外trapを発生させる。WABTでsource binaryを検証し、抽出情報から生成したcanonical sourceとASTが一致する場合だけ変換する。外部memory観測・書換え・imports・start・grow・shared memory・memory64・可変copy・一般関数は対象外。追加のmemory exportは試験専用である。

## 履歴なしで修復できる条件

現状態だけからT_j y_0を計算できる必要十分条件は

```
ker(P_j) ⊆ ker(T_j).
```

必要性：P_j y=P_j zなのにT_j y≠T_j zなら、同じ現memoryから必要な二つの結果を選べない。十分性：同じP_j像を持つ入力全てでT_jの値が一致するので、像上で修復写像を定義できる。これは通常の写像の因子化条件であり、今回初めて発見した一般原理ではない。

Bは可逆なのでker(T_j)=B ker(P_j)。両kernelの次元は同じであり、条件はBによるker(P_j)の保存と等価になる。P_jの各行は入力byteを一つ選ぶため、そのkernelは現在どこにも複製が残っていない入力位置の標準基底で張られる。生き残る位置集合S_jはjに対して単調に縮む。

各位置iについて、初めてS_jから外れるjをdeath_iとする。最後まで残る位置にはK+1を割り当てる。全prefixの条件は

```
(B^-1)[i,k] != 0 なら death_k >= death_i
```

と等価である。生存中の論理入力を、既に失った物理入力に依存させない。death順のblock三角行列族であり、Bも同じ族に属する。可換性B C=C Bは要求せず、実験で生成した6つのBはいずれも全ての個別copyと非可換だった。

## 生成と修復

```
validate source; recover data, N and fixed copy sequence
compute all prefix maps P[0..K]
derive death[i] from survivor sets
inverse = I
repeat 3*N times, seeded:
    choose i != k such that death[k] >= death[i]
    inverse.row[i] ^= inverse.row[k]
B = invert(inverse)
for each prefix j:
    for each survivor i, choose a current position rep[i] holding original i
    Q.row[i] = unit(rep[i]) if i survives, otherwise zero
    D = B*P[j]*inverse XOR P[j]
    W = D*Q
    require W*P[j] == D
    V = row_basis(W); find U with U*V == W
    repair[j] = (V,U)
encode initial data with B
leave all successful native copies unchanged
before a known failing copy j, apply repair[j], then execute that failing copy
after the last successful copy, apply repair[K]
```

各修復では、現在のmemoryからz=V y_jを**全て先に**読み、y_j←y_j+U zをstore8で書く。すると

```
y_j + W_j y_j = (P_j + W_j P_j)y_0 = B P_j B^-1 y_0.
```

Qは真の逆行列ではない。残った入力の代表を選ぶ部分的復元であり、失った値を0と置いてもDがその値に依存しないことを行列恒等式で確認している。情報を魔法のように取り戻す仕組みではない。

入口から保持する値は0。ただし修復中の一時値は必要。実装ではbyte情報をi32 localに格納する。rank(W)はこの線形補正に必要な独立な式数を与えるが、実CPUのregister割当・stack使用量の最小性を主張しない。全prefixの修復を別々に出力するため、コードが大きくなる場合がある。

## 意味保存と反例

memory.copyの範囲検査は書込みより前に行われるため、失敗するcopyの直前にj個の成功copy後の状態を修復すれば、trap後にdigestと次のrunが観測する状態を保存できる。repairの全アクセスは既に存在する先頭N byte内にあり、追加trapを発生させない。途中にhost callbackや外部memory観測がないことが必要。実時間・命令位置・stack trace・資源枯渇は観測同値に含めない。

全初期状態についての行列導出を示したが、Python parser/emitter、WABT、Nodeを含む処理系全体の形式証明ではない。小モデルは3byteの各値が0/1に限られる全8状態・全168可逆行列を3copy構造で調べ、107,520状態対を検査した。適合Bは8/24/24個、個別copy全てと可換なBは各1個であり、可換codecより広い族を具体的に確認した。

条件外のBでは、同じ現memoryなのに必要な出力が異なる入力対を保存した。trap prefixの修復を省くbad版12条件も全て反例が出た。正常終了だけの正当性では不十分である。

## 攻撃モデルと失敗原因

解析者は全binaryと方式を知り、最適化・instrumentation・実行を利用できる。seed・manifest・元sourceは回復器に与えない。保護目標は元のbyte表現とcopy操作列を、短い等価Wasmとして回復する作業の負担を増すこと。

既存のprefix-repair回復器を一切変更せずに適用できた。digestのXOR式からB^-1を抽出し、runのnative copyまたはO3のload/store、全fail区分の記号memoryを検査し、初期値を復号して元版を再生成する。12/12 current条件が元sourceとbyte一致し、同じBのbasisに比べて回復費用の増加も支持されなかった。公開decoderを維持したまま保存・修復の場所を変えても、この解析経路は変わらない。
