# 逆向き受理ベクトルと観測関数による回復

2026-10-22。検証済みの限定的な変換候補。独立した新規性・保護上の優位を確立できず、主発明には採用しない。

## 入力と変換

入力は、初期状態0の二記号DFAを表す定型の実`.wasm`。状態数3..10、非空の受理集合、privateな3要素funcref tableと4関数を持つ。公開関数は`run(word:i32,length:i32)->i32`。wordの下位bitからlength個を読み、unsigned length>32なら最初にtrapする。import、memory、global、追加export、任意の制御フローは非対応。入力全体を再生成したASTと照合し、範囲外のmoduleを拒否する。

元の遷移をδ(q,a)、受理集合のbit vectorをAとする。vの第q bitを「残りの語を状態qから読むと受理するか」と解釈する。逆順に記号aを読む更新は`T_a(v)_q = v_δ(q,a)`である。可逆Boolean写像Eで混ぜ、`G_a=E∘T_a∘E^-1`、`h(z)=(E^-1(z))_0`を生成する。

Eはseedで選ぶ2n個のToffoli型更新`bit_i ^= bit_j & bit_k`の合成。生成時にG_0,G_1,hの全2^n点を計算し、Möbius変換でANFへ展開する。生成物にはEのgate列や明示的な逆変換手順を入れない。各monomialは、bit積を0/1へ評価し、`0-term`でmaskにして係数vectorとANDし、全項をXORする。

```text
compile(delta, A, E):
    for z in 0 .. 2^n-1:
        v = inverse(E)(z)
        for a in {0,1}: table[a][z] = E(T_a(v))
        output[z] = v[0]
    emit ANF(table[0]), ANF(table[1]), ANF(output)
    emit run(word,length):
        if unsigned(length)>32: trap
        z = E(A)
        for i = length-1 down to 0: z = G_bit(word,i)(z)
        return h(z)
```

処理済みsuffixについてvが各状態の受理を表すという帰納的不変条件から、出力は元DFAと一致する。Eは全単射なので、この不変条件をz=E(v)へ移せる。length=0、length=32、範囲外trapを保つ。一般の副作用を持つWasmへこの証明を拡張していない。

## 攻撃モデルと反証

解析者は方式と公開binaryを知り、関数・table・定数を読める。元DFA、seed、Eのgate列、manifestは回復器へ渡さない。目標は同じ出力とtrapを持つ小さい前向きDFAの生成。ソースの変数名の回復や暗号的秘密の奪取は目標にしない。

回復器はhelperを静的評価し、出力関数hから合成`h∘G_a`の閉包を列挙する。関数の等値は全状態のtruth tableで判定する。新しいDFAの初期状態はh、受理値は各関数を初期符号化状態E(A)で評価した値となる。

```text
observers = [h]
for each g in observers, including newly added entries:
    for a in {0,1}:
        next = truth_table(g composed with G_a)
        intern next in observers
        emit transition(g,a,next)
accept(g) = g(encoded_initial_state)
```

この生成族では`h_q(z)=(E^-1(z))_q`とおくと`h_q∘G_a=h_δ(q,a)`。したがって初期h_0からの閉包は最大n関数であり、Eを分解しなくても元の到達可能状態を回復できる。Eの全単射性から座標観測関数は全領域で互いに異なる。今回の全到達可能・BFS番号付けされた3例では元binaryとbyte一致した。一般の状態番号付けでも同じbyte列になるとは主張しない。

Wasmの実driverについてはrawまたは所定O3後のcanonical ASTと照合する。helperは純粋な整数式のみに限定し、必要bitを後ろから解析して3..10bitの状態幅を求める。状態領域を出る遷移や非Boolean出力も拒否する。

truth table構築は幅に指数的である。今回の4/6/7bitの結果を大規模系への一律の安い攻撃と解釈しない。一方、変換器自身も2^n点とANFを生成し、サイズと実行費用が増す。単にEのgate数を増やすと閉包の小ささは変わらない。既知の反転・可観測性との関係は[先行研究比較](prior-art.md)に記録した。
