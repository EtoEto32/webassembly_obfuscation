# Kの実測と採否

2026-10-24。**検査器としての成立を確認したが、独立した強い学術的新規性は未確立。** 自作mutantを検出した件数を既存製品の新規bug数とはしない。Jは[直接比較](../logical-reset/strict-review.md)の理由で主方式への採用を見送った。

## 主検査

[probe-v4](../../results/state-witness/probe-v4/results.json)が主記録。8構造fixture（同一系列の容量・segment・float stateの変種）から64 binaryを作成した。WABT validation、raw/O3、元APIの実行を含む。

- 元APIの実行4,872回。元binary・観測付き・観測付きtwin等の対応比較に不一致0。この数は比較pair数ではなく実行回数。
- segment/end-bound probeを23,480回呼び、1,168箇所で反復observerとnative state直接読取りから非破壊性を検査。
- Jの再初期化後を192回比較。fullの48回は一致。plain/no-bounds/no-dropの24設定は各6 epoch、合計144回で意図した差を検出。
- bytesだけのoracleが見逃すsegment差を8例で検出。元APIの0長initで成功/trapが違う反例も保存。
- nullnessだけでは分からないtable変更を4例、生bitを見ないNaN比較が見逃す差を4例で検出。

[Wasmtime cross-v2](../../results/state-witness/cross-v2/results.json)は3,852呼出し、1,488 trap。globals raw bits / 容量 / boundary / segmentsについて同じ分類を確認した。memory全bytesとtable function identityの別engine比較ではない。

[境界検査](../../results/state-witness/boundary-v1/results.json)は5受理・9拒否。empty module、宛先のないsegment、複数tableを含む。unsupported import/start/ref API/ref global/過大capacity等を成功として数えない。

## 自作例以外

最新：[公式testの中断点生成と4対照](cut-results.md)。272変換条件、1 engine当たり430回の到達復元、Node/Wasmtimeの結果一致を確認した。寿命変更後の中断では4つの元moduleで元API差が出た。二つのdelimiterが必要という仮説は棄却し、Kのstate差だけでは問題と断定できないケースも分類した。

追加：[公開wasm-migrateの実行比較と原因切り分け](external-results.md)を完了した。8変換条件の無移行対照は一致し、到達した復元点では制御フローとsegment寿命の二種類の結果差を確認した。Node / Wasmtimeおよび独立再ビルドで再現した。これは自作mutant以外の検査用途を支持するが、新規な検査原理の成立とは区別する。

[公式testへの適用 spec-v4](../../results/state-witness/spec-v4/results.json)：spec commit `aa4dcf44b8de3f3f3270ca067422172518ecc341`（2026-10-23）のmemory_init/table_initを取得。69個のmodule commandのうち63受理、6 imports未対応、tool rejection 0。受理分の既存操作650件が期待結果及び元binaryと一致し、追加probe 3,552回を実行した。

table_init末尾15行のGC moduleはWABTが構文を読めない。元のerror、読めた2271行のprefix、未読込みtailを保存し、上記69moduleとは別に扱う。公式suite全体の合格ではない。assert_invalid等の対象外commandもmanifestに残した。公開JavaScript generatorは実行していない。

## 観測差と脆弱性の区別

[observability-v1](../../results/state-witness/observability-v1/results.json)では、dropしかできず読取APIが定数を返すmoduleでも、内部segment差が出ることを確認した。元APIの長さ6までの127 suffixでは差がない。この特定例は関数本体の構造から任意長でも出力不変と説明できる。別のmoduleへinitを公開すると、4番目の候補（長さ1）で実際の成功/trap差が見つかった。

従って「state差を見つけた」だけでは機密漏えいや元APIの不正を主張できない。state復元契約を厳密に検査する用途と、外部観測されるセキュリティ効果の確認を区別する。

## 費用

[performance-v2](../../results/state-witness/performance-v2/results.json)。Node 24.15 / V8 13.6、5 fresh process、3 warmup＋15 shuffled round、各100観測。数値はprocess中央値の中央値。visibleはbytes/globals/tableを読み、segment/boundsのprobeを省いた弱い対照。

|fixture・状態|visible µs|segment追加 µs|full µs|
|---|---:|---:|---:|
|0page、初期|5.132|32.010|50.910|
|0page、drop後|4.519|47.863|65.452|
|1page、初期|27.575|55.123|72.524|
|1page、drop後|26.877|69.902|86.726|
|4pages＋追加state、初期|18.470|63.317|80.197|
|4pages＋追加state、drop後|17.875|100.030|125.017|

trapのhost捕捉が高価で、常時本番検査に向くとの結果ではない。memory大小の時間が単調でないため、GC・JIT・allocationの影響も含む短い測定として解釈する。四分位数と全48条件を保存した。RSSは全modeを含むprocessの最終値で107,966,464–119,103,488 bytes。mode別RSSの優劣は言えない。

主fixture full変換はsource 840–1013 bytes →1793–2288 bytes、1回の変換39.4–50.0ms（WABT起動含む）。全64binaryの生成2.355秒。反復分布を持つ変換時間ではない。

## 失敗記録・採否

probe-v2はcanonical exportsが最適化後にaliasするケースを過度に拒否し停止した。v3でalias classを保持し、v4でtable/NaNの見落とし対照を追加した。v1のtable参照照合は同じJS参照に対する最後のindexを保持していたため、主記録として使わない。spec-v1のGC構文失敗、v2の不要なenable-allによるcompact-import encoding問題も保持した。

Kの価値は、再現可能なstate比較器と、弱いoracleが何を見落とすかを示す対照にある。**仕様test自体が既に中核probeを生成しており、新しい原理の強い主成果としては採用保留。** 外部実装での実測反例を追加できたが、既存の元API差分検査でも結果差は検出できる。修士研究の新規性には、複数実装での一般化または既存検査に対する追加の価値を示す必要がある。
