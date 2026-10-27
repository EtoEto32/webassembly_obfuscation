# 非線形更新を共同多項式へ展開する候補

2026-10-18。採用済み発明ではない。前回のNFA重なりは、対応の曖昧さを増やしても小さな等価DFAへ戻せた。今回は有限状態の列挙を避け、32bit整数の複数変数を使う反復計算を対象にする。

## 選んだ仮説

状態xを可逆行列Aによりz=A xへ移す。通常の「復号→元更新F→符号化」では元更新がそのまま残る。そこで生成時に P(z,u)=A F(A^-1 z,u) を完全に展開し、異なる出力が使う単項式を共有してWasm i32x4の係数ベクトルへまとめる。実行中に元の状態変数をいったん作る操作をなくす。

線形共役、変数符号化、多項式の共通項共有、SIMD化そのものは既知。差分の仮説は、反復領域全体の展開と係数列の共同実行によって、個別復号より小さい実行費用で、元の疎な非線形更新則の回復に追加費用を課せるかである。Wasm固有性は固定128bit SIMDによる実装・正確なmod 2^32意味にあり、新しい数学原理とは主張しない。先行のpoly encoding / IPとの独立性は未確認。

```
extract simultaneous polynomial updates F and observation c*x
choose invertible A over Z/(2^32), compute B=A^-1
P <- expand and combine coefficients of A * F(B*z, u)
for each distinct monomial m in P:
    emit coefficient_vector(m) * splat(m(z,u))
sum vectors to obtain the next carried state
emit observation (c*B)*z only at the original output boundary
```

## 比較と反証

比較は元のscalar、同一vector lowererによる恒等基底、明示的decode/update/encode、展開した共同更新。raw/O2/O3を測る。入力は公開memory上のbyte列、状態初期値は0、出力は一つのi32。初期化時に行列全体を公開するABIを避けるが、解析者は全バイナリ・方式・係数を読める。秘密鍵や暗号化による保証を前提にしない。

解析課題はコンパクトな同値更新則の回復。元の行列Aの完全復元は必須ではない。特に公開された出力線形形式を、更新多項式の線形結合から逆にたどる解析を試す。非線形shift-registerでは、元状態の過去値が線形に移動するため、この経路が有力。一般の多項式ループに対する解析未対応は保護成功としない。

成功条件は、既知構成から区別できる具体的規則とその増分効果が、同じlowerer・同程度の費用の対照に対して支持されること。展開で式が大きくなっただけ、係数抽出器が未対応なだけ、元と同じ状態名が消えただけでは成功にしない。

## 比較検討して今回は選ばなかった方向

1. 例外・継続による動的な戻り先の共有：Wasm固有の命令は使えるが、CPS / exception-based control-flow obfuscationとの具体的差が弱い。前のtyped-relayで安い要約が得られた問題も残るため今回実装しない。
2. 複数loadと利用式の共同計画：trap境界を保持する領域単位の計画が必要だが、通常のload coalescingとの差と、bit射影で戻した後の保護課題を未定義。幅を増やすだけの再試験をしない。
3. 非線形更新の共同多項式化：既知の基底変更だけでは足りないが、明示的decodeを消した後の回復費用を実バイナリから検査できるため今回の反証対象に選ぶ。

この3方向を3つの新発明として数えない。最大のReject理由は、多項式符号化の既知手法に対して、SIMD実装上の差しか残らないことである。
