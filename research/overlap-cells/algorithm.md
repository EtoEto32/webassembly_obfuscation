# 重なるcell対の符号化と更新

2026-10-19。実装済みの検証仮説であり、独立した新規発明の成立は未確認。[事前計画](plan.md)と[評価](analysis.md)を併読する。

## 対象と意味

入力は実際のcore `.wasm`。単一export `run(i64)->i64`が、下位2N bitをN個の4値cellへ展開し、隣接3cellの式によって中心cellだけを更新し、最後に再packする明示的profileを受理する。N=4..32、更新1..128回。各式はi32 add/sub/mul/and/or/xor/shl/shr_uと定数からなり、64組すべてで出力0..3、左右を固定したとき中心について全単射であることを変換前に確認する。式の形はfixtureの3族に限定しないが、入出力の構文profileは固定する。

一般的なC/C++プログラムや任意のメモリアクセスを受理する実装ではない。import、既存memory、global、call、分岐、loop、浮動小数点、GC等は入力profile外。入力の上位未使用bitは無視され、出力の上位未使用bitは0。出力は同じcore ABIを持つ。ホストから観測する既存メモリ副作用はない。

## 表現

添字はNを法として扱う。元の状態をc[i]とすると、pair状態はp[i]=E[i](c[i],c[i+1])。E[i]は16値の置換である。中心iを更新する式f(a,b,d)に対して、p[i-1]とp[i]を入力に、更新後の両pairを一つのbyteで返す表Tを構成する。

```text
for (a,b,d) in {0,1,2,3}^3:
    v = f(a,b,d)
    index = 16*Eleft(a,b) + Eright(b,d)
    T[index] = 16*Eleft_new(a,v) + Eright_new(v,d)
fill remaining 192 entries with unused output bytes, in random order
at run time:
    t = load8_u(Tbase + 16*pleft + pright)
    pleft = t >> 4
    pright = t & 15
```

`pair-zero`は到達不能192入力を0で埋め、符号化を固定する。`pair-noise`は上記の埋込みで固定する。`pair-recode`は両方の新しいEを各更新で選ぶ。center全単射により有効64入力から有効64出力への対応が全単射となり、残る192出力で表全体を256値置換にできる。`single`は独立cellの4値置換と64-entry更新表による対照である。これは既存ツールの完全再現ではなく、符号化表の基本原理を実装した対照。

入口には元のcell対からEへの16-entry表、出口には各pairの左cellを返す16-entry表を置く。表はWasmのprivate linear memory内で256byte境界に配置する。1固定page（64KiB）、import/exportなし。最大受理profileの使用領域は49,152byte。各loadのindexは0..255なので、その領域で範囲外trapは生じない。ホストが追加のmemoryやmoduleを確保できる資源前提が必要で、資源不足までの等価性は主張しない。seedは生成時のみ使用し、実行時の鍵や秘密記憶を要求しない。

## 意味保存の理由

初期表によってpair不変条件が成立する。隣接pairが同じ中心値bを表すなら、有効64入力のいずれかが選ばれ、出力は(a,f(a,b,d))と(f(a,b,d),d)を表す。他のpairは変化しない。帰納的に不変条件が保たれ、出口表は元の各cellを返す。整数演算はi32のwrapとshift countのmod32を含めて列挙する。この説明と有限テストは、binary生成器全体を機械検証した証明ではない。

## 方式既知の回復

攻撃入力は変換後binaryのみ。seed、manifest、元の演算、正解の符号化対応は渡さない。実際のdata segmentとloadのbit由来を追い、公開入口表から初期pair対応を得る。各更新で整合する64入力を列挙し、出力byteの上位4bitと下位4bitを二部グラフの左右頂点として接続する。

中心の更新が全単射なので、a,dを固定してbを動かすと新中心vの全値を通る。vを固定したとき、すべてのa,dが現れる。従って出力supportはvごとの4個のK4,4である。新しいEを知らなくても連結成分がvのラベルを与える。a,dが保存される条件を照合すると、新しい左右pair対応を伝播できる。無効入力の値は参照しなくてよい。

```text
frames = read_public_entry_encoders(binary)
for each update load in dependency order:
    evaluate its 64 consistent inputs using frames
    partition output support into connected components
    label each component in first-occurrence order
    record a 64-entry independent-cell update
    propagate pair encoders using preserved outer cells
check final decoder depends on its own recovered cell only
emit canonical independent-cell Wasm
```

回復物は独立cellの更新表を持つ等価実装。元の算術演算子名、変数名、ソースを得たとは言わない。readerは本profileに専用であり、汎用逆コンパイラではない。4値なら更新ごと64入力、32頂点のsupportを調べる。一般にq値ではq³有効入力と2q²頂点で、符号化の置換候補を全探索する必要がない。この共通成分の原理には[既存のcommon information理論](prior-art.md)がある。

Wasmは固定幅bit演算、byte表、private memoryによる実装形式を提供するが、この重複表現の原理は他ISAにも適用できる。Wasm固有の新原理とは主張しない。
