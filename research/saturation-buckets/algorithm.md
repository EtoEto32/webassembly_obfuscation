# アルゴリズムと成立範囲

## 変換

各論理レーンの範囲を0..L、L=2^b−1とする。物理レーンの幅は16、最大値M=65535、A=2^(16−b)。

```
D(Y) = Y // A
representation(x) = { A*x + r | 0 <= r < A }
```

全てのu16値がいずれかの論理値を表す。固定したE(x)だけを使う全単射符号化ではない。初期値としてAxだけを選ぶzero版、Ax OR dを選ぶbucket版を比較する。dは0..Lに制限され、b<=8によりd<Aなので、ORは下位部分だけを変える。

対象Wasmは、各byteから得たx,dをLへ制限し、段ごとに異なる定数mask mを使って、次を行う。

```
delta = d & m         # 0 <= m <= L
x = min(L, x+delta)  # 加算段
x = max(0, x-delta)  # 減算段
```

生成器は実際の入力binaryを読み、WABTでvalidateし、幅と更新maskを抽出する。抽出情報から原型を再生成しASTが完全一致することを検査する。閉じたprofile外をそのまま変換しない。

```
for each lane j:
    A[j] = 2^(16-b[j])
    Y[j] = A[j]*x[j] + permitted_initial_residue
    V[j] = A[j]*d[j]
for update (sign, mask):
    step = V & (A*mask)
    Y = i16x8.add_sat_u(Y, step) or i16x8.sub_sat_u(Y, step)
at exit:
    x[j] = (Y[j] * 2^b[j]) >> 16
pack eight byte results into one i64
```

Aは2冪なので`(A*d) & (A*m) = A*(d&m)`。固定定数の拡大は生成時、deltaの拡大は入口で一度だけ行う。laneごとにbを変えるため、出口はunsigned extended multiplicationでu32へ拡大し、16bit右shift、narrowで戻す。Wasmのnarrow命令へ大きいu16を直接渡す方法とは異なる。shift後は0..255なので、signed入力として解釈するnarrowの罠を避けられる。

## 意味保存の導出

Y=Ax+r、0<=r<A、M=A(L+1)−1と書く。

- x+d<=LならY+Ad=A(x+d)+r<=Mで、その商はx+d。
- x+d>LならY+Ad>Mとなり、native飽和の結果Mの商はL。
- x>=dならY−Ad=A(x−d)+rで、その商はx−d。
- x<dならY−Ad<0となり、native飽和の結果は0。

従って全Y、全d∈[0,L]について `D(sat16(Y +/- A*d)) = clamp(D(Y) +/- d,0,L)`。反復中にrが0やA−1へ変わってもよい。これは各更新に関する論証であり、WABT・Binaryen・実行器を含む生成実装全体の機械証明ではない。

2つの非正規化状態の加算には拡張できない。例えばA=4096、Y=Z=4095はどちらも0を表すが、Y+Zの商は1となる。この反例を監査に保存した。更新量側には余りを入れない、という非対称な条件が必要となる。

canonical対照は加算後に下位bitを消して常にAxを保持する。減算では、両入力がAの倍数なら飽和後もAの倍数なので補正を入れない。全段で無条件に補正する弱い対照との比較を主結果にしない。

## 適応的解析

解析者はbinaryを実行でき、レーン独立で、固定delta入力ごとの関数が飽和平行移動の合成であることを知る。元の幅・mask・段数・変換mode・source・manifestは学習器へ渡さない。

固定したdに対して各更新の加減量は定数なので、レーンごとの全処理は `f(x)=clamp(x+t,l,h)` になる。初期のxの制限もこの形である。合成でtを加え、端点l,hを次のclampへ通せば閉じる。この閉性は直接の式変形で、一般の非線形更新列へ拡張しない。

```
for byte d=0..255:
    lo = run(x=0,d), hi = run(x=255,d)
    if lo==hi: choose t=0
    otherwise:
        binary search the first integer k with run(k,d)>lo
        t=lo+1-k
    store (lo,hi,t)
```

8レーンを一つの呼出しに詰める。二分探索中のxはレーンごとに選べる。表は8×256×3個のi32で24,576bytes。回復Wasmは1pageのprivate memoryから係数を読み、各レーンで加算と2つのselectを行う。元の更新列や低bit履歴を復元しなくても同じ入出力が得られる。

一般コードではこの学習だけで正しさは分からない。byte rotationはbroadcast入力でidentityに見えるが、packed入力1では256を返す。学習されたidentityは1を返す。この実Wasm反例も保存した。今回の変換族がレーン独立であることは生成規則に基づく条件で、学習器が未知binaryから証明するものではない。

## 制限と保護上の解釈

商Dは単なる上位bit読取りなので、局所値の回復も安い。低bitに履歴が残ることを解析耐性とは扱わない。全modeの入出力学習が同じ問い合わせ数で済んだため、追加表現の自由度による保護上の利得は本実験では支持されない。

native演算とWasmのunsigned拡大・narrowの正確な意味を利用するが、同じSIMD命令を持つ他ISAにも応用できる。Wasmにしか存在しない原理とは主張しない。memory副作用、trap、import、NaN、共有状態を持つ入力は対象外であり、それらの保存を実証したという結果ではない。
