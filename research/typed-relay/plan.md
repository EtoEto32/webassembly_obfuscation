# 型付き共有relayの反証ゲート

2026-10-18。これはCPS方式の移植を新発明として採用する実験ではない。前の区間上書き案の局所回復を踏まえ、関数間へ解析を移すだけで有用な差が出るかを調べる。

## 固定した問い

Wasmの `call_ref` と `return_call` / `return_call_ref` で、複数の整数演算を同じrelayへ通す。文脈を区別しない呼出し先集合は合流する。しかし、引数位置から呼出し先への記号的な要約を一度作れば、呼出し箇所ごとの対応は安く復元できるのではないか。

対象は一つのexport関数、固定1pageの公開memory、i32引数・locals・結果を持つmodule。import、global、table、既存の関数呼出し、data segment等は対象外。変換はfolded WATで左右の子式を持つ、trapしない二項i32演算だけに適用する。loop、分岐、load/storeは元の順序で残す。したがって本ゲートは制御フロー全体をCPS化するものでも、Luの実装の再現でもない。

## 規則

```
type OP = (i32, i32) -> i32
for every used binary operator op:
    leaf_op(a,b) = op(a,b)
relay_0(a,b,f:ref OP) = tailcall_ref f(a,b)
relay_j(a,b,f:ref OP) = tailcall relay_(j-1)(a,b,f)
replace op(x,y) by call relay_(d-1)(transform(x),transform(y),ref leaf_op)
```

原命令の左、右の評価順序を保存する。渡すrefは非nullかつ正しい型であり、間接呼出し自体のtrapを新しく加えない。ただし追加の通常呼出し・初期化・コードの資源消費はあるため、資源枯渇まで含めた全環境の同値性は主張しない。

## 比較と判定

元、直接typed ref、共有relayの深さ1/4/8、深さ4の通常call版。raw/O2/O3。演算集合の複数種類を使う3つのloopカーネルを用い、公開memoryを更新する例も含める。

1. 値、trapの有無、trap後も含む全公開memoryを差分比較。境界値、ランダム入力、別エンジンを用いる。
2. バイナリだけからleafとrelayの関係を検証し、引数に関する要約を構成する。原source、生成時manifest、関数名は回復に渡さない。未知の命令や循環は未対応として分離する。
3. 文脈非依存の集合合流と、方式既知の要約を分ける。候補数の増加は保護強度そのものとしない。
4. 実行時間、サイズ、追加linear memory、process RSS、変換時間、解析時間を測る。ウォームアップ、反復、fresh processを保存する。
5. 誤った引数順、追加副作用、未知のhelperを拒否・識別できるか検査する。

新規性はCPS・combinator共有・common prototypeと照合する。単に深くすることやWasm命令への移植は独立した差分に数えない。安い要約回復が成立するなら、一般CFAの文脈数を増やすだけの次案は選ばない。回復成功率だけでなく費用を比較する。
