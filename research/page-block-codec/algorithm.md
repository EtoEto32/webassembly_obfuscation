# アルゴリズム・意味保存・攻撃モデル

2026-10-21。汎用の安全性証明を備えたコンパイラではなく、限定した実Wasm変換器。特許の主案には未採用。

## 表現と処理

各16byteをlittle-endianの4語 v[0..3] とする。次の4組を順に使い、v[i] ^= rotl32(v[j]+v[k],r) を行う。

```
(i,j,k,r) = (0,1,2,5), (1,2,3,11), (2,3,0,17), (3,0,1,23)
```

各段は自己逆であり逆順適用が復号。零は零へ移る。暗号強度・秘密鍵は想定しない。ARXの可逆更新は既知で、本研究の新規性の根拠にはしない。

source memory32 のscalar load/storeをcallへ置き換える。固定のページ数を持つprivate memory64へ変更し、active dataを表現変換する。

```
a = zero_extend_u32(original_address_expression) + original_immediate_offset
b = a & ~15
e = (a + width - 1) & ~15
off = a & 15

store_block(a, width, value):
  c0 = v128.load(b)
  c1 = (e != b) ? v128.load(e) : zero
  # この時点までメモリを書かない
  v0 = decode(c0); v1 = decode(c1)
  v128.store(b, encode(replace_selected_bytes(v0, off, width, value)))
  if e != b:
    v128.store(e, encode(replace_remaining_bytes(v1, off, width, value)))
```

byte選択には i8x16.swizzle と i8x16.lt_u、v128.bitselectを使う。これらの既知命令の組合せ自体を新原理とはしない。loadは同じブロックを復号し、2つのswizzleをORして下位64bitから必要な幅を抽出する。符号拡張は元の幅に従う。

元のアドレス式のi32加算は改変しない。**即値offsetを加える段階だけ**をi64へ持ち上げる。たとえば p=4, offset=0xfffffffc では数学的な有効アドレスは2^32であり、0へwrapしてはいけない。

## 意味保存の条件

メモリ長 L は64KiBの倍数、従って16の倍数。a>=0、1<=w<=8なので、元の範囲条件 a+w<=L は e+16<=L と同値。後者が成立すれば b+16<=L も成立する。aは最大2*(2^32-1)で、i64の加算はwrapしない。

原storeのアドレス式、値式は同じ順序で一度ずつ評価される。codec側の読込みはその後に行う。元のstore自体がtrapする場合、ブロックの読込み段階で止まり、元storeに由来する変更は行わない。先行命令やアドレス式・値式のstoreはそのまま残る。成功時は必要byte以外を元に戻すため、表現不変条件 encoded=E(logical) が成立する。

外部呼出し・共有メモリ・memory export・grow・bulkを拒否するため、helper途中で観測者が割り込んだりmemoryが変わったりしない。ページは増やさない。追加helperによるstack消費、時間、fuel、OOM、trap PC/stack trace/エラーメッセージ文字列は保存契約外。全バイナリの機械検証済み同値性ではない。

## 既知の高アドレス優先方式

文献照合後に block-high 対照を追加した。e!=bなら先にeをload/decode/patch/encode/storeし、その後bを処理する。eのloadが成功すればbも必ず有効なので、すべてのblockを先にloadしなくても部分書込みを防げる。block間は独立なEであり、後の読込みを壊さない。

これはWasmの既知の高アドレス優先store loweringに対応する。新しい主発明として数えない。今回の結果は、事前読込みの一括化が意味保存のために必須、という強い動機を反証する。

## 実装範囲

- sourceは実wasm。固定min=maxの0..16ページの単一非共有memory32、private memory、整数scalarの通常load/store、通常関数/制御、定数active data。
- i32/i64の8/16/32/64bit読み書き、signed/unsigned load、非整列、alias、最大i32即値offsetを扱う。
- import、global、start、table、GC、例外、memory.size/grow、bulk、元memory64、浮動小数点、SIMDソース、外部によるmemory変更は非対応。動的linking/custom/debug sectionの完全保存は保証しない。
- readerはWABT出力AST用。実アプリへの適用率は未評価。0/1/2ページの1つの合成APIプログラムを検査しただけで、3種類の独立アルゴリズムではない。

## 保護課題と回復

保護対象は元のbyte位置・値の読取りである。攻撃者は配布binaryを編集し実行でき、仕組みを知る。試験APIには任意のi32書込みがある。このAPI自体が強い情報を与えるため、この例を製品の保護性能の代表にはしない。

`recover.py` は元source・codec定数・seed・正解表を読まない。WATから v128 -> v128 のhelperを型で列挙して呼出しwrapperを追加し、private memoryを観測可能にする。`recover.cjs` は4語×3組、12回の公開書込みで既知の論理blockを作り、物理blockを各helperに渡す。既知の論理値に戻るhelperを選び、観測memory全体へ適用する。

raw/O3、byte/block/block-high、1/2ページの12条件で復号器を同定し、全byteが独立したplain実行と一致した。0ページは回復対象のbyteがないため攻撃の正条件に数えない。完全な逆コンパイル、元source型の復元、一般のcodec同定を行ったわけではない。helperがinlineされた一般例は未対応であり、未対応を耐性とはしない。
