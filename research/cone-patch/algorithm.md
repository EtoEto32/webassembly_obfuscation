# 可逆混合レコードのread/write別局所更新

## 表現と対象

1レコードはN個のchunk、1chunkは4個のi32。Nは4以上の2冪。混合Eは、偶数targetと奇数targetを交互に選ぶD段の自己逆gate列とする。chunk tの4laneを、それぞれ独立に次式で更新する。

```text
x[t] := x[t] XOR rotl32(x[(t-1) mod N] * coefficient[k]
                       + x[(t+1) mod N], rotation[k])
rotation[k] = (7 + 5*k) mod 31 + 1
```

加算・乗算は32bit剰余。同じ段のtargetは互いのcontrolではない。係数は相異なる奇数で、配布バイナリにも現れる。秘密鍵や暗号学的安全性は仮定しない。SIMDは4laneの実行をまとめるだけで、lane間の混合はない。

Uを元の更新、Eを状態符号化とすると、関数境界で必要な更新はE ∘ U ∘ E^-1。返り値もUの観測に含める。全回路を毎回実行する代わりに、Uと交換できないgateだけを残す。

## 計画

Rは現在の更新が読むchunkの保守的集合、Wは変更し得るchunkの保守的集合。元関数内の全load/storeから初期化する。returnが読むだけのchunkもRに含む。

```text
selected = []
R, W = chunks_read_by(U), chunks_written_by(U)
for gate in E, in execution order:
    t = gate.target
    C = gate.controls
    if t not in (R union W) and intersection(C, W) is empty:
        continue
    selected.append(gate)
    changes_target = (t in W) or intersection(C, W) is nonempty
    R = R union C union {t}
    if changes_target:
        W = W union {t}

emit original bounds check and record base computation
emit selected gates in reverse order
emit U and save its result
emit selected gates in forward order
return saved result
```

`footprint`対照はread/writeを区別せず、gateのtarget/controlと現在のfootprintの交差があれば残し、常にtargetをWへ加える。`full`は全gate、`plain`は元の状態表現。`broken`はRへの干渉を無視する反例用で、公開CLIの選択肢には含めない。

## 意味保存の根拠

gate gのtargetがR∪W外にあり、そのcontrolを更新が書かない場合、gは更新の返り値にも書込み値にも影響せず、更新はgの計算にも影響しない。この場合g^-1;U;gをUへ相殺できる。干渉する場合は残して新しい保守的R/Wを計算し、次のgateへ進む。

特にtargetがreadだけで、controlも変更されない場合、挟んだgateはtargetを最後に元へ戻す。読み依存は増えるが、targetを新たな書込み依存へ加える必要はない。この区別がfootprint対照との差である。これは既知の可換性・依存解析に基づく推論で、新しい代数原理の発見とは扱わない。

元の更新は不可逆でもよい。Eの可逆性だけを用いる。ただし、gate間または元の更新途中の状態がアプリケーションに観測されないことが必要。解析者の観測を禁止する仮定ではない。解析者が挿入したメモリ観測は[実験](analysis.md)で別に扱う。

## 実装で受理する範囲

実際の`.wasm`をWABTで検証・folded WAT化し、構文を検査して変換する。1個のprivate、非共有、固定64KiB memoryのみ。レコード数1〜16、レコード総容量64KiB以下。全関数は3個のi32引数と1個のi32結果を持ち、先頭に所定のunsigned境界検査とベース計算がある。各アクセスは当該レコード内の固定4byte境界offsetのi32 load/store。bodyは許可した全域的なi32演算、local操作、selectからなる直線コード。

import、memory export、shared memory、call、loop、早期return、memory.grow、浮動小数点、division、途中でのtrap、動的field offset、入力引数やベースlocalの変更は受理しない。開始時のactive dataはレコード領域内のみ。元の範囲外record番号は混合処理に入る前にtrapするので状態は保存される。未知の入力は黙って処理せず`Unsupported`として拒否する。

上記の依存推論は証明の概略であり、実装の機械検証ではない。有限の32bit差分実験と、1/2bitの縮小モデル全探索を区別する。
