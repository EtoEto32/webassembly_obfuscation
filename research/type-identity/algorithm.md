# 再帰型グループを使う状態表現

2026-10-19。別原理の探索として実装したが、追加の保護優位性は未確認。Wasmの型同値性そのものを発明と呼ばない。

## 対象と変換

元プログラムは2記号DFAの有限長scanner。状態数Nは1–16、初期状態0、遷移δ(q,b)、受理関数F(q)を持つ。公開API `run(x:i32,n:i32)->i32` は `n & 31` 回、xの下位bitから順に記号を読み、最終状態のFを返す。元の実Wasmのpacked-table式を読み、全moduleが再構成したcanonical sourceと一致することを確認する。状態数を示すsource中のdrop定数も公開profileの一部であり、秘密ではない。

```text
Transform(source, G, D, seed):
    δ,F,N = read_and_check_canonical_source(source)
    W = N + D
    σ = seedで作る0..W-1の置換
    同じ定義のrec groupをG個、binaryに明示して出力
        各groupはW個の空のfinal struct型
    各状態qについてimmutable global token[q]を生成
        token[q] = struct.new_default(type[group=q mod G, slot=σ(q)])
    test_type[q] = type[group=(q+1) mod G, slot=σ(q)]
    step(token,b):
        各qについてref.test(test_type[q], token)を評価
        一致すればtoken[δ(q,b)]を返す
        一つも一致しなければunreachable
    accept(token): F(q)=1であるtest_type[q]へのref.testの論理和
    元と同じbit/length処理でstepを反復しacceptを返す
```

`gc`はG=1,D=0の対照。`groups`はG=2/8、D=0/32の4条件を主実験とする。ほかに元のpacked tableと、同じ順番の整数比較でdispatchするbranch対照がある。G,Dの違いを新しい原理の候補数に数えない。

通常のassemblerは型を内部化する際に同値groupを統合し得るため、GC版のraw binaryは型section・global・コードを直接符号化する。`census.py`はrawの宣言数を既存型正規化の前に読む。`.wat`はBinaryenによる正規化済みdisassemblyであり、rawのgroup複製数をそのまま表すsourceではない。

## 意味保存の根拠

同じrec group定義の同じ位置から取り出した型は、別のgroup宣言であっても同値となる。一つのgroup内の異なる位置は区別される。この既知の規則により、σが単射なら `ref.test(test_type[i],token[q])` はi=qの場合だけ1となる。φ(q)=token[q]と置くと、step(φ(q),b)=φ(δ(q,b))、accept(φ(q))=F(q)。初期状態と各bitの抽出が同じなので、反復に関する帰納法で返り値が保存される。

これは生成規則に対する紙上の説明であり、binary writer全体の機械検証済み証明ではない。テストで各生成状態と記号の全組合せを確認し、別実行器でも照合した。対象の型は空のstructであり、**再帰型グループの宣言を使うが、fieldによる循環参照グラフは作らない**。

型グループ全体を変えると同値性も変わる。使われない兄弟型を一つだけ変更した負の対照では、group間の対応が崩れ、実行時にどの状態にも一致しない反例を得た。兄弟型を単に削除してよいという変換規則ではない。

## 方式既知の解除

解析者には配布binaryと方式の仕様を与える。元のδ,F、生成seed、状態対応表は渡さない。`lower`はBinaryenの既存readerで型を正規化してから、空structの型ごとに整数を割り当てる。globalのallocationはその型番号、`ref.test`は整数の等値比較、参照local/globalはi32へ置換する。制御フローはそのまま残り、通常の整数状態機械になる。

nullは−1に対応させ、nullable localも−1で明示初期化する。参照の等値性比較`ref.eq`、非空struct、型subtyping、外部へ参照を渡すABI、imports等はこの解除器の対象外。オブジェクトのidentityと型のidentityを混同しない。最初の実装はnullable localの既定値を誤って0にしたが、別の反例で検出して修正した。

型グループの同値性はgroupを何度も展開せず正規化できる。追加D個の型を読む費用は残るが、回復する計算の意味状態は増えない。解除後はGC命令・GC型を含まないMVP Wasmとなる。元のpacked-table構文や最小DFAの回復を測ったという意味ではない。

## 前提と限界

sourceはpure i32、memory・import・外部callback・共有参照・副作用なし。追加GC allocationはインスタンス化時に行い、関数の実行中には行わない。allocation失敗、メモリ枯渇、時間、JIT/GCの観測は同値性の範囲外。一般Wasm、任意のC/C++プログラム、Wasm GCプログラム全体の変換は未対応。

Wasm固有なのはrec group単位の構造的型同値性とref.testを具体的に使う点。有限状態をオブジェクト・型のタグへ移す一般発想と、型の正規化は既知であり、この移植だけを新規性にしない。
