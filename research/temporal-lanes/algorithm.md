# 時間差を持つレーンへの変換

## 対象と保護課題

対象は、N個の32bit状態を持つ直列cascadeをT回更新する関数。段iは自分の旧値と、同じ論理反復で既に更新された段i−1の値を使う。段0は入力系列を使う。保護課題は、配布バイナリから元の段順・各段の更新則・係数を回復し、元の逐次cascadeを生成することとした。

元の一反復に属する状態を、変換後の異なる物理時刻へ移す。一つのv128には異なる論理反復の段を格納する。この変更は時間軸に対するもので、値の暗号化ではない。Wasmの128bit SIMD、固定レーン幅、shuffle、bitselectを利用するが、時間変更そのものは既知のsoftware pipeliningに属する。

入力profileは実バイナリからWATへ変換後、関数本体をcanonicalな形と照合する。エクスポートは`run(i32,i32,i32,i32)->i32`のみ、memoryは非共有・非公開の固定1page。段数Nは4/8/16。Tをunsignedとして16384以下か入口で検査し、範囲外は状態変更前にtrapする。import、途中のmemory操作、call、共有memory、例外、GC、浮動小数、任意の分岐・一般loopは対象外。任意のC/C++を変換するコンパイラではない。

各段の係数c_iと共通rotate量rを入力から読む。主実験は以下の3系列。

|系列|段更新 F_i(a,b)|r|
|---|---|---|
|0|rotl32(a·c_i+b,r)|7|
|1|(a XOR b)·c_i+rotl32(a,r)|12|
|2|rotl32(a+b,r) XOR a·c_i|17|

全演算はmod 2^32。初期状態は`(x XOR ((i+1)*0x10204081))+y`、時刻tの入力は`rotl32(z+t*0x9e3779b9,11) XOR y`。終了後にN状態をmemoryの先頭からi32で格納し、全状態のXORを返す。これらのprofile規約は解析者にも公開する。

## 変換手順

```text
transform(input.wasm, mode, seed):
    validate input and match the supported source profile
    infer N, F, coefficients, rotation from input
    preserve the entry guard
    initialize each stage from the original initialization
    choose a lane permutation within each group of four stages
    for physical tick t = 0 .. T+N-2:
        old = all stage states       # simultaneous old-value view
        for every stage i, in SIMD groups:
            predecessor = input(t) if i == 0 else old[i-1]
            candidate = F_i(old[i], predecessor)
            active = (i <= t) AND (t < T+i)
            next[i] = bitselect(candidate, old[i], active)
        commit all next states together
    undo lane order for final stores and XOR return
    emit and validate output.wasm
```

`scalar`は同じ時間変更をi32 localとselectで実行。`vector`は自然な段順で4段を格納。`mixed`は4段内の配置をseedで入れ替える。各段のpredecessorは自分のvectorまたは直前vectorから`i8x16.shuffle`で集める。新値を全組で計算するまで旧vectorを保持する。実験のmixedはseed37に固定。配置のランダム化を秘密鍵とは扱わない。

## 意味保存の根拠と限界

物理tick tを終えた段iは、元の逐次実行を`clamp(t−i+1,0,T)`回進めた段iの値を持つ、という不変条件を用いる。更新前の自段は必要な旧値、前tickの直前段は同じ論理反復の更新済み値になる。fill/drainのmaskが初期値と最終値を保持する。T=0ではN−1回の非活性tickを通り、初期状態を出力する。T上限によりT+N−1やphaseのunsigned計算はoverflowしない。

候補式は非活性laneでも計算されるため、Fにtrap・host callback・途中の観測可能な副作用がある場合へそのまま一般化できない。対象Fはtotalな整数演算のみ。入口trapは元と同じ位置に保持し、終了時に全状態を元と同じ場所へ格納する。途中の命令数・時間・local値は一致させない。

この帰納的説明はスケジュールのモデルに対するもの。Python変換器、WAT reader、Wasm実装全体の機械証明ではない。実装は有限の差分試験、縮小モデルの全列挙、別実行器、誤mask反例で検査した。

## 方式既知の回復

第一の解析はlocal/stackを記号的に追い、bitselectのmaskから各laneの論理段番号を読む。更新の乗算定数とrotate、shuffleのpredecessorを回復し、整合性を検査して元の逐次関数を生成する。

第二の解析はmaskの値を順序推定に使わない。物理ノードを`(loop入口のvector local, lane)`とし、shuffleからpredecessor辺を作る。外部入力を持つ一つの根から後続辺を辿ると段順が決まり、各laneの係数を元の順へ並べられる。mask構文はlocal.tee解決のため走査するが、数値は順序推定に渡さない。

両者は公開profileを知る専用解析で、一般の逆コンパイラや同値性判定器ではない。特に第二の解析はmaskの正当性を検証しない。任意の破損バイナリを同値なプログラムへ戻せるとは主張しない。元バイナリ・seed・正解係数は推定へ渡さず、推定終了後の採点にだけ使用する。
