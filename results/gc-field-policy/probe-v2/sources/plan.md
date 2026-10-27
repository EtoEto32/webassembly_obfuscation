# O候補：構造的GC型のフィールド権限をmodule受理時に検査する

2026-10-25。Lのwrapper失効と異なり、実行時の検査を追加せず、Wasm GCの型付きアクセス命令を使って**受理可能な第三者moduleの集合**を制限する仮説。新規性は未確立。JVMのaccess control、bytecode verification、proof-carrying code、Wasm private type提案との比較が必須である。

## 問題と想定する契約

信頼するlibraryがGC objectを返し、loaderが受理した第三者Core Wasmだけがその値を受け取る。hostは信頼し、任意の追加Wasmを検査器の外で実行させない。libraryの意味的な許可APIから情報が返ることは認める。

保護対象は、指定したGC型のフィールドの直接read/writeと、その型の値の第三者による生成。現状では値のclass/identity、array length、timing、メモリ量を秘密にしない。型ごとの一様な権限であり、同じ構造的型の別ownerのobjectを区別できるとはしない。

問題自体は既知。[type importsのprivate type節](https://github.com/WebAssembly/proposal-type-imports/blob/main/proposals/type-imports/Overview.md)はcastを通じたencapsulationの破れを防ぐ必要を既に述べる。[GC issue #215](https://github.com/WebAssembly/gc/issues/215)も2021年にstrong data encapsulationを議論している。これらを新発見とは扱わない。

## 初期アルゴリズム仮説

libraryのpost-optimization binaryと信頼するfield policyを入力にする。loaderの同じcanonical type contextで各consumerをvalidateし、同値なrecursive type groupを同じ型IDへ正規化する。**module-localの型番号・型名では照合しない。**

protected型Tのfield kをread/writeから守るとき、Tの全supertypeでkが存在する型Uに対するアクセスも禁止する。consumerが宣言したTのsubtype Dに対するアクセスも同じfieldの権限を継承する。T生成を禁止するとき、Tとその全subtypeのconstructorも禁止する。array.copyはsource readとdestination writeを別々に検査する。unknown opcode/featureは対応を確認するまで拒否する。

```text
canonicalize and validate trusted library
resolve trusted policies to canonical type IDs
for each consumer binary:
    validate in the same canonical type context
    for every struct/array operation:
        enumerate its read/write/create obligations
        close operand type and protected types over declared subtyping
        if an obligation intersects a forbidden protected field: reject
    otherwise admit these exact checked bytes
```

動的flowを無視するので保守的に拒否する。Tのsupertype U上の同じfieldを読む処理は、実際の入力がTでなくても拒否する。これが利用不能なほど強ければ、runtime wrapperやprivate copyの方が適切であり、静的方式を成功としない。

## 初期実験と反証条件

まず小さいWasmを生成し、型番号変更、同形の別recursive group、正規化で同値になる型の複製、supertype経由アクセス、consumer新規subtype生成、array.copyを含める。正常な公開field操作と単なる値の受渡しは許す。型が似ていてもWasm上は異なる例を対照にする。Nodeで実際にlibraryとconsumerをlinkして観測する。可能ならWasmtimeも使用する。

比較は(1)検査なし、(2)module-local型番号一致、(3)canonical型の完全一致だけ、(4)subtyping closure、(5)全GCアクセス拒否。2/3は想定される不完全実装であり既存製品の不具合ではない。5の代わりに安全な公開APIだけを使う設計は強い実用対照として別途検討する。

主テーマへの条件は、既知のfield access verificationを移しただけではない保証・合成条件・実用効果を示すこと。単にcounterexampleを増やすだけでは満たさない。受理検査の時間とruntime instrumentationゼロを、runtime上の全コストゼロや完全な情報流保護と言い換えない。

## 先行確認

- wasmparser 0.227.1 `Validator::reset`の公式実装とdocを読んだ。複数module間のcanonical type ID再利用は既に実装済みであり、本方式の新アルゴリズムとはしない。
- **SecWasm**, Iulia Bastys / Maximilian Algehed / Alexander Sjösten / Andrei Sabelfeld, SAS 2022, pp.74–103, DOI 10.1007/978-3-031-22308-2_5。大学の書誌、著者PDFのAbstract/Non-goals/Contributionsの検索本文を確認。hybrid IFCとtermination-insensitive noninterferenceを扱う。全文検証は未了。Oの直接アクセス制限とは保証範囲が異なり、Oが一般IFCを上回るとはしない。
- private type提案とGC議論は仕様設計資料であり査読論文と区別する。近接する言語横断のprivate field enforcement、JVM verification、型付きcapability研究の追加調査が必要。
