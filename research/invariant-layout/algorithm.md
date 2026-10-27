# 不変量から配置を求める表現と差分更新

4つの32bit語をx=(x0,x1,x2,x3)とする。h(t)=(t xor (t>>u13))&3、s(x)=Σh(xi) mod4。Rkは語の位置を右へk回転する作用で、保存表現をE(x)=R_s(x)(x)とする。

## 可逆性と更新

sは回転に不変なのでs(E(x))=s(x)。従ってE^-1(y)=R_-s(y)(y)であり、追加の配置表が不要。これは初等的な不変量と群作用の構成で、新しい数学原理とは主張しない。語の値自体は変更せず、値と論理位置の対応を変える方式である。

```text
read(y, i):
    k = s(y)
    return y[(i+k) mod4]

write(y, i, new):
    k = s(y)
    j = (i+k) mod4
    old = y[j]
    y[j] = new
    return R_(h(new)-h(old))(y)
```

書換え直後のyは旧配置kにおける新しい論理データx'である。s(x')=k+h(new)-h(old) mod4なので、差分だけ回転するとE(x')になる。full対照はE^-1→通常位置で更新→Eを実行し、transportと同じ境界表現を持つ。fixed対照は常に1語回転する。

Wasmではv128.load、i32x4の等値mask、v128.bitselect、i8x16.swizzleを使う。差分回転の添字はbyteごとに15でANDして0..15へ収める。単語取得は最初の4byteだけをextractするため、それ以外のswizzle laneが0になっても結果に影響しない。

## 意味保存の前提

単一のprivate・非共有・固定0～2ページのmemory32、i32.load/storeのみを対象にする。アドレスが4の倍数になることを定数、AND、定数shift等の保守的な構文規則で証明し、即値offsetも4の倍数に制限する。関数内の通常のi32計算・local・if/loopとtrapを扱う。import、global、call、memory export、grow、bulk、atomic、任意の非整列アクセス、浮動・GC等は拒否する。汎用Wasm全体への対応ではない。

元アドレスをunsigned i64へ拡張してから即値offsetを加える。storeの値を含めた元のoperand評価を終えてから、helperで4byteの範囲を検査する。overflowをi32へwrapさせない。成功したアクセスの16byte整列blockは、ページ長が16の倍数であるため全体が範囲内。更新は最後のv128.store一回なので、先行する元store後に次のアクセスがtrapしても、論理メモリの状態を保つ。0ページは常にtrapする。

時間・fuel・追加helperのstack/resource exhaustion・trap PCや文言は同値契約外。共有memoryやhostの途中観測を許す変換ではない。解析者によるinstrumentationは許す。正当性の論証、モデル全探索、実binaryの有限照合を区別する。

## 方式既知攻撃

配布binaryから、引数i64→i32とi64,i32→voidのアクセスhelperを型で見つける。memoryとhelperを計測用にexportし、既知の固定配置・動的配置の2モデルについて、それぞれ256組のblock、位置、更新値で照合する。各組はreadとwriteを一回ずつ行うので、全方式で1,024問い合わせを使う。

一致したモデルを用いて初期dataを通常配置へ戻し、helperを範囲検査付きの通常load/storeへ置き換える。元ソース、seed、manifest、元データは攻撃入力にしない。これは特定の生成族に対する候補同定であり、任意の改変binaryが全入力でモデルと一致することを保証する検証器ではない。候補は元プログラムとの独立した有限差分試験で評価する。

今回の生成器ではO3後も同定可能なhelperが残り、18/18条件から候補を作れた。helperを隠すだけでこの問題が解決するとは考えない。公開されたs(y)は、全メモリをどの時点でも安く通常配置へ戻す手段でもある。
