# 構成、意味保存条件、回復方法

## 入力と構成

`x=sign_extend8(arg0)`、`y=sign_extend8(arg1)`、`z_i=a_i*x+b_i*y+c_i`、`i=0..3`。
出力は `sum_i w_i max(z_i,0) mod 2^32`。実装はWasmの`i32x4`積和・`max_s`・lane抽出で計算する。係数64 bytesを非公開の固定1page memoryから読み、書込み・import・grow・外部副作用は持たない。

```
D = [-128,127]^2
for channel i:
    signature_i = [z_i(x,y)>0 for (x,y) in D]
group channels by exact equality of signature_i
for each two-channel group (i,j):
    choose s,t in {1,2,3}
    B = [[1,t], [s,1+s*t]]
    (z'_i,z'_j) = B*(z_i,z_j)   # coefficient arithmetic at transform time
    (w'_i,w'_j) = (w_i,w_j)*inverse(B)
require all coefficients and weights fit signed i32
require 128*(abs(a'_i)+abs(b'_i))+abs(c'_i) < 2^31
emit the same SIMD operations with the new constants
```

det(B)=1なので逆行列は整数。生成器は入力WasmをWABTで検証し、原型またはBinaryen 133のO3原型とのAST一致を要求する。4 channel、2個ずつのgroupが実験profile。単なる非比例性や一部のテスト点の一致だけでは変換しない。

## 正当性

各groupでは任意のD上の入力で、全channelが正または全channelが非正となる。Bは非負成分なので、前者ではReLUは恒等、後者では両側とも0となり、`ReLU(Bz)=B ReLU(z)`。従って `w B^-1 ReLU(Bz)=w ReLU(z)`。

前段と混合後のaffine計算は保守的な絶対値上界でsigned overflowを排除する。後段の重み乗算・加算はmod 2^32でよく、整数恒等式をこの環へ写す。`max_s`の前でwrapを許すと符号判定が変わるため同じ証明は成立しない。浮動小数点では丸め順序の別検査が必要となる。

元fixtureの例は `1025x+512` と `1536x+2y+768`。整数範囲では同じ符号になるが、非整数点x=-1/2,y=1では値が-1/2と2になり同符号条件を破る。この反例を有理数で監査した。連続実数領域へ適用できるという主張はしない。

## 方式既知の回復

攻撃者はbinary、Wasm意味論、実装profile、有限入力領域を知る。元係数、元ソース、生成seed、混合行列、manifestを回復関数へ渡さない。実験ハーネスは正解照合のために元fixtureを保持するが、回復器の入力とは分ける。

```
extract transformed affine coefficients and weights from binary
rediscover exact sign groups over all D
for each group G:
    choose a small affine predicate with the same sign signature
      search triples in [-2,2]^3, omitting zero, in canonical order
      filter on 16 points, then verify all 65536 points
      if none exists, use a member's original predicate
    aggregate = sum_{i in G} w'_i*(a'_i,b'_i,c'_i)
    emit select(aggregate(x,y), 0, predicate(x,y)>0)
sort groups canonically and sum their results
```

元の4列を特定する必要はなく、groupごとの出力寄与を復元すれば保護対象の計算内容が簡潔になる。今回は全fixtureで小係数predicateが見つかり、2個の条件付きaffine式になった。plain・permutation・mixのraw/O3はfixtureごとに同一binaryとなった。これは限定profileの適応解析であり、汎用Wasm逆コンパイラでの成功率ではない。

## 費用と限界

混合後も実行命令の形は同じ。係数のbyte表現によりバイナリサイズは変わる。変換時にchannelごと65,536入力を列挙し、Pythonではsignatureを1点1byteで保存する。広い入力や高次元にはこの全列挙は拡張できない。

通常のO3だけでは係数が元へ戻らないが、方式既知解析のgroup発見・集約がそのまま適用できる。正しさを保証する同符号関係が、回復器にも使える不変量となった。係数数の増加だけを根拠に新しい解析耐性が生じるとは見込めない。
