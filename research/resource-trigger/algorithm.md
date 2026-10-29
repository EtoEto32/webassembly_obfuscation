# 所有resourceの破棄順への状態更新の移動

## 対象と意味保存

入力は一つのexport run(i32,i32)->i32だけを持つcore Wasm。純粋なtotal整数式のうち、xを一度だけ含む状態更新鎖` s[0]=x, s[i+1]=op[i](s[i],p[i](y)) `を抽出する。opはadd/xor/mul/rotl、payload式はadd/sub/mul/bitwise/shift/rotate。i32ローカルの代入を展開して読む。1..128段。メモリ、global、外部import、一般CFG、div/trap、floatなどは入力として拒否する。

出力はComponent Modelのバイナリであり、coreモジュールとは異なる形式。exportはu32,u32->u32で、元のi32入出力との関係は**32bitパターンの一致**。JS呼出し側で`component.run(x >>> 0, y >>> 0) | 0`とすれば元のsigned i32の表現へ戻る。coreバイナリをそのまま置き換えて同じローダで実行できるという意味ではない。

内部engineにはi32状態globalと非exportの1page memoryがある。payloadを書き込むhelper、状態reset/read、4種の更新helperをexportしてcomponent内で結線する。各resource型のdestructorは更新helper。型・結線は公開されており、秘密鍵はない。

```text
transform(core, seed):
    s[0]=x; (op[i],payload[i](y)) = extract_chain(core)
    define four owning resource types R[op], destructor = engine.step[op]
    define canon.new[op], canon.drop[op]
    run(x,y):
        engine.reset(x)
        for i in seeded_permutation(0..N-1):
            engine.store(4*i, payload[i](y))
            h[i] = canon.new[op[i]](4*i)
        for i in 0..N-1:
            canon.drop[op[i]](h[i])
        return engine.read()

engine.step[op](address):
    state = op(state, i32.load(address))
```

4*iは0..508、alignmentとboundsを満たす。payloadの評価はx/stateから独立し、副作用・trapがないため順序を変えられる。slotは個別で、対応破棄まで上書きしない。各hは借用されず、一回だけ破棄され、外部へ逃げない。仕様上のresource.dropはown handleのrepをdestructorへ渡す。第i回破棄直前のstate=s[i]を帰納法の不変条件とすれば、全破棄後は元のs[N]になる。次回呼出しはstateをresetし全使用slotを再初期化する。

この説明は対象profileとresource割当・メモリ割当が成功する前提に限る。資源不足、hostの中断、並行再入、誤ったhandle、一般の副作用付きプログラムに対する同値性は主張しない。テストは実装検証であり、この説明を機械証明したものではない。

## 比較とアブレーション

| mode | 計算の配置 | resource | payload保存 |
|---|---|---|---|
| core | 元のcore式 | なし | なし |
| plain | 元の式をcomponentへlift | なし | なし |
| direct | 同じengineのhelperを順次呼出し | なし | 内部buffer |
| immediate | 生成して直後に破棄 | 各段で1個 | 内部buffer |
| deferred | 全生成後に正しい順で破棄 | ピークN個 | 内部buffer |

directとresource版は同じbufferと更新helperを用いる。plainとの差にはcomponent境界と状態/メモリ化の費用が混ざる。deferred/immediateは、生成順変更とhandle生存期間延長の効果を比較する。

## 適応解析

攻撃者はcomponentバイナリ全体、仕様、方式を知り、原本・seed・manifestは知らない。Jco printでcomponentのtype/alias/instance/canonを読む。埋め込みcoreはバイナリから抽出しWABTでvalidateとfolded WAT化を行う。import名は意味ラベルとして扱わず、実際のalias結線で解決する。

解析器はcore関数、private global、定数アドレスの32bit bufferを記号実行する。newは(resource型,一意ID)にrepを対応付ける。dropはその対応を消し、型定義のdestructorへrepを渡す。整数入力を列挙せず、式のまま伝播させる。通常のhelper呼出しも同じ解析器でinlineする。元の式へ戻したcore .wasmを生成する。

```text
symbolic_new(type, rep): h = fresh_id(); H[h]=(type,rep); return h
symbolic_drop(type, h):
    assert H[h].type==type
    rep = H.remove(h).rep
    symbolic_call(destructor[type], rep)
```

生成と破棄の対応は辞書参照で求まり、生成順の順列を探索する必要はない。このprofileでは曖昧なaliasや分岐がなく、命令数にほぼ比例する処理で解除できる。対応profile外のcomponent一般を解析するツールではない。最初にO3のoperand stack表現を読み落とした失敗はv1へ保存し、関数arityとstack消費の実装で修正した。
