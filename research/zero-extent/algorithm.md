# アルゴリズムと意味保存条件

入力は実際の `.wasm`。対象を検査してからWABTのfolded WATへ読み、変換後を再びバイナリへ組み立て、validateする。既存出力は上書きしない。

## 変換

純粋かつ全域的なi32式で構成された条件を0/1へ正規化し、構造化ifを順序付きguarded-effect列へ展開する。thenは親guardと条件のAND、elseは親guardと条件の否定のAND。sourceのlocal更新、load、call、div、loop等は拒否するので、非選択側の式の評価・条件の再評価に副作用やtrapはない。ifを跨ぐメモリ操作の順序は変えない。

```
for each guarded effect (c, E), in original branch order:
    c := normalize_to_0_or_1(c)
    if E = memory.fill(a,v,n):
        memory.fill(select(c,a,0), v, select(c,n,0))
    if E = memory.copy(a,b,n):
        memory.copy(select(c,a,0), select(c,b,0), select(c,n,0))
    if E = store_w(a,offset,v):
        full := unsigned_extend(a) + offset        // i64, not i32 wrap
        d := full > UINT32_MAX ? UINT32_MAX : wrap32(full)
        d := select(c,d,0)
        if w > 1:
            memory.copy(d,d,w*c)                  // range preflight
        for i = 0 .. w-1:
            memory.fill(d+i*c, v >> (8*i), c)
```

擬似コードのselectは`select(condition,true,false)`の通常表記であり、WATでは値2個の後に条件を置く。即値offset=0の場合はi64演算を省く。実装のmemory最大値は2ページ以下なので、UINT32_MAXは必ず範囲外。4GiB memoryへこの処理をそのまま一般化しない。

`explicit`対照はidentity copyの代わりに`unsigned64(d)+unsigned64(w*c) > memory.size*65536`ならunreachableとする。他の変換は共通。`flat`対照は同じguard展開を使い、元effectをifで囲う。

## 条件付きの正当性理由

1. c=0では宛先・copy元・長さが0となり、0ページの場合もboundsを通過して公開状態を変えない。store分解のi*cも0である。
2. c=1ではbulkの引数は元の値と等しい。元のstoreについて、effective addressを非wrapで計算する。overflow時の写像先は必ず範囲外であり、元と同様にtrapする。
3. 幅2/4のcopy(d,d,w)は失敗ならmemoryを変えずtrapする。成功なら同じbyteを同じ場所へ写すだけであり、後続のbyte fillはすべて安全な範囲内。little endianの下位byte列が元storeと等しい。
4. 各effectの前後の公開memoryが等しく、順序も保つので、最初のtrapの時点でそれまでに完了したeffectの結果も等しい。

これは指定した機構についての説明であり、Python実装全体の機械検証や全入力の証明ではない。非共有memory、host callbackなし、実行中の外部観測なしを前提にする。instruction trace、時間、trap PCやエラーメッセージの同一性は保護対象外。memory64、shared/atomic、import、table、data section、関数間変換、任意のC/Rustプログラムは未対応。

## 方式既知の解析

`normalize`はバイナリを入力とし、local値のunsigned上界を保守的に伝播する。長さが0/1のfillは条件付きstore8へ、同一宛先のcopyはbounds検査へ、その他のbulkは長さ非零の分岐へ移す。零長側でも元のboundsを保持する。元のソース、guard一覧、seedは渡さない。

解析目標は**副作用の有効条件を分岐として露出させ、零長操作を含まない更新へ正規化すること**。元のifの構文・木形状・変数名の一意回復ではない。残るcopy/fillの非零処理をすべてscalarへ展開したとも主張しない。数学的には各bulkの効果条件は長さ≠0なので、秘密の解除鍵や全パス探索は要らない。公開メモリからcopy内容が読めることも脅威モデルに含む。

operand評価はWasm順序どおり左から右。前のaddress operandのlocal.teeが後のlengthを変更できるため、評価前のlocal上界を使い回さない。ifの両腕は同じ分岐前状態から解析して合流する。loop・非局所分岐・call・memory.growは解析器でも拒否する。
