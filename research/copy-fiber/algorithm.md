# コピーの固定点と残差座標による表現変換

## 定義と意味保存

h,wは各8個のi32値。以下の+はXORであり、通常の整数加算ではない。

```text
C(h,w) = (h,h)
E(h,w) = (h, h + g(w+h))
E^-1(h,y) = (h, h + g^-1(y+h))
```

gは8語上の全単射でg(0)=0とする。逆写像の式からEも全単射。
E(C(h,w))=(h,h+g(0))=(h,h)=C(E(h,w))。よってこの固定コピーだけは
表現を変えても同じmemory.copyで実行できる。任意のgについて成立する
一般のcopy最適化ではなく、g(0)=0と、hを保存してwをhへ上書きする
冪等操作に依存する。非可逆なコピーの逆写像を仮定していない。

生成するgは、i,j,kが相異なる以下のshearを8個または16個合成する。

```text
x[i] ^= rotl32(x[j] +_32 x[k], r)
        XOR (x[j] AND rotl32(x[k], s))
```

+_32はmod 2^32加算。各shearは更新先を右辺に含まないため自己逆で、
全体の逆はshearを逆順に実行する。零入力の右辺は零である。
線形対照では右辺をrotl(x[j],r) XOR rotl(x[k],s)に替える。
32bit実装で非線形性を破る具体的入力対をaudit.jsonへ保存した。
可逆shearを新しく発明したとは主張しない。

## Wasmからの変換

```text
validate input Wasm
require: no imports, exactly private memory(1,1), compress:(i32^24)->i32^8
require prefix: store parameter H[0..7]; copy [0,32) to [32,64)
require rest: straight-line i32 operations, constant aligned addresses
require: H is read-only after copy; writes only to W
construct g and g^-1 with the zero-fixing shears
leave prefix copy unchanged
replace each load W[i] with H[i] XOR g^-1(Y XOR H)[i]
replace each store W[i]=v:
    r = g^-1(Y XOR H)
    r[i] = v XOR H[i]
    Y = H XOR g(r)
validate output Wasm
```

変換器は実際の.wasmを入力にし、WABTの検証・folded WATを介して変換する。
SHAソースそのものとのbyte一致だけを条件にするものではないが、上記の狭い
24入力/8出力profileに限定する。動的address、loop、分岐、callを持つ入力、
memory export、外部呼出し、共有memory、メモリ成長、異なるcopy、浮動小数点、
GC、SIMD、例外を受け付けない。変換出力の内部callは解析器が扱う。

毎回hを上書きしている間、以前のwに対する表現関係は維持しない。この区間でwは
使われず、importもtrapもない。続く固定copyでw=hという関係を確立し、その後は
上のload/store規則で不変条件を維持する。再入・共有・観測可能なprefix途中の
状態を許すとこの説明は成立しない。未対応を勝手に同値変換しない。

全addressは固定1page内の整列した0..63byteなので入力値によるOOB trapは
生じない。整数演算はi32のwrapを保存し、shift量はWasmのmod32規則に従う。
private memoryには観測可能な外部副作用がない。診断版だけmemoryをexportして
表現関係を検査する。診断用export追加後のプログラムを元と同じ観測契約とはしない。

## 対象計算とWasm固有性

全64roundのSHA-256圧縮を実行する。入力は任意のchaining state8語とblock16語。
各roundの直前にworkを読み、次状態8語をstoreする。最終feed-forwardを加え、
multi-valueで8語を返す。padding、エンディアン変換とblock連鎖はJSで行う。
元のsha.js資産から定数を使用し、そのライセンスを保持する。

Wasmのmemory.copyのbyte意味論・private linear memory・固定幅演算を利用する。
数学的構成は他形式の固定memcpyにも移せるので、Wasmだけで成立する原理とは
主張しない。最適なSHAコンパイラの代替でもない。

## 適応的な解除

recover.pyは元ソース、g、seed、targets.jsonを読まない。与えたWasmのprivate
callを展開し、定数addressのメモリを記号値として追跡する。entry memoryは
未定値として扱い、最終出力からの依存が消えることを要求する。XORは項の偶奇で
相殺、定数演算をfoldし、可換演算の引数を正規化、共通式をDAGで共有する。
shearの非線形右辺を逆算・学習せず、同一の右辺を2回XORすることを消す。
出力に必要なDAGだけを、memoryも状態APIもない24入力8出力Wasmへ生成する。

解析器のinstruction上限4,000,000、call深さ64。非対応命令、symbolic address、
残る初期memory依存はunsupportedとして区別する。これは任意Wasmの解除器ではない。
