# 持続状態の非単射表現と公開応答からの回復

## 対象と保護目標

R=Z/(2^32)。初期状態0、公開API `reset()` と `step(u:i32)->i32` を持ち、stepは `x'=Ax+Bu, y=Cx'` を行う。source状態数nは2–8。状態はprivateなmutable i32 globalで保持し、呼出しをまたいで残る。外部memory、import、他の副作用やtrapはない。

攻撃者はbinaryと生成方式を知り、任意の公開入力を送れる。元source、A/B/C、U/D、seed、生成manifestは回復器へ渡さない。保護目標は、同じ入出力を持つ短い状態更新または漸化式の回復費用を増やすこと。元の変数名や元の全状態そのものの一意回復を要求しない。暗号学的な秘匿性を目的にしない。

## 変換

各座標に0≤s_i<32を指定し、D=diag(2^s_i)とする。以下を検査する。

```
if s_j > s_i: A_ij is divisible by 2^(s_j-s_i)
C_i is divisible by 2^s_i
```

これらの条件のもとで `G D = D A`、`h D = C` を満たすG,hを整数のshift/divisionから生成できる。ここで必要な割算は事前に確認した整数の割切れであり、Rで偶数の逆元を取る処理ではない。

Uは有限回の可逆な行加算から生成し、Uの逆行列も同時に計算する。出力する状態更新と観測は

```
z' = U (G+K) U^-1 z + U D B u
y  = h U^-1 z'
```

Kの各列jを2^(32-s_j)の倍数にすればKD=0。s_j=0の列は零にする。quotientはK=0、perturbはこの条件を満たすseeded K。basis対照はD=I,K=0で同じUを使う。plainは元の入力Wasm。

```
A,B,C = parse_and_validate_canonical_source(binary)
assert kernel_preservation_and_observer_conditions(A,C,s)
D = diagonal(2^s)
G,h = divide_only_after_checking_divisibility(A,C,s)
U,Uinv = elementary_shears(seed)
K = columnwise_annihilator(s)  # optional ablation
emit simultaneous i32 global updates using U*(G+K)*Uinv, U*D*B, h*Uinv
```

## 意味保存

E=UDとして、生成時に `A' E=E A`、`B'=E B`、`C' E=C`、`KD=0` を32bit剰余で厳密に確認する。z=Exが成り立つ時、任意の入力uについてz'=Ex'かつ出力一致。初期0とresetでも関係は成立するため、呼出し列について帰納できる。sourceの同時更新を一時local経由で保持する。

いずれかのs_i>0ならEは非単射で、全域R^nの状態を一意に復元する逆関数はない。核の大きさは2^(Σs_i)、像の大きさは2^(32n−Σs_i)。**これは全域の代数的な個数であり、実際の到達状態の個数や保護強度のbit数ではない。** 失われる状態差は将来の観測にも影響しないという条件がある。

この条件付き行列論証は、parserやcode generator全体の機械的証明とは別である。Wasmでは固定幅加減乗算が剰余で定義されるので、整数overflowの未定義動作を使わない。資源枯渇と実行時間の一致まで主張しない。

## 公開応答からの攻撃

既知上限N=8と、零初期・時不変・線形・状態更新後の線形観測というpromiseを置く。reset後に入力 `1,0,...,0` を2N回与え、h_0,...,h_(2N−1)を得る。内部stateを読む必要はない。

各r=1..Nについて、次の合同式を解く。

```
h_t = sum(a_i * h_(t-1-i), i=0..r-1), t=r..2N-1
b_j = h_j - sum(a_(i-1)*h_(j-i), i=1..j), j=0..r-1
```

最初に解けたrを採り、

```
y_t = sum(a_i*y_(t-1-i), i=0..r-1)
    + sum(b_j*u_(t-j), j=0..r-1)
```

のWasmを出力する。全応答が0ならr=0の零関数を候補とする。線形合同式では最小の2進付値を持つpivotを選び、奇数部分だけ逆元で除く。行・列基本変換を追跡し、零因子を非零の体要素のように扱わない。求まる係数が非一意でも、同じ応答を生成する一組があればよい。

これはReeds–Sloaneの全アルゴリズムを再実装したものではない。固定された小さい次数を順に試し、mod2^32の合同式を解く実装である。

## 2N個で十分になる条件の議論

この十分条件は既知の線形系・有理級数の議論から直接導くもので、数学的な新発見とは主張しない。元のインパルス応答の生成級数は `H(z)=C(I-zA)^-1 B`。分母Q(z)=det(I-zA)は次数≤n、Q(0)=1、分子Pの次数<nである。Rは体でなくても、定数項1の級数は形式的に可逆である。

候補の分子P'・分母Q'もdeg P'<r、deg Q'≤r、Q'(0)=1。先頭2N項の一致から `P Q'−P' Q` の先頭2N係数は零。この多項式の次数は<n+r≤2Nなので、全体が零となる。したがって全インパルス応答が一致し、線形性から任意の入力列で出力が一致する。

これは任意のブラックボックスに16問送れば同値性が証明されるという話ではない。非線形例外入力やNを超える遅延系は同じ16応答を返して後から違い得る。実際に両方を反例として保存した。

## 前提の別検査

`certify.py`はraw/O3の全命令を有限環の一次式として記号実行し、private零初期global、零reset、時不変線形性、状態数、更新後の状態だけによる出力を確認する。folded WATに残るoperand stackとlocal.teeも順序通り扱う。この検査は公開I/O回復器の後の独立監査であり、行列は回復器へ渡さない。

今回の全24条件はこの検査を通った。判定器は限定した命令profile向けで、未対応命令を含むプログラムの線形性一般を決定できるとは主張しない。
