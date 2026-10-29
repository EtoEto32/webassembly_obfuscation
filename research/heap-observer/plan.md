# 外部GC読出しhelperの先行性・実現性ゲート

2026-10-27、実装前固定。主テーマ採用前の小さな実験であり、新規性を認定した計画ではない。

## 問題と仮説

JSに渡されたWasm GC objectのfieldは通常のJS property列挙では読めない。そこで対象binaryのrecursive type groupを別Wasmへ複製し、型検査とstruct.get/array.getだけを含む読出しhelperを生成する。対象programやengineは変更しない。公開済参照をhelperへ渡し、到達field・参照共有を有界に記録する。

初期仮説H1：元type groupを保つhelperで、複数engineにおいてopaqueなstruct/arrayの内容を取得できる。H2：同じhelperをO0とO3へ使えば、open-worldで保証される境界観測を比較できる。H3：closed-worldでは同じ観測が不適切になる例がある。H1の成立だけでは新アルゴリズムではない。

## 重要な先行性

Binaryen133 pass.hは、open-worldでは外へ逃げる参照の詳細な検査を前提とし、closed-worldでは外からの内容検査・呼出し・構築・型reflectionを禁止している。したがってこの区別自体は既存。BinaryenのTwo handlerもfuzz-importで第2moduleを作り、独立最適化やmergeと比較する。外部moduleによるテスト一般を新規性に数えない。DUMPLING、Java serialization、V8 DevToolsのGC heap可視化も近接技術。

## 実装・検証範囲

- wasmparser/encoderでGC MVPのtype sectionを全て複製。rec group順・supertype・finalityを保存。追加のhelper関数型は後置する。
- 対象のcode sectionには触れない。helperはpureな読出しのみ。fieldのi8/i16はunsignedで読み、floatはbit列へ変換する。符号・NaNの厳密oracleとしては別の正規化条件が必要。
- shared type、descriptor、continuation、例外参照は初期対象外と明示。任意のJS object/funcref内部は辿らない。
- 同じO0から作ったhelperでO0/O3を観測する。型indexはhelper内部の固定座標であり、別々のhelperのindexを直接比較しない。
- 手製校正：scalar、packed、array、共有/別object、循環、rec groupの相互参照、subtype、null、float bits、拒否。対象fieldへアクセスできない対照はunsupportedとして別計数。
- 既存の表示・boundary identity・helper snapshotの3観測を同じ故障対照で比較。故障注入の検出と自然不具合を分ける。
- open/closed-world差は仕様・optimizerの契約に照らして分類し、closed-worldでの外部読出し差をbugにしない。

## 採用条件

実現性だけでは不十分。強い対照（単純に手で書いたgetter、既存Two handler）との差、実生成器・独立した既知不具合での効用、観測費用とfalse positiveの検証が必要。既知reflection/serializationの適用に留まるなら主テーマの新規性は未確立とする。全heap同値・全入力同値・observerによるGCタイミング非干渉は主張しない。
