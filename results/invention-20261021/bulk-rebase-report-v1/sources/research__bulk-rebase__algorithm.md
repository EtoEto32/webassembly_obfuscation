# 位置依存byte表現のコピー後補正

2026-10-21。実験で検査する具体規則であり、独立した新原理や特許性の認定ではない。

## 状態対応と手順

元メモリを A、変換後を B とする。Pはbyte上の全単射で、試作では同じ16要素置換を上下nibbleに適用する。Kは公開の16byte周期mask。状態関係は `B[a]=P(A[a]) XOR K[a mod16]`。PやKを解析者から秘密にする仮定はない。

```text
load8(a):       return P^-1(B[a] XOR K[a mod16])
store8(a,v):    B[a] = P(v mod256) XOR K[a mod16]
copy(d,s,n):
    memory.copy(d,s,n)         // B上で実施。範囲検査と重複処理を標準命令へ委ねる
    for i = 0 .. n-1:
        B[d+i] ^= K[(s+i) mod16] XOR K[(d+i) mod16]
```

raw copy後の移動先は、操作直前の `P(A[s+i]) XOR K[s+i]`。二つのmaskをXORすると `P(A[s+i]) XOR K[d+i]` になる。補正は各移動先を一度だけ読み書きし、元の移動元を読み直さない。従って重複方向による変更は不要。Pを明示的に復号しない点は、二つのPが代数的に相殺されることによる。

SIMD版は16byteずつ補正する。Kの周期が16なので、補正vectorは開始時に一度生成すればよい。同じ最適化を直接コピーする対照にも適用する。残りはscalarで処理する。

## 意味保存の前提

Wasmのmemory.copyは、unsignedなd+nとs+nの範囲を検査した後に書き込む。n=0でもこの検査を省略できない。成功したcopyの移動先範囲は全て有効なので、後続の補正アクセスは新たなbounds trapを起こさない。private・非共有memory、importなしの逐次実行を対象とし、補正途中でホストや別threadが状態を読む状況を含めない。

直接copyの対照は64bitへ拡張して両端を先に検査し、d<=sなら前進、それ以外なら後退する。32bit和のwrapや、途中まで書いてからtrapするloopは同値ではない。元の引数評価とその副作用は、helper呼出しの引数順で保存する。copyより前に行われた元の書込みは、そのcopyがtrapしても保持する。

初期dataは元のsegment順で静的符号化する。dataで覆われない零領域は追加startでE_a(0)に初期化し、その後に元startを呼ぶ。複数の重なるdata segmentと、元startの読書きも検査する。生成器全体の機械的な意味保存証明は行っていない。

## 実装範囲

入力は実.wasm。WABTで読取り・検証し、byte load/storeとmemory.copyをhelperへ置換する。固定1または2pageの非共有・非公開memoryを1個だけ持ち、import/table等を持たないmoduleが対象。直接call、関数列、分岐、loop、global、startを扱う。元の関数番号を維持してhelperを追加する。

memory.grow/fill/init、別幅load/store、非零offset、shared memory、atomic、間接call、動的data、memory export等は非対応。既存WAT profile全体の同一性を要求する方式ではないが、任意C/C++や全Wasm機能の変換器ではない。検査fixtureはbyte処理APIをまとめた1/2page moduleであり、独立した実アプリ2本とは数えない。

## 比較方式と失敗条件

plain、Pの復号・再符号化を行う方向付きscalar、Pを相殺する方向付きscalar/SIMD、copy後補正scalar/SIMDを比較する。素朴な復号版に勝つだけでは採用せず、直接SIMDに対する時間・サイズ・保護課題を判断する。後補正は2走査になるため、copyの高速な実装を使えても不利になり得る。

方式既知の解析者は自分のbinaryを計測できる。本fixtureのwrite APIとメモリ観測から等価decoderを学習できる。アドレス0へ0..15を書いて得た物理byteをq_vとすると、`delta_v=q_v XOR q_0=P(v) XOR P(0)`。他の15位相へ0を書いた値z_aを加え、全byteの表現を `E_a(v)=z_a XOR delta_lo(v) XOR (delta_hi(v)<<4)` と再構成できる。計31問い合わせで、元P/K自体を特定せず同じ状態を復号できる。書込みAPIを持たない任意アプリへのquery上界とは主張しない。
