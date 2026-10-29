# 剰余表現とWasmの整数wrap

2026-10-23。これは既知RNCの移植規則を検査する成立性ゲートであり、新しい難読化原理の提案ではない。暗号の秘密性も想定しない。

## 対象と観測

実際の`.wasm`を入力し、単一export `run(i32,i32)->i32`にあるadd/sub/mul、定数、2引数からなる純粋な式を変換する。import、memory、global、source local、分岐、除算、float、SIMDは対象外。公開Wasm、規則、moduliを解析者に与え、短い等価i32式を回復することを解析タスクとする。元sourceや生成seedは回復器に渡さない。今回の実装範囲では追加trapはない。非ゼロ定数によるunsigned remainderしか生成せず、中間値はu64に収まる。

## 三つの規則

W=2^32、E(x)=(x mod m0,x mod m1)、M=m0*m1と置く。moduliは互いに素。CRTは[0,M)の代表を返す。

```
compile(expr, mode):
    if leaf: return E(unsigned_i32(leaf))
    a = compile(left, mode); b = compile(right, mode)
    if mode == repair:
        x = i32_op(wrap(CRT(a)), wrap(CRT(b)))
        return E(unsigned_i32(x))
    else:
        return (op(a[0],b[0]) mod m0, op(a[1],b[1]) mod m1)
run = wrap(CRT(compile(expr, mode)))
```

`odd`は(65537,65539)で成分演算する負の対照。M=4,295,229,443>Wでも任意のi32式には正しくない。例としてx=y=4,294,967,295の加算は期待4,294,967,294に対し4,294,705,147となる。これは本稿の規則の反例であり、先行論文の著者実装にバグを発見したという意味ではない。

`repair`は同じmoduliを使い、各演算でCRT復元、native i32演算、再符号化する。入力から各nodeまでの帰納法でcanonical E(word)が保たれる。ただし各nodeで平文のword値と元の演算を実体化する。既知のdecode/operate/encodeである。

`aligned`は(W,65537)で成分演算する。最終出力の下位32bitが元の多項式評価に一致する。**第2channelが各中間wordのcanonical encodingになるとは限らない。** 第1channelがword演算を保ち、他channelは整数liftの剰余を保持する。最終出力だけの不変条件で十分な対象へ限定している。

## 成立条件と解除

整数の代表をmod Mで同一視してからmod Wへ射影する写像がwell-definedなのはW|Mの場合。必要性は整数0とMがmod Mでは等しい一方、mod Wでも等しくなるにはW|Mが必要なことから従う。十分性はMの倍数を除いてもmod Wの値が変わらないことによる。これは既知の環の商の性質で、新しい定理とは主張しない。

さらにcanonical E(word)が全てのword加算・乗算で成分演算と可換になるには、各miがWを割る必要がある。この強い条件と、alignedの最終出力だけの条件を混同しない。互いに素なmoduliの積が2^32の倍数なら、その一つに2^32の因子全体が含まれる。そのchannelの下位32bitが論理値を与える。

`project`は純粋なstraight-line整数式をmod 2^32へ抽象解釈する。add/sub/mul、wrap/extend、2^32によるrem、下位mask、定数left shift、local値の追跡を扱う。他の非ゼロ定数remはopaqueにし、その値が0倍や32以上のleft shiftで消える場合のみ除く。副作用やtrapを消さないよう、全ASTの許可命令と除数を先に検査する。式に残るopaqueは拒否する。O3がrem内へ移したlocal.teeの定義も、評価順に追跡する。

6条件全てを元plainとbyte一致するWasmへ回復した。ただしこれは一般のWasm逆コンパイラではなく、上記命令集合の射影器である。O3単独で元式を回復したという結果でもない。repairの自動回復は今回測定していない。範囲制限、別符号化、非準同型補正、cross-channel操作を持つあらゆるRNS方式の不可能性は示していない。

## 修正履歴

v1の射影器は、出力下位bitに寄与しないodd remainderの部分木を走査せず、O3でその中へ移されたlocal.teeを見落とした。local 2の未定義参照で停止したため、実行失敗として扱った。部分生成物は`residue-wrap-v1`へ残し、保護成功には数えない。v2は不透明部分木も評価順に走査し、localの初期値0も登録する。監査にはこの配置の独立した回帰例と、消去してはいけないtrap等の8拒否対照を追加した。この記録は失敗後の追記であり、v1当時の生ログを再作成したものではない。
