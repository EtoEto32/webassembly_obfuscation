# 倍率とbinary32の丸め格子を同時に変える変換

## 表現と生成規則

元の各nodeの値をx_iとし、変換後はbinary64のv_i=2^p_i x_iで保持する。
各p_iは[-32,32]の整数で、shiftedでは0を除いて選ぶ。倍率は公開である。
元の演算の**直後ごと**に次の量子化を適用する。

```text
Q_p(v) = 2^p * RN32(v / 2^p)

for i in source topological order:
    if input: v[i] = exact_scale(promote_f32(input), p[i])
    if add/sub(a,b):
        u = f64_add/sub(exact_scale(v[a],p[i]-p[a]),
                        exact_scale(v[b],p[i]-p[b]))
        v[i] = Q(p[i], u)
    if mul(a,b):
        u = exact_scale(f64_mul(v[a],v[b]),p[i]-p[a]-p[b])
        v[i] = Q(p[i], u)
return demote_f64(exact_scale(v[root],-p[root]))
```

`Q`は内部でf32へ変換せず、f64のbit表現から対象格子への最近接偶数丸めを行う。
符号bit s、符号を除くraw bit a、格納指数Eについてe=E-1023-pとする。
零・無限大・NaNはそのまま。NaNの最終bit表現は元から存在するwrapperでcanonical化する。

```text
if e > 127: signed infinity
if e >= -126:
    b = (a + (2^28-1) + ((a >> 29) & 1)) & (2^63-2^29)
    if b >= (1151+p) << 52: signed infinity
    else: reinterpret(s | b)
if e < -150: signed zero
otherwise:
    r = -97-e                    # 30..53
    M = (a & (2^52-1)) | 2^52
    q = (M + 2^(r-1)-1 + ((M>>r)&1)) >> r
    return copysign(f64(q) * 2^(p-149), v)
```

最後の区間は対象binary32のsubnormal格子に対応する。qのcarryによる最小normalへの移行も含む。
f64自体のsubnormalは、この倍率範囲では対象最小値の半分より十分小さいため零の分岐へ入る。

## 意味保存の理由と限界

元の有限値はbinary32なので、倍率変更後もf64で正確に表せる。
pの範囲を制限したため、有限の中間値の指数はf64のnormal範囲に収まり、倍率調整自体のunderflow/overflowは生じない。
binary32同士の積は高々48bitの有効桁で、53bitのbinary64内で正確に表せる。
加減算についても、binary32入力をbinary64で演算しbinary32へ丸めるときの二重丸めが無害となる既知の条件を使う。
本案の二重丸めの安全性を新しい定理とはしない。[先行資料の確認範囲](prior-art.md)を参照。

直感的には、有効指数差が29以下なら必要な桁が53bit以内に収まる。
差がさらに大きい場合、小さい項は大きいbinary32値の隣接丸め境界まで値を動かせない。
subnormalも正規化した有効桁で同じ範囲を考え、対象subnormal格子への丸めをQで行う。
符号付き零・無限大・NaNは別に扱い、正の2の冪を使って零の符号を保存する。
この説明は実装全体の機械検証ではなく、各emitter・optimizer・JITの完全性を証明していない。

Wasmの通常数値命令は丸め規則が固定され、FP状態flagをプログラムから観測しない。
したがってhostの丸め状態を保存する処理を必要としない。ただし同じ性質を持つ他形式にも移植可能であり、
Wasmだけで成立する新原理とは主張しない。途中のreinterpretやraw NaN payloadを観測するAPIへは適用しない。
メモリ・整数変換・trapを起こし得る追加命令は入力profileから除外している。

## 適応的な解除

公開量子化器を別途compileしたprofileを用意し、targetには元DAGもseedも与えない。
helperのlocal.set/local.teeを代入し、条件分岐とreturnを保持した式のsignatureを照合する。
これは既知helperの認識で、任意のWasm関数の同値判定ではない。

各式に `(元node, 倍率の指数, 直前の丸め完了)` を付けて伝播する。
2の冪の乗算は指数だけを変更する。加減算は同じ指数の丸め済み入力を要求し、乗算は指数を足す。
Q呼出しでは引数の指数とQのpが一致することを確認し、保留した演算をf32 nodeとして確定する。
最後に指数0・丸め済みであることとcanonical NaN wrapperを検査する。
raw/O3の最終16条件すべてで、同じ順序の元DAGが得られた。

helperを見慣れない形に変えれば現在の復元器が未対応になる可能性はあるが、それだけを保護利得とはしない。
今回は方式の丸め境界と倍率が局所的に読み取れるため、構成の中心そのものが回復に使える。
同じ仕組みの倍率数を増やすだけの改良を次の独立発明には数えない。
