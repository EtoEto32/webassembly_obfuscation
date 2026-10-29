# 静的lookupを有限体の多項式へ変換する規則

2026-10-21。既知の集合表現・補間を用いた実装仮説。独立した新原理の認定ではない。

## 入力と変換

入力は実際の`.wasm`。privateな非共有memory32を1page持ち、公開関数が
`lookup(i32)->i32`だけで、固定headから12byte recordのnext/key/valueを読む
単方向リストprofileを受理する。3フィールドの配置は任意の順列。関数AST全体を
照合し、dataを初期memoryへ配置してreachable chainを調べる。最大512 node。
cycle、範囲外、store、memory export、host import、別関数等は拒否する。
重複キーは最初の値を採用する。元の順序、未到達データは公開I/Oへ影響しない。
汎用C/C++または任意Wasmの変換器ではない。

p=4294967291=2^32-5 とする。k<pの一意なkey/valueを(k_i,v_i)とし、

```
P(X) = product_i (X-k_i)
L_i(X) = [P(X)/(X-k_i)] / P'(k_i)
R0(X) = sum_i (v_i mod p) L_i(X)
R1(X) = sum_i floor(v_i/p) L_i(X)
```

をF_p上で生成する。キーが相異なるためP'(k_i)は非零で逆元を持つ。
空集合ではP=1、R0=R1=0とする。k>=pの5種類は存在flagと値を直接保持する。
従ってこれら5キーの値は難読化していない。

```
transform(binary):
    validate and match the entire supported lookup AST
    instantiate initial bytes symbolically; walk and validate the pointer chain
    keep the first value of each unsigned key
    split off keys >= p
    construct P, R0, R1; discard the original records and next pointers
    emit one unsigned-i64 Horner evaluator and lookup below

lookup(x_i32):
    x = unsigned_extend_to_i64(x_i32)
    if x >= p: return saved exception value if present, else 0
    if Horner(P,x) != 0: return 0
    return wrap_i32(Horner(R0,x) + p*Horner(R1,x))
```

`poly-pruned`はR1の全係数が0の場合、その評価だけを省くアブレーション。
`array`はsourceから得た辞書を整列した8byte key/value配列へ置く対照。
どちらも既知の最適化で、別の発明に数えない。原データのfield配置・list順を
消すこと自体はarrayでも成立する。

## 意味保存

sourceは受理条件により有限のvalid nodeだけを読み、書き込み・callback・
trapは生じない。辞書のfirst-matchを保持すれば全i32引数で返り値が一致する。
有限体ではP(x)=0 iff xはいずれかのk_iである。根上でR0/R1は補間値に一致し、
R0+p*R1は元のu32値を表す。体に入らない5キーを剰余で潰さないことが必要。

Hornerのa,x,cは0..p-1。a*x+c <= p(p-1) < 2^64なので、Wasmのi64.mul/addは
この範囲では数学的整数積・和を保存する。非零pへのi64.rem_uはtrapしない。
private dataは最大512件でも1pageに収まり、全生成loadは範囲内。
元・変換とも1pageを確保する前提とし、時間・資源枯渇・debug情報の同一性は
契約に含めない。これは手作業の意味保存説明で、emitter全体の機械証明ではない。
[Wasm数値仕様](https://webassembly.github.io/spec/core/exec/numerics.html)のunsigned
remainder定義も確認した。Wasmが特別な因数分解困難性を与えるという主張はない。

## 解析タスクと攻撃

配布binaryと方式を知る解析者が、等価なkey/value辞書を回復する課題。
元next、元順序、元field名の完全再現は要求しない。秘密鍵・trusted hostなし。
private memoryも解析者に秘密とは仮定しない。

回復器は実data segmentから公開formatの件数・係数・例外値を読み、
Pを既知の等次数因子分割で線形因子へ分解する。各因子の根でR0/R1を評価し、
array形式の等価Wasmを出力する。各分割で(x+a)^((p-1)/2) mod Pとgcdを用い、
分割失敗の回数上限を持つ。得た線形因子を掛け戻してPと一致すること、根の
相異性、値域も検査する。root探索の乱数seedは攻撃側の公開値で生成器の秘密ではない。

入力はbinary・公開方式名・攻撃側seedのみ。source/manifest/元key/oracleは
回復プロセスへ渡さない。採点側が後から保存された正解辞書と照合する。
抽出器はこのformat専用で、汎用逆コンパイラではない。データformatの件数header
は保護機構でなく、次数は係数列やループ上限からも得られる。

正当な実行はO(n)回のHorner step。今回の素朴なPython因数分解にはそれ以上の
費用がかかるが、暗号学的困難性はない。NTL等の高度な実装なら費用が変わる。
「元のdecoderがない」だけを解析困難性の証明にしない。
