# GC参照の境界同一性oracle：実装前計画

2026-10-27。型文脈案の基本操作はBinaryen/公式テスト/WebKitに既存だったため、主案にはしない。次は「opaqueな参照を値別に表示するだけでは、返されたオブジェクトの共有関係の差を見逃す」という限定的な仮説を実測する。新規性は未確認。**初出順のオブジェクト番号付け自体は既知のシリアライズ手法であり、新アルゴリズムと呼ばない。**

## 検査対象

公開済みexportの呼出し、既存importへの引数、hostから渡す参照の列について、同じGC objectが再登場する関係を比較する。Wasm本文へ計数器・heap walk・追加exportを挿入しない。現行JS embeddingのExported GC Object cacheは、同じaddressを同じJS objectへ対応付ける。nullは別token。実験はstruct/arrayに限定し、function merging、custom descriptor、exception、stringref、JS primitiveの同値性は混ぜない。

各実行のWeakMapを空にし、既存のhost入力を順に登録する。その後、実際に観測された参照ごとに未登録なら次の番号を割り当てる。異なる実行の生のobject/addressを比較しない。非参照のevent名・値・trapも別途比較する。到達していない内部参照、field内容、GC配置・寿命は観測しない。

## 比較と反証

- 対照1：取得済みBinaryen133 `fuzz_shell.js` の `printed` 関数をそのまま抽出して使う。実fuzzer全体の検出率とは呼ばない。
- 対照2：全ての過去の参照と `===` 比較する単純なfirst-occurrence対照。同じ情報が得られるならWeakMap版を新しい検出原理としない。
- 正負校正：fresh/shared、交互共有、import callback、入力とのalias、struct/array、null、内部だけのallocationの変更。異なる共有関係を作る変種は意図的な故障対照であり、compiler bugではない。
- 実変換：同じ元binaryへBinaryen `-O2` / `-O3` を適用し、2 JS engineで未変換と同じ公開動作を確認する。閉世界仮定は指定しない。
- 測るもの：validator結果、呼出し・event数、区別できた故障対照、正常変換への誤報、実行時間、binaryサイズ、生成/変換時間。小例での差から実プログラムの検出率は推定しない。

## 主テーマへの昇格条件

このoracleだけでは不十分。既存のidentity-aware logging/graph serialization/API testingとの論文差分、実生成器で出現する共有関係、実不具合又は独立に選定した既知不具合への追加検出、同一予算の強い単純対照に対する利益が必要。単にWeakMapを追加すれば同じ結果となる場合、実用的な改善点とは扱っても独立した新規主アルゴリズムとしない。
