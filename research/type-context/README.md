# 型関係を保つモジュール文脈案の先行性検査

2026-10-27。**型をコピーし、別モジュールで型同一性を検査するという中心部分には強い先行実装があり、現段階で新規主案としては採用しない。** コンパイル順序を含む全ての一般化が既に解決されたという意味ではない。前案の[次方向の判断](../gc-execution-gap/next-decision.md)に対する調査結果。

## 実際に読んだ一次資料

|資料|確認箇所と既存の仕組み|今回の案に対する意味|
|---|---|---|
|Binaryen133 [wasm-fuzz-types.cpp](https://github.com/WebAssembly/binaryen/blob/version_133/src/tools/wasm-fuzz-types.cpp)|`checkCanonicalization`、`checkRecGroupShapes`、run全体。再帰groupの境界・内部参照を保ち、旧canonical型と新temporary型を混ぜてコピー。同一性、部分型、LUB、group形状の順序・hash等を検査|型番号の付け替え・既存と新規型の混在・等価性の不変性だけでは新しい検査原理にならない|
|公式 [type-rec.wast](https://github.com/WebAssembly/testsuite/blob/main/type-rec.wast)|全226行。group長、投影位置、内部/外部参照の違い、link成功/失敗、call_indirect成功/trap|肯定・否定の型関係を検査することは既存|
|公式 [type-equivalence.wast](https://github.com/WebAssembly/testsuite/blob/main/type-equivalence.wast)|構文上・実行時の型同値性、同型の再帰group、間接呼出し|「実行時に検査した」という点だけでも差分にならない|
|V8 [runtime-type-canonicalization.js](https://github.com/v8/v8/blob/main/test/mjsunit/wasm/runtime-type-canonicalization.js)|取得済みGit blob `e6935f3921bc4a06c629e61de695f253291fec77`、全ファイル。同じinstance、同module別instance、別module、GC後でref.testの成功と失敗を検査|別module・過去の型registry状態まで扱う近接先行実装|
|WebKit [cross-module-rtt-identity.js](https://github.com/WebKit/WebKit/blob/main/JSTests/wasm/stress/cross-module-rtt-identity.js)|全ファイル。独立にcompileした同じ再帰structの生成値を別moduleでcastしてfieldを読む|cross-module ref.castと値の確認を初めて行うとは言えない|

これらは査読論文ではなく仕様テスト・公開実装。V8は公式directory listingから存在するファイルを特定し、Git blobのSHA-1を照合した。他のmain資料は取得時のSHA-256を保存したが、同一commitへの固定取得ではない。最初に推測したファイル名2件は404で未読、DNS失敗もmanifestに残した。

## 実行した既存対照

Binaryen133 `wasm-fuzz-types --seed 0..63 --verbose` を各fresh processで実行。**64/64正常終了**。1 workloadは20型slotから始まるが、同値型の重複や派生型を含むため1,280個の独立型を試したとは言わない。process起動を含む中央値10.994 ms、最大13.313 ms。これはBinaryen内の自己検査であり、3つのWasm実行エンジンの安全性検証ではない。

```powershell
python research/type-context/baseline.py results/type-context/fresh-baseline
```

出力先は新規directory。生ログ：[64 seed](../../results/type-context/binaryen-baseline-v1/report.json)。取得資料は `priors-v2` / `more-priors-v2` / `v8-prior-v1`。関連資料と実行ログを含むhash確認は[後続監査](../../results/boundary-alias/audit-v2/report.json)で行った。

次は型関係検査を別名で再実装せず、[境界の参照共有を比較するoracle](../boundary-alias/README.md)の不足を調べた。こちらも一般的な同一性番号付けは既知なので、実装の機能差と研究の新規性を分ける。
