# 構成、許容範囲、意味保存

## 計算を一つの広い除算へ移す

元はu32のx,dについてq=x div d、r=x mod dを計算し、qを上位32bit、rを下位32bitへpackする。変換後はu64の除算結果Zの上位bitにq、下位bitにrに関する小数情報を置く。下位bitは最終結果に必要であり、前の飽和案のような不要部分ではない。

一般の幅wについてA=2^w、0<=x<A、1<=d<A、g=gcd(A,d)、B=A-d+g-1とする。

```
t = B AND rotl_w(x XOR d, 13)
Z = (A*x+t) div d
q = Z div A
r = (d*(Z mod A)+d-1) div A
return A*q+r
```

w=32でg=d&(-d)をWasmのi32演算で得る。Bはi32で`-d+(d&-d)-1`を評価すればよい。native `i64.div_u`は1個。xのゼロ拡張・32bit左shift、tのゼロ拡張・ORで分子を作る。後段はi64 AND、multiply、add、unsigned shiftで評価する。tは公開された決定的な値で、秘密鍵や暗号学的保証はない。

## 許容範囲の論証

**固定したdとt（0<=t<A）について、上式が全xで正しい必要十分条件は0<=t<=B。** これはすべての入力依存関数t(x,d)を分類する主張ではない。生成器はこの一様な十分範囲から各入力のtを選ぶ。

x=q0*d+r0、0<=r0<dと書く。K=floor((A*r0+t)/d)と置くと、t<Aから0<=K<AなのでZ=A*q0+K。したがってq=q0。

s=(A*r0+t) mod dとする。gはA,dを割るのでs≡t (mod g)。s>=t mod gであり、t<=A-d+g-1ならt-(t mod g)<=A-dである。従って

```
A*r0 <= d*K+d-1 = A*r0+t-s+d-1 <= A*r0+A-1
```

となり、r=r0。下界ではs<=d-1とt>=0を用いた。

必要性について、B<t<Aなら、A/gとd/gが互いに素なので、`A*r0+t ≡ t mod g (mod d)`となるr0を0..d/g-1から選べる。このときs=t mod g、t-s>=A-d+gだから、d*K+d-1>=A*(r0+1)。余りは誤る。dが2の冪ならB=A-1であり、範囲内のtは全て許される。

縮小幅2..6の全x,d,t、計294,128組でこの分類を検査した。w=32の30,000比較と、B+1の反例も保存した。有限検査を一般幅の証明の代わりにしていない。上記は算法の論証であり、Python/Wasm生成器全体の機械検証ではない。

## Wasmでの条件

u32のxとtについてA*x+t<=2^64-1。d,K<=A-1からd*K+d-1<=A^2-A-1。従って分子とdecoderに意図しないu64 wrapはない。Bの計算だけは意図したi32剰余算術を使う。

d=0では元のunsigned div/remも変換後のi64.div_uもtrapする。それ以前の追加演算は全域演算で、外部副作用を持たない。signed除算のINT_MIN/-1や符号付き剰余は対応範囲に含めない。

入力は実.wasmで、type/func/exportだけを持つ純粋なi32/i64 module。対応命令のloop/if/local/call等の中から、同じlocal.getまたは定数をoperandとするpacked div/remを見つける。対応箇所ごとにprivateなi64 localを追加する。operandの評価中にlocalを書き換える式は対象にしない。特定fixture全体のbyte一致ではないが、任意C/Rust binaryの全除算を変換するものでもない。memory、import、global、table、float、SIMD等は拒否する。

観測契約は呼出しの返り値とtrap。時間、fuel、call stack等の資源枯渇、デバッグ位置、custom sectionの保持は含まない。ホストとの副作用を含む任意文脈の同値性は主張しない。

## 方式既知の回復

攻撃者は方式・全binaryを知り、書換え可能とする。元binary、対応表、正解manifestは回復器へ渡さない。課題は等価な通常div/remの回復であり、元のlocal番号やソーステキストの一致ではない。

回復器はWABTの式から広い除算、上位・下位の利用、tの許容範囲式を照合する。O3のlocal.tee・共通化を閉じた算術式の中で追い、一時値が外へ漏れない、または外側の代入で直ちに上書きされることを確認してから通常のdiv/remへ置換する。誤った境界、誤decoder、外部から使われる一時値は拒否する。

```
for each closed arithmetic expression E:
    expand local temporaries within E, preserving evaluation order
    recognize Z=(A*x+t)/d and the exact output decoder
    certify the allowed t expression and temporary liveness
    replace E by pack(x div_u d, x rem_u d)
```

raw/O3の12条件全てが回復した。最初の回復器がO3のlocal共通化に対応していなかった6件は実装不足として修正し、防御成功には数えない。今回のパターン以外のO3変形に一般対応するという保証はない。

許容範囲の証明は、方式既知解析にとっても直接の書換え証明になる。部分計算の姿は変わったが、今回の生成器では局所的な対応を失わせていない。
