# G 実測と限界

2026-10-24。正常実行の一致を確認したが、特許主案に採用しない。反復版の件数を足して独立実験数にはしない。

|実験|範囲|結果|
|---|---|---|
|[V8 probe-v4](../../results/import-alias-quotient/probe-v4/results.json)|27自作fixture、198同一性分割、元/商と各O3|16,632値・状態照合、39,600memory照合、5,104trap照合で不一致0|
|[Wasmtime cross-engine-v1](../../results/import-alias-quotient/cross-engine-v1/results.json)|792instance、同じ入力列|16,632照合、37,800memory照合、5,104trap照合で不一致0|
|[既存linker対照](../../results/import-alias-quotient/merge-baseline-v1/results.json)|wasm-mergeとalias再公開wrapper、198instance|4,158照合、9,450memory照合、1,276trap照合で不一致0|

V8側は独立JavaScript byte配列模型と、呼出しごとの全memory bytes、返値/trap、export object同一性を比較する。Wasmtime側は同じ参照traceの全memory SHA-256と長さを比較する。Python wrapperのobject identityは主張しない。これは数学的同値証明ではない。

意図的にloadを先行storeの前へ動かす誤変換を、aliasのある8条件で検出し、非aliasの14条件では一致した。実runtimeの新しい脆弱性を8件発見したという意味ではない。

Node全harnessは6.391秒、Wasmtime検査loopは2.903秒。実装言語・作業範囲・初期化の計上が異なるため、この値をruntimeの優劣に使わない。NodeのRSS 91,799,552 BとmaxRSSはprocess全体の値で、guest単体の追加memory量ではない。変換時間とbinary bytesは各manifest、既存linkerの生成時間はbuilds.jsonへ記録した。保護変換としての実行時間ベンチマークではない。

初回v1はBinaryen機能flag不足で停止。v2はWABT 1.0.42の既知memory.init writer問題へ再遭遇した。原因と限定対処は[reader-note](reader-note.md)に示す。既知不具合の再現を新規発見と数えない。

限定した整数・bulk memory・grow例の境界状態を検査できた。一方、既存linker対照が全条件を代替したため、新しい統合アルゴリズムという主張は成立していない。一般のmetamorphic testingとの差も弱い。
